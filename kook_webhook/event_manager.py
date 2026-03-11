import re
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    TypeVar,
    Union,
)

from .models import MessageExtra, SystemEventExtra, WebhookEvent
from .sdk import KookClient

if TYPE_CHECKING:
    from .app import WebhookApp

ContextDataT = TypeVar("ContextDataT")


class Context(Generic[ContextDataT]):
    """Handler execution context with typed custom data

    Generic parameter ContextDataT allows type-safe access to custom application context.
    """

    def __init__(self, app: "WebhookApp[ContextDataT]", data: ContextDataT = None):
        self.app = app
        self.data = data

    @property
    def config(self):
        """Access app configuration

        :return: Config object
        """
        return self.app.config

    @property
    def logger(self):
        """Access app logger

        :return: Logger object
        """
        return self.app.logger

    @property
    def bot(self) -> KookClient:
        """Access bot client

        :return: KookClient object
        """
        return self.app.bot

    def __getattr__(self, name: str) -> Any:
        """Backward compatibility: allow direct access to app attributes

        This is kept for backward compatibility. New code should use ctx.data instead.

        :param name: Attribute name
        :return: Attribute value
        """
        return getattr(self.app, name)


# Type aliases for handler callbacks (generic over ContextDataT)
RawHandler = Callable[[Context[Any], Dict[str, Any]], Awaitable[Optional[bool]]]
MessageHandler = Callable[
    [Context[Any], WebhookEvent, MessageExtra, str], Awaitable[Optional[bool]]
]
CommandHandler = Callable[
    [Context[Any], WebhookEvent, MessageExtra, str, str], Awaitable[Optional[bool]]
]
SystemHandler = Callable[[Context[Any], WebhookEvent, SystemEventExtra], Awaitable[Optional[bool]]]
ErrorHandler = Callable[[Context[Any], Exception, Any, str, Any], Awaitable[None]]
PostHandler = Callable[[Context[Any], WebhookEvent], Awaitable[None]]


class EventPriority(Enum):
    """Event priority"""

    HIGHEST = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    LOWEST = 4


@dataclass
class EventHandler:
    """Event handler for raw and post events"""

    callback: Union[RawHandler, PostHandler, SystemHandler]
    priority: EventPriority = EventPriority.NORMAL
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CommandHandlerWrapper:
    """Command handler wrapper"""

    pattern: str
    callback: CommandHandler
    priority: EventPriority = EventPriority.NORMAL
    enabled: bool = True
    name: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def match(self, command: str) -> bool:
        """Match command pattern

        :param command: Command name
        :return: Whether the command matches
        """
        if self.pattern == "*":
            return True
        if self.pattern.startswith("regex:"):
            pattern_str = self.pattern[6:]
            return re.match(pattern_str, command) is not None
        return command == self.pattern or command.startswith(self.pattern + " ")


@dataclass
class MessageHandlerWrapper:
    """Message handler wrapper"""

    callback: MessageHandler
    priority: EventPriority = EventPriority.NORMAL
    enabled: bool = True
    channel_types: Optional[List[str]] = None
    message_types: Optional[List[int]] = None
    guild_ids: Optional[List[str]] = None
    user_ids: Optional[List[str]] = None
    mention_ids: set = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def match(
        self,
        channel_type: str,
        message_type: int,
        guild_id: Optional[str] = None,
        user_id: Optional[str] = None,
        mention_ids: Optional[set[str]] = None,
    ) -> bool:
        """Match message against filter conditions

        :param channel_type: Channel type
        :param message_type: Message type
        :param guild_id: Guild ID (optional)
        :param user_id: User ID (optional)
        :param mention_ids: User IDs (optional)
        :return: Whether the message matches
        """
        if self.channel_types and channel_type not in self.channel_types:
            return False
        if self.message_types and message_type not in self.message_types:
            return False
        if self.guild_ids and guild_id not in self.guild_ids:
            return False
        if self.user_ids and user_id not in self.user_ids:
            return False
        if self.mention_ids and (mention_ids is None or not (mention_ids & self.mention_ids)):
            return False
        return True


