import base64
import zlib
from collections import Counter
from functools import wraps
from inspect import isawaitable
from types import SimpleNamespace
from typing import Callable, Generic, Optional

import orjson
from Crypto.Cipher import AES
from pydantic import BaseModel, ConfigDict, Field
from sanic import Sanic, response
from sanic.exceptions import NotFound

from .config import Config
from .event_manager import (
    CommandHandler,
    Context,
    ContextDataT,
    ErrorHandler,
    EventManager,
    EventPriority,
    MessageHandler,
    PostHandler,
    RawHandler,
    SystemHandler,
)
from .logger import get_logger
from .models import (
    MessageExtra,
    MessageType,
    SystemEventExtra,
    WebhookData,
    WebhookEvent,
    WebhookMessage,
)
from .sdk import KookClient


class EventStats(BaseModel):
    """Internal counters for webhook events."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    total_requests: int = 0
    challenge_requests: int = 0
    message_events: int = 0
    system_events: int = 0
    dropped_by_raw_handler: int = 0
    invalid_verify_token: int = 0
    errors: int = 0
    event_type_counts: Counter[str] = Field(default_factory=Counter)
    channel_type_counts: Counter[str] = Field(default_factory=Counter)
    system_event_type_counts: Counter[str] = Field(default_factory=Counter)

    def to_response_dict(self) -> dict:
        """Convert counters to plain JSON-serializable dict."""
        return {
            "total_requests": self.total_requests,
            "challenge_requests": self.challenge_requests,
            "message_events": self.message_events,
            "system_events": self.system_events,
            "dropped_by_raw_handler": self.dropped_by_raw_handler,
            "invalid_verify_token": self.invalid_verify_token,
            "errors": self.errors,
            "event_type_counts": dict(self.event_type_counts),
            "channel_type_counts": dict(self.channel_type_counts),
            "system_event_type_counts": dict(self.system_event_type_counts),
        }


class WebhookApp(Generic[ContextDataT]):
    """Webhook application with typed context support

    Generic parameter ContextDataT allows type-safe custom application context.
    """

    def __init__(
        self,
        config: Optional[Config] = None,
        context_factory: Optional[Callable[["WebhookApp[ContextDataT]"], ContextDataT]] = None,
    ):
        self.config = config or Config()
        self._context_factory = context_factory
        self._context_data: Optional[ContextDataT] = None
        self.event_manager = EventManager(app=self, command_prefix=self.config.command_prefix)
        self.logger = get_logger("kook_webhook.app")
        self._event_stats = EventStats()

        # Sanic application
        self.app = Sanic(self.config.name)
        self.app.exception(NotFound)(self._not_found_handler)
        self._setup_routes()

        # Kook Client
        self.bot = KookClient(self.config.bot_token)
        if self.config.bot_user_id:
            self.bot.bot_user_id = self.config.bot_user_id

    def _get_context_data(self) -> ContextDataT:
        """Lazy initialize context data

        :return: Context data object
        """
        if self._context_data is None:
            if self._context_factory:
                self._context_data = self._context_factory(self)
            else:
                # Backward compatibility: create a SimpleNamespace
                self._context_data = SimpleNamespace()  # type: ignore
        return self._context_data

    def _create_context(self) -> Context[ContextDataT]:
        """Create handler context

        :return: Context object
        """
        return Context(self, self._get_context_data())

    def _setup_routes(self):
        """Setup routes"""
        self.add_http_route(
            self.config.webhook_endpoint,
            ["POST"],
            self._webhook_handler,
            require_auth=False,
        )
        self.add_http_route(
            self.config.healthz_endpoint,
            ["GET"],
            self._healthz_handler,
            require_auth=False,
        )
        self.add_http_route(
            self.config.stats_endpoint,
            ["GET"],
            self._stats_handler,
            require_auth=True,
        )

    def add_route(self, path: str, methods: list[str], handler: Callable):
        """Register route"""
        self.add_http_route(path, methods, handler, require_auth=False)

    def _auth_is_active(self) -> bool:
        """Whether token auth is effectively enabled."""
        return self.config.auth_enabled and bool(self.config.auth_token)

    def _is_authorized(self, request) -> bool:
        """Validate request auth token from header."""
        token = request.headers.get(self.config.auth_header_name, "")
        return token == self.config.auth_token

    def _wrap_handler_with_auth(self, handler: Callable, require_auth: bool) -> Callable:
        """Wrap route handler to support optional token auth."""

        @wraps(handler)
        async def wrapped(request, *args, **kwargs):
            if require_auth and self._auth_is_active() and not self._is_authorized(request):
                return response.text("Unauthorized", status=401)
            result = handler(request, *args, **kwargs)
            if isawaitable(result):
                return await result
            return result

        return wrapped

    def add_http_route(
        self,
        path: str,
        methods: list[str],
        handler: Callable,
        *,
        require_auth: bool = False,
    ):
        """Register route with optional auth enforcement."""
        wrapped_handler = self._wrap_handler_with_auth(handler, require_auth=require_auth)
        self.app.route(path, methods)(wrapped_handler)

    @property
    def events(self) -> EventManager:
        """Access event manager"""
        return self.event_manager

    def on_raw(
        self,
        func: RawHandler,
        *,
        priority: EventPriority = EventPriority.NORMAL,
        metadata: dict = None,
    ):
        """Register raw event handler"""
        if metadata is None:
            metadata = {}
        self.event_manager.on_raw(priority=priority, **metadata)(func)

    def on_message(
        self,
        func: MessageHandler,
        *,
        priority: EventPriority = EventPriority.NORMAL,
        metadata: dict = None,
    ):
        """Register message event handler"""
        if metadata is None:
            metadata = {}
        self.event_manager.on_message(priority=priority, **metadata)(func)

    def on_mention(
        self,
        mentions: list[str],
        func: MessageHandler,
        *,
        priority: EventPriority = EventPriority.NORMAL,
        metadata: dict = None,
    ):
        """Register message event handler"""
        if metadata is None:
            metadata = {}
        self.event_manager.on_message(priority=priority, mentions=mentions, **metadata)(func)

    def on_command(
        self,
        pattern: str,
        func: CommandHandler,
        *,
        priority: EventPriority = EventPriority.NORMAL,
        name: str = None,
        description: str = None,
        metadata: dict = None,
    ):
        """Register command event handler"""
        if metadata is None:
            metadata = {}
        self.event_manager.on_command(
            pattern=pattern,
            priority=priority,
            name=name,
            description=description,
            **metadata,
        )(func)

    def on_system(
        self,
        event_type: str,
        func: SystemHandler,
        *,
        priority: EventPriority = EventPriority.NORMAL,
        metadata: dict = None,
    ):
        """Register system event handler"""
        if metadata is None:
            metadata = {}
        self.event_manager.on_system(event_type=event_type, priority=priority, **metadata)(func)

    def on_error(self, func: ErrorHandler):
        """Register error event handler"""
        self.event_manager.on_error()(func)

    def on_post(
        self,
        func: PostHandler,
        *,
        priority: EventPriority = EventPriority.NORMAL,
        metadata: dict = None,
    ):
        """Register post event handler"""
        if metadata is None:
            metadata = {}
        self.event_manager.on_post(priority=priority, **metadata)(func)

    def run(self, **kwargs):
        """Start server"""
        # Merge configuration
        host = kwargs.get("host", self.config.host)
        port = kwargs.get("port", self.config.port)
        access_log = kwargs.get("access_log", self.config.access_log)
        debug = kwargs.get("debug", False)
        motd = kwargs.get("motd", False)

        self.logger.info(f"Starting KOOK Webhook server - {host}:{port}")
        self.logger.info(f"Handler statistics: {self.event_manager.list_handlers()}")
        self.app.run(
            host=host,
            port=port,
            access_log=access_log,
            debug=debug,
            motd=motd,
            single_process=True,
        )

    async def _not_found_handler(self, request, exception):
        """Return plain text for unknown routes."""
        return response.text("404", status=404)

    async def _webhook_handler(self, request):
        """Handle KOOK Webhook request"""
        try:
            self._event_stats.total_requests += 1

            # Check compression parameter
            compress = request.args.get("compress", "1") != "0"
            if self.config.auto_compress:
                compress = True

            # Decompress
            if compress and request.body:
                try:
                    decompressed_data = zlib.decompress(request.body)
                except zlib.error:
                    decompressed_data = request.body
            else:
                decompressed_data = request.body

            # Parse JSON
            data = orjson.loads(decompressed_data)

            # Decrypt
            if "encrypt" in data and self.config.encrypt_key:
                data_str = self._decrypt_message(data["encrypt"], self.config.encrypt_key)
                data = orjson.loads(data_str)

            # Parse to Pydantic model
            message = WebhookMessage(**data)
            webhook_data = message.d

            # Check if it's a CHALLENGE request
            if webhook_data.channel_type == "WEBHOOK_CHALLENGE":
                challenge = webhook_data.challenge
                verify_token = webhook_data.verify_token

                self.logger.info(
                    f"Received CHALLENGE request: challenge={challenge}, verify_token={verify_token}"
                )
                self._event_stats.challenge_requests += 1

                if verify_token and verify_token != self.config.verify_token:
                    self.logger.warning(
                        f"verify_token mismatch! Expected: {self.config.verify_token}, Received: {verify_token}"
                    )
                    self._event_stats.invalid_verify_token += 1
                    return response.text("Invalid verify_token", status=401)

                return response.json({"challenge": challenge})

            # Check verify_token
            if webhook_data.verify_token and webhook_data.verify_token != self.config.verify_token:
                self.logger.warning(
                    f"verify_token mismatch! Expected: {self.config.verify_token}, Received: {webhook_data.verify_token}"
                )
                self._event_stats.invalid_verify_token += 1
                return response.text("Invalid verify_token", status=401)

            self._event_stats.event_type_counts[str(webhook_data.type)] += 1
            self._event_stats.channel_type_counts[str(webhook_data.channel_type)] += 1

            # Trigger raw event handlers
            should_continue = await self.event_manager.emit_raw(data)
            if not should_continue:
                self._event_stats.dropped_by_raw_handler += 1
                return response.text("OK", status=200)

            # Parse event data
            event = WebhookEvent(
                channel_type=webhook_data.channel_type,
                type=webhook_data.type,
                target_id=webhook_data.target_id,
                author_id=webhook_data.author_id,
                content=webhook_data.content,
                msg_id=webhook_data.msg_id,
                msg_timestamp=webhook_data.msg_timestamp,
                nonce=webhook_data.nonce,
                extra=webhook_data.extra,
            )

            # Dispatch based on message type
            if webhook_data.type == MessageType.SYSTEM:
                # System message
                self._event_stats.system_events += 1
                if webhook_data.extra:
                    extra = SystemEventExtra(**webhook_data.extra)
                    self._event_stats.system_event_type_counts[str(extra.type)] += 1
                    await self.event_manager.emit_system(extra.type, event, extra)
            else:
                # Regular message
                self._event_stats.message_events += 1
                if webhook_data.extra:
                    extra = MessageExtra(**webhook_data.extra)
                    await self.event_manager.emit_message(event, extra, webhook_data.content)

            # Trigger post handlers
            await self.event_manager.emit_post(event)

            return response.text("OK", status=200)

        except Exception as e:
            import traceback

            traceback.print_exc()
            self.logger.error(f"Error handling Webhook request: {e}")
            self._event_stats.errors += 1
            return response.text("Internal Server Error", status=500)

    async def _healthz_handler(self, request):
        """Root path for health check"""
        return response.text("ok")

    async def _stats_handler(self, request):
        """Return internal event statistics."""
        return response.json(self._event_stats.to_response_dict())

    def _decrypt_message(self, encrypted_data: str, encrypt_key: str) -> str:
        """Decrypt encrypted message"""
        # Pad key to 32 bytes with \0
        key = (encrypt_key + "\0" * 32)[:32].encode("utf-8")

        # Base64 decode
        str_bytes = base64.b64decode(encrypted_data)
        iv = str_bytes[0:16]
        cipher_text = str_bytes[16:]

        # AES-256-CBC decrypt
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(base64.b64decode(cipher_text))

        # Remove PKCS7 padding
        padding_len = decrypted[-1] if isinstance(decrypted[-1], int) else ord(decrypted[-1])
        decrypted = decrypted[:-padding_len]

        return decrypted.decode("utf-8")