class EventManager:
    """Event manager"""

    def __init__(self, app: Optional["WebhookApp"] = None, command_prefix: str = "/"):
        self._app = app
        self._command_prefix = command_prefix

        # Raw event handlers (executed before all other handlers)
        self.raw_handlers: List[EventHandler] = []

        # Message event handlers
        self.message_handlers: List[MessageHandlerWrapper] = []

        # Command handlers
        self.command_handlers: List[CommandHandlerWrapper] = []

        # System event handlers
        self.system_handlers: Dict[str, List[EventHandler]] = {}

        # Error handlers
        self.error_handlers: List[ErrorHandler] = []

        # Post handlers (executed after all other handlers)
        self.post_handlers: List[EventHandler] = []

    def set_app(self, app: "WebhookApp"):
        """Set WebhookApp reference (called after initialization)

        :param app: WebhookApp instance
        """
        self._app = app

    def _get_context(self) -> Context[Any]:
        """Get execution context

        :return: Context object
        """
        if self._app is None:
            raise RuntimeError("WebhookApp not set. Call set_app() first.")
        return self._app._create_context()

    def on_raw(self, priority: EventPriority = EventPriority.NORMAL, **metadata):
        """Register raw event handler (executed before parsing)

        Handler signature: async def handler(ctx: Context, raw_data: Dict[str, Any]) -> Optional[bool]

        :param priority: Handler priority (default: NORMAL)
        :param metadata: Custom metadata
        :return: Decorator function

        Handler parameters:
            - ctx: Execution context with access to app, config, logger, and custom attributes
            - raw_data: Raw event data dictionary

        Return value:
            - Return False to block subsequent handlers (like gin middleware model)
            - Return None or True to continue processing
        """

        def decorator(func: RawHandler):
            self.raw_handlers.append(
                EventHandler(callback=func, priority=priority, metadata=metadata)
            )
            self._sort_handlers(self.raw_handlers)
            return func

        return decorator

    def on_message(
        self,
        priority: EventPriority = EventPriority.NORMAL,
        channel_types: Optional[List[str]] = None,
        message_types: Optional[List[int]] = None,
        guild_ids: Optional[List[str]] = None,
        user_ids: Optional[List[str]] = None,
        mentions: Optional[List[str]] = None,
        **metadata,
    ):
        """Register message event handler

        Handler signature: async def handler(ctx: Context, event: WebhookEvent,
                                            extra: MessageExtra, content: str) -> Optional[bool]

        :param priority: Handler priority (default: NORMAL)
        :param channel_types: Channel type filter (e.g. ["GROUP", "PERSON"]), None for no filter
        :param message_types: Message type filter (e.g. [1, 9]), None for no filter
        :param guild_ids: Guild ID filter, None for no filter
        :param user_ids: User ID filter, None for no filter
        :param mentions: Mentions filter, None for no filter
        :param metadata: Custom metadata
        :return: Decorator function

        Handler parameters:
            - ctx: Execution context with access to app, config, logger, and custom attributes
            - event: Webhook event data
            - extra: Message extra information
            - content: Message content string

        Return value:
            - Return False to block subsequent handlers (like gin middleware model)
            - Return None or True to continue processing
        """

        def decorator(func: MessageHandler):
            self.message_handlers.append(
                MessageHandlerWrapper(
                    callback=func,
                    priority=priority,
                    channel_types=channel_types,
                    message_types=message_types,
                    guild_ids=guild_ids,
                    user_ids=user_ids,
                    mention_ids=set(mentions) if mentions else set(),
                    metadata=metadata,
                )
            )
            self._sort_handlers(self.message_handlers)
            return func

        return decorator

    def on_command(
        self,
        pattern: str,
        priority: EventPriority = EventPriority.NORMAL,
        name: Optional[str] = None,
        description: Optional[str] = None,
        **metadata,
    ):
        """Register command handler

        Handler signature: async def handler(ctx: Context, event: WebhookEvent,
                                            extra: MessageExtra, command: str, args: str) -> Optional[bool]

        :param pattern: Command pattern (exact match, wildcard "*", or "regex:..." for regex)
        :param priority: Handler priority (default: NORMAL)
        :param name: Command name (default: pattern)
        :param description: Command description
        :param metadata: Custom metadata
        :return: Decorator function

        Handler parameters:
            - ctx: Execution context with access to app, config, logger, and custom attributes
            - event: Webhook event data
            - extra: Message extra information
            - command: Command name (without /)
            - args: Command arguments string

        Return value:
            - Return False to block subsequent handlers (like gin middleware model)
            - Return None or True to continue processing
        """

        def decorator(func: CommandHandler):
            self.command_handlers.append(
                CommandHandlerWrapper(
                    pattern=pattern,
                    callback=func,
                    priority=priority,
                    name=name or pattern,
                    description=description,
                    metadata=metadata,
                )
            )
            self._sort_handlers(self.command_handlers)
            return func

        return decorator

    def on_system(
        self, event_type: str, priority: EventPriority = EventPriority.NORMAL, **metadata
    ):
        """Register system event handler

        Handler signature: async def handler(ctx: Context, event: WebhookEvent,
                                            extra: SystemEventExtra) -> Optional[bool]

        :param event_type: System event type (e.g. "joined_guild", "updated_guild")
        :param priority: Handler priority (default: NORMAL)
        :param metadata: Custom metadata
        :return: Decorator function

        Handler parameters:
            - ctx: Execution context with access to app, config, logger, and custom attributes
            - event: Webhook event data
            - extra: System event extra information

        Return value:
            - Return False to block subsequent handlers (like gin middleware model)
            - Return None or True to continue processing
        """

        def decorator(func: SystemHandler):
            if event_type not in self.system_handlers:
                self.system_handlers[event_type] = []
            self.system_handlers[event_type].append(
                EventHandler(callback=func, priority=priority, metadata=metadata)
            )
            self._sort_handlers(self.system_handlers[event_type])
            return func

        return decorator

    def on_error(self):
        """Register error handler

        Handler signature: async def handler(ctx: Context, error: Exception, handler: Any,
                                            handler_type: str, context: Any) -> None

        :return: Decorator function

        Handler parameters:
            - ctx: Execution context with access to app, config, logger, and custom attributes
            - error: The exception that occurred
            - handler: The handler that raised the error
            - handler_type: Type of handler (raw, message, command, system, post)
            - context: Additional context (event data, etc.)
        """

        def decorator(func: ErrorHandler):
            self.error_handlers.append(func)
            return func

        return decorator

    def on_post(self, priority: EventPriority = EventPriority.NORMAL, **metadata):
        """Register post handler (executed after all other handlers)

        Handler signature: async def handler(ctx: Context, event: WebhookEvent) -> None

        :param priority: Handler priority (default: NORMAL)
        :param metadata: Custom metadata
        :return: Decorator function

        Handler parameters:
            - ctx: Execution context with access to app, config, logger, and custom attributes
            - event: Webhook event data
        """

        def decorator(func: PostHandler):
            self.post_handlers.append(
                EventHandler(callback=func, priority=priority, metadata=metadata)
            )
            self._sort_handlers(self.post_handlers)
            return func

        return decorator

    async def emit_raw(self, raw_data: Dict[str, Any]) -> bool:
        """Trigger raw event handlers

        :param raw_data: Raw event data dictionary
        :return: False if processing should be blocked, True otherwise
        """
        ctx = self._get_context()
        for handler in self.raw_handlers:
            if not handler.enabled:
                continue
            try:
                result = await handler.callback(ctx, raw_data)
                if result is False:  # Block subsequent processing
                    return False
            except Exception as e:
                await self._handle_error(e, handler, "raw", raw_data)
        return True

    async def emit_message(
        self,
        event: WebhookEvent,
        extra: MessageExtra,
        content: str,
    ) -> bool:
        """Trigger message event handlers

        :param event: Webhook event data
        :param extra: Message extra information
        :param content: Message content string
        :return: False if processing should be blocked, True otherwise
        """
        ctx = self._get_context()
        # Execute general message handlers first
        for handler in self.message_handlers:
            if not handler.enabled:
                continue
            if not handler.match(
                event.channel_type,
                event.type,
                extra.guild_id,
                event.author_id,
                set(extra.mention),
            ):
                continue
            try:
                result = await handler.callback(ctx, event, extra, content)
                if result is False:  # Block subsequent processing
                    return False
            except Exception as e:
                await self._handle_error(e, handler, "message", event)

        # Check if it's a command
        if content.startswith(self._command_prefix):
            command = content.split()[0][len(self._command_prefix) :]  # Remove command prefix
            args = content.split(" ", 1)[1] if " " in content else ""
            for handler in self.command_handlers:
                if not handler.enabled:
                    continue
                if handler.match(command):
                    try:
                        result = await handler.callback(ctx, event, extra, command, args)
                        if result is False:  # Block subsequent processing
                            return False
                    except Exception as e:
                        await self._handle_error(e, handler, "command", event)

        return True

    async def emit_system(
        self, event_type: str, event: WebhookEvent, extra: SystemEventExtra
    ) -> bool:
        """Trigger system event handlers

        :param event_type: System event type
        :param event: Webhook event data
        :param extra: System event extra information
        :return: False if processing should be blocked, True otherwise
        """
        if event_type not in self.system_handlers:
            return True

        ctx = self._get_context()
        for handler in self.system_handlers[event_type]:
            if not handler.enabled:
                continue
            try:
                result = await handler.callback(ctx, event, extra)
                if result is False:  # Block subsequent processing
                    return False
            except Exception as e:
                await self._handle_error(e, handler, "system", event)
        return True

    async def emit_post(self, event: WebhookEvent) -> None:
        """Trigger post handlers

        :param event: Webhook event data
        """
        ctx = self._get_context()
        for handler in self.post_handlers:
            if not handler.enabled:
                continue
            try:
                await handler.callback(ctx, event)
            except Exception as e:
                await self._handle_error(e, handler, "post", event)

    async def _handle_error(self, error: Exception, handler: Any, handler_type: str, context: Any):
        """Handle error in handler execution

        :param error: The exception that occurred
        :param handler: The handler that raised the error
        :param handler_type: Type of handler (raw, message, command, system, post)
        :param context: Additional context (event data, etc.)
        """
        ctx = self._get_context()
        for error_handler in self.error_handlers:
            try:
                await error_handler(ctx, error, handler, handler_type, context)
            except Exception:
                pass

    def _sort_handlers(self, handlers: List[Any]):
        """Sort handlers by priority

        :param handlers: List of handlers to sort
        """
        handlers.sort(key=lambda h: h.priority.value)

    # ==================== Management Methods ====================

    def disable_handler(self, callback: Callable):
        """Disable a specific handler

        :param callback: Handler callback function to disable
        """
        for handler_list in [
            self.raw_handlers,
            self.message_handlers,
            self.command_handlers,
            self.post_handlers,
        ] + list(self.system_handlers.values()):
            for handler in handler_list:
                if handler.callback == callback:
                    handler.enabled = False

    def enable_handler(self, callback: Callable):
        """Enable a specific handler

        :param callback: Handler callback function to enable
        """
        for handler_list in [
            self.raw_handlers,
            self.message_handlers,
            self.command_handlers,
            self.post_handlers,
        ] + list(self.system_handlers.values()):
            for handler in handler_list:
                if handler.callback == callback:
                    handler.enabled = True

    def remove_handler(self, callback: Callable):
        """Remove a specific handler

        :param callback: Handler callback function to remove
        """
        self.raw_handlers = [h for h in self.raw_handlers if h.callback != callback]
        self.message_handlers = [h for h in self.message_handlers if h.callback != callback]
        self.command_handlers = [h for h in self.command_handlers if h.callback != callback]
        self.post_handlers = [h for h in self.post_handlers if h.callback != callback]
        for event_type in list(self.system_handlers.keys()):
            self.system_handlers[event_type] = [
                h for h in self.system_handlers[event_type] if h.callback != callback
            ]

    def list_commands(self) -> List[Dict[str, Any]]:
        """List all registered commands

        :return: List of command information dictionaries
        """
        return [
            {
                "name": handler.name,
                "pattern": handler.pattern,
                "description": handler.description,
                "enabled": handler.enabled,
                "priority": handler.priority.name,
            }
            for handler in self.command_handlers
        ]

    def list_handlers(self) -> Dict[str, Any]:
        """List all registered handlers statistics

        :return: Dictionary with handler counts by type
        """
        return {
            "raw": len(self.raw_handlers),
            "message": len(self.message_handlers),
            "command": len(self.command_handlers),
            "system": {k: len(v) for k, v in self.system_handlers.items()},
            "error": len(self.error_handlers),
            "post": len(self.post_handlers),
        }
