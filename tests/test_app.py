"""Tests for app module"""

import base64
import zlib
from typing import Callable, List

import orjson
import pytest
from Crypto.Cipher import AES

from kook_webhook.app import WebhookApp
from kook_webhook.config import Config
from kook_webhook.event_manager import EventPriority
from kook_webhook.models import MessageType


class TestWebhookApp:
    """Tests for WebhookApp"""

    def test_initialization(self):
        """Test app initialization"""
        from sanic import Sanic

        Sanic.test_mode = True
        app = WebhookApp()
        assert app.config is not None
        assert app.event_manager is not None
        assert app.logger is not None
        assert app.app is not None
        # Cleanup
        try:
            if app.config.name in Sanic._app_registry:
                del Sanic._app_registry[app.config.name]
        except Exception:
            pass
        Sanic.test_mode = False

    def test_initialization_with_config(self):
        """Test app initialization with custom config"""
        import uuid

        from sanic import Sanic

        Sanic.test_mode = True
        unique_name = f"custom_app_{uuid.uuid4().hex[:8]}"
        config = Config(
            name=unique_name,
            port=9000,
            webhook_endpoint="/kook-hook",
            healthz_endpoint="/kook-healthz",
            stats_endpoint="/kook-stats",
        )
        app = WebhookApp(config=config)
        assert app.config.name == unique_name
        assert app.config.port == 9000
        route_uris = [route.uri for route in app.app.router.routes]
        assert "/kook-hook" in route_uris
        assert "/kook-healthz" in route_uris
        assert "/kook-stats" in route_uris
        # Cleanup
        try:
            if config.name in Sanic._app_registry:
                del Sanic._app_registry[config.name]
        except Exception:
            pass
        Sanic.test_mode = False

    def test_events_property(self, app):
        """Test events property"""
        assert app.events is app.event_manager

    @pytest.mark.asyncio
    async def test_not_found_handler_returns_plain_text(self, app):
        """Unknown routes should return plain text 404."""
        from sanic.exceptions import NotFound

        request = type("Request", (), {})()
        exception = NotFound("not found")
        resp = await app._not_found_handler(request, exception)
        assert resp.status == 404
        assert resp.body == b"404"

    def test_run_uses_production_defaults_and_single_process(self, app, monkeypatch):
        """run should use prod-friendly defaults and keep single_process."""
        captured = {}

        def fake_run(_self, **kwargs):
            captured.update(kwargs)

        monkeypatch.setattr(type(app.app), "run", fake_run)
        app.run()

        assert captured["host"] == app.config.host
        assert captured["port"] == app.config.port
        assert captured["access_log"] == app.config.access_log
        assert captured["debug"] is False
        assert captured["motd"] is False
        assert captured["single_process"] is True

    @pytest.mark.asyncio
    async def test_healthz_handler(self, app):
        """Test index handler"""
        request = type("Request", (), {})()
        response = await app._healthz_handler(request)
        assert response.body == b"ok"
        assert response.status == 200

    @pytest.mark.asyncio
    async def test_webhook_challenge(self, app, sample_challenge):
        """Test webhook challenge handling"""
        # Create request mock
        request = type(
            "Request",
            (),
            {
                "args": {"compress": "0"},
                "body": orjson.dumps(sample_challenge),
            },
        )()

        response = await app._webhook_handler(request)
        assert response.status == 200
        response_data = orjson.loads(response.body)
        assert response_data["challenge"] == "challenge_token_123"

    @pytest.mark.asyncio
    async def test_webhook_challenge_invalid_token(self, app, sample_challenge):
        """Test webhook challenge with invalid verify_token"""
        sample_challenge["d"]["verify_token"] = "wrong_token"

        request = type(
            "Request",
            (),
            {
                "args": {"compress": "0"},
                "body": orjson.dumps(sample_challenge),
            },
        )()

        response = await app._webhook_handler(request)
        assert response.status == 401

    @pytest.mark.asyncio
    async def test_webhook_message(self, app, sample_webhook_message):
        """Test webhook message handling"""
        request = type(
            "Request",
            (),
            {
                "args": {"compress": "0"},
                "body": orjson.dumps(sample_webhook_message),
            },
        )()

        response = await app._webhook_handler(request)
        assert response.status == 200
        assert response.body == b"OK"

    @pytest.mark.asyncio
    async def test_webhook_compressed_message(self, app, sample_webhook_message):
        """Test webhook with compressed data"""
        uncompressed = orjson.dumps(sample_webhook_message)
        compressed = zlib.compress(uncompressed)

        request = type(
            "Request",
            (),
            {
                "args": {"compress": "1"},
                "body": compressed,
            },
        )()

        response = await app._webhook_handler(request)
        assert response.status == 200
        assert response.body == b"OK"

    @pytest.mark.asyncio
    async def test_webhook_auto_compress(self, app, sample_webhook_message):
        """Test auto compress setting"""
        app.config.auto_compress = True
        uncompressed = orjson.dumps(sample_webhook_message)
        compressed = zlib.compress(uncompressed)

        request = type(
            "Request",
            (),
            {
                "args": {"compress": "0"},  # Even with compress=0, should decompress
                "body": compressed,
            },
        )()

        response = await app._webhook_handler(request)
        assert response.status == 200

    @pytest.mark.asyncio
    async def test_webhook_invalid_verify_token(self, app, sample_webhook_message):
        """Test webhook with invalid verify_token"""
        sample_webhook_message["d"]["verify_token"] = "wrong_token"

        request = type(
            "Request",
            (),
            {
                "args": {"compress": "0"},
                "body": orjson.dumps(sample_webhook_message),
            },
        )()

        response = await app._webhook_handler(request)
        assert response.status == 401

    @pytest.mark.asyncio
    async def test_webhook_system_event(self, app, sample_system_event):
        """Test webhook system event handling"""
        request = type(
            "Request",
            (),
            {
                "args": {"compress": "0"},
                "body": orjson.dumps(sample_system_event),
            },
        )()

        response = await app._webhook_handler(request)
        assert response.status == 200

    @pytest.mark.asyncio
    async def test_webhook_command_message(self, app, sample_command_message):
        """Test webhook command message handling"""
        called = []

        @app.events.on_command("help")
        async def help_handler(ctx, event, extra, command, args):
            called.append((command, args))

        request = type(
            "Request",
            (),
            {
                "args": {"compress": "0"},
                "body": orjson.dumps(sample_command_message),
            },
        )()

        response = await app._webhook_handler(request)
        assert response.status == 200
        assert len(called) == 1
        assert called[0] == ("help", "test args")

    @pytest.mark.asyncio
    async def test_webhook_raw_handler_blocking(self, app, sample_webhook_message):
        """Test raw handler blocking subsequent processing"""
        called = []

        @app.events.on_raw()
        async def blocking_handler(ctx, raw_data):
            called.append("raw")
            return False  # Block

        @app.events.on_message()
        async def message_handler(ctx, event, extra, content):
            called.append("message")

        request = type(
            "Request",
            (),
            {
                "args": {"compress": "0"},
                "body": orjson.dumps(sample_webhook_message),
            },
        )()

        response = await app._webhook_handler(request)
        assert response.status == 200
        assert called == ["raw"]  # message handler should not be called

    @pytest.mark.asyncio
    async def test_webhook_error_handling(self, app):
        """Test error handling in webhook"""
        # Send invalid JSON to trigger an error
        request = type(
            "Request",
            (),
            {
                "args": {"compress": "0"},
                "body": b"invalid json",
            },
        )()

        response = await app._webhook_handler(request)
        # Should return 500 on error
        assert response.status == 500

    @pytest.mark.asyncio
    async def test_webhook_post_handler(self, app, sample_webhook_message):
        """Test post handler execution"""
        called = []

        @app.events.on_post()
        async def post_handler(ctx, event):
            called.append(event.msg_id)

        request = type(
            "Request",
            (),
            {
                "args": {"compress": "0"},
                "body": orjson.dumps(sample_webhook_message),
            },
        )()

        response = await app._webhook_handler(request)
        assert response.status == 200
        assert len(called) == 1

    def test_decrypt_message(self, app):
        """Test message decryption"""
        # Setup
        encrypt_key = "test_key_123456789012345678901234"
        app.config.encrypt_key = encrypt_key

        # Prepare encrypted data
        plaintext = b'{"test": "data"}'
        key = (encrypt_key + "\0" * 32)[:32].encode("utf-8")

        # Create IV and encrypt
        iv = b"0123456789abcdef"
        cipher = AES.new(key, AES.MODE_CBC, iv)

        # Add PKCS7 padding
        padding_len = 16 - (len(plaintext) % 16)
        padded = plaintext + bytes([padding_len] * padding_len)

        # Encrypt
        cipher_text = cipher.encrypt(padded)

        # Encode
        cipher_text_b64 = base64.b64encode(cipher_text)
        final_data = iv + cipher_text_b64
        encrypted_data = base64.b64encode(final_data).decode("utf-8")

        # Test decryption
        decrypted = app._decrypt_message(encrypted_data, encrypt_key)
        assert decrypted == plaintext.decode("utf-8")

    @pytest.mark.asyncio
    async def test_webhook_encrypted_message(self, app, sample_webhook_message):
        """Test encrypted webhook message"""
        # Setup encryption
        encrypt_key = "test_key_123456789012345678901234"
        app.config.encrypt_key = encrypt_key

        # Prepare encrypted data
        plaintext = orjson.dumps(sample_webhook_message)
        key = (encrypt_key + "\0" * 32)[:32].encode("utf-8")

        # Create IV and encrypt
        iv = b"0123456789abcdef"
        cipher = AES.new(key, AES.MODE_CBC, iv)

        # Add PKCS7 padding
        padding_len = 16 - (len(plaintext) % 16)
        padded = plaintext + bytes([padding_len] * padding_len)

        # Encrypt
        cipher_text = cipher.encrypt(padded)

        # Encode
        cipher_text_b64 = base64.b64encode(cipher_text)
        final_data = iv + cipher_text_b64
        encrypted_data = base64.b64encode(final_data).decode("utf-8")

        # Create encrypted message
        encrypted_message = {"encrypt": encrypted_data}

        request = type(
            "Request",
            (),
            {
                "args": {"compress": "0"},
                "body": orjson.dumps(encrypted_message),
            },
        )()

        response = await app._webhook_handler(request)
        assert response.status == 200

    @pytest.mark.asyncio
    async def test_webhook_message_handler_with_filters(self, app, sample_webhook_message):
        """Test message handler with filters"""
        called = []

        @app.events.on_message(channel_types=["GROUP"])
        async def group_handler(ctx, event, extra, content):
            called.append("group")

        @app.events.on_message(channel_types=["PERSON"])
        async def person_handler(ctx, event, extra, content):
            called.append("person")

        request = type(
            "Request",
            (),
            {
                "args": {"compress": "0"},
                "body": orjson.dumps(sample_webhook_message),
            },
        )()

        response = await app._webhook_handler(request)
        assert response.status == 200
        assert called == ["group"]  # Only group handler should be called

    def test_add_route(self, app):
        """Test add_route method"""
        called = []

        async def custom_handler(request):
            called.append("custom")
            from sanic import response

            return response.text("Custom Route")

        # Add custom route
        app.add_route("/custom", ["GET", "POST"], custom_handler)

        # Verify route is registered
        route_names = [route.name for route in app.app.router.routes]
        assert any("custom" in name for name in route_names)

    @pytest.mark.asyncio
    async def test_add_http_route_with_auth(self, app):
        """Test add_http_route with auth enabled"""
        app.config.auth_enabled = True
        app.config.auth_token = "test_auth_token"
        app.config.auth_header_name = "X-Webhook-Token"

        async def custom_handler(request):
            from sanic import response

            return response.text("Authorized")

        wrapped_handler = app._wrap_handler_with_auth(custom_handler, require_auth=True)

        unauthorized_request = type(
            "Request",
            (),
            {
                "headers": {},
            },
        )()
        unauthorized_response = await wrapped_handler(unauthorized_request)
        assert unauthorized_response.status == 401

        authorized_request = type(
            "Request",
            (),
            {
                "headers": {"X-Webhook-Token": "test_auth_token"},
            },
        )()
        authorized_response = await wrapped_handler(authorized_request)
        assert authorized_response.status == 200
        assert authorized_response.body == b"Authorized"

    @pytest.mark.asyncio
    async def test_add_http_route_auth_disabled_pass_through(self, app):
        """When auth is disabled, require_auth route should pass."""
        app.config.auth_enabled = False
        app.config.auth_token = "test_auth_token"
        app.config.auth_header_name = "X-Webhook-Token"

        async def custom_handler(request):
            from sanic import response

            return response.text("Allowed")

        wrapped_handler = app._wrap_handler_with_auth(custom_handler, require_auth=True)
        request = type(
            "Request",
            (),
            {
                "headers": {},
            },
        )()
        response = await wrapped_handler(request)
        assert response.status == 200
        assert response.body == b"Allowed"

    @pytest.mark.asyncio
    async def test_stats_handler(self, app, sample_webhook_message):
        """Test statistics endpoint data"""
        request = type(
            "Request",
            (),
            {
                "args": {"compress": "0"},
                "body": orjson.dumps(sample_webhook_message),
            },
        )()
        webhook_response = await app._webhook_handler(request)
        assert webhook_response.status == 200

        stats_request = type("Request", (), {})()
        stats_response = await app._stats_handler(stats_request)
        assert stats_response.status == 200
        stats_data = orjson.loads(stats_response.body)
        assert stats_data["total_requests"] == 1
        assert stats_data["message_events"] == 1
        assert stats_data["system_events"] == 0
        assert stats_data["event_type_counts"]["1"] == 1
        assert stats_data["channel_type_counts"]["GROUP"] == 1

    def test_on_raw_registration(self, app):
        """Test on_raw method registration"""
        called = []

        async def raw_handler(ctx, raw_data):
            called.append("raw")
            return True

        # Register handler using on_raw method
        app.on_raw(raw_handler, priority=EventPriority.HIGH, metadata={"test": "data"})

        # Verify handler is registered
        assert len(app.event_manager.raw_handlers) == 1
        handler = app.event_manager.raw_handlers[0]
        assert handler.callback == raw_handler
        assert handler.priority == EventPriority.HIGH
        assert handler.metadata == {"test": "data"}

    def test_on_raw_with_default_params(self, app):
        """Test on_raw method with default parameters"""

        async def raw_handler(ctx, raw_data):
            return True

        # Register handler with defaults
        app.on_raw(raw_handler)

        # Verify handler is registered with defaults
        assert len(app.event_manager.raw_handlers) == 1
        handler = app.event_manager.raw_handlers[0]
        assert handler.callback == raw_handler
        assert handler.priority == EventPriority.NORMAL
        assert handler.metadata == {}

    def test_on_message_registration(self, app):
        """Test on_message method registration"""
        called = []

        async def message_handler(ctx, event, extra, content):
            called.append("message")

        # Register handler using on_message method
        app.on_message(message_handler, priority=EventPriority.LOW, metadata={"test": "data"})

        # Verify handler is registered
        assert len(app.event_manager.message_handlers) == 1
        handler = app.event_manager.message_handlers[0]
        assert handler.callback == message_handler
        assert handler.priority == EventPriority.LOW
        assert handler.metadata == {"test": "data"}

    def test_on_message_with_default_params(self, app):
        """Test on_message method with default parameters"""

        async def message_handler(ctx, event, extra, content):
            pass

        # Register handler with defaults
        app.on_message(message_handler)

        # Verify handler is registered with defaults
        assert len(app.event_manager.message_handlers) == 1
        handler = app.event_manager.message_handlers[0]
        assert handler.callback == message_handler
        assert handler.priority == EventPriority.NORMAL
        assert handler.metadata == {}

    def test_on_command_registration(self, app):
        """Test on_command method registration"""
        called = []

        async def command_handler(ctx, event, extra, command, args):
            called.append((command, args))

        # Register handler using on_command method
        app.on_command(
            "help",
            command_handler,
            priority=EventPriority.HIGHEST,
            name="help_command",
            description="Help command",
            metadata={"test": "data"},
        )

        # Verify handler is registered
        assert len(app.event_manager.command_handlers) == 1
        handler = app.event_manager.command_handlers[0]
        assert handler.callback == command_handler
        assert handler.pattern == "help"
        assert handler.priority == EventPriority.HIGHEST
        assert handler.name == "help_command"
        assert handler.description == "Help command"
        assert handler.metadata == {"test": "data"}

    def test_on_command_with_default_params(self, app):
        """Test on_command method with default parameters"""

        async def command_handler(ctx, event, extra, command, args):
            pass

        # Register handler with defaults
        app.on_command("test", command_handler)

        # Verify handler is registered with defaults
        assert len(app.event_manager.command_handlers) == 1
        handler = app.event_manager.command_handlers[0]
        assert handler.callback == command_handler
        assert handler.pattern == "test"
        assert handler.priority == EventPriority.NORMAL
        assert handler.name == "test"
        assert handler.metadata == {}

    def test_on_system_registration(self, app):
        """Test on_system method registration"""
        called = []

        async def system_handler(ctx, event, extra):
            called.append(extra.type)

        # Register handler using on_system method
        app.on_system(
            "joined_guild", system_handler, priority=EventPriority.LOWEST, metadata={"test": "data"}
        )

        # Verify handler is registered
        assert "joined_guild" in app.event_manager.system_handlers
        assert len(app.event_manager.system_handlers["joined_guild"]) == 1
        handler = app.event_manager.system_handlers["joined_guild"][0]
        assert handler.callback == system_handler
        assert handler.priority == EventPriority.LOWEST
        assert handler.metadata == {"test": "data"}

    def test_on_system_with_default_params(self, app):
        """Test on_system method with default parameters"""

        async def system_handler(ctx, event, extra):
            pass

        # Register handler with defaults
        app.on_system("test_event", system_handler)

        # Verify handler is registered with defaults
        assert "test_event" in app.event_manager.system_handlers
        assert len(app.event_manager.system_handlers["test_event"]) == 1
        handler = app.event_manager.system_handlers["test_event"][0]
        assert handler.callback == system_handler
        assert handler.priority == EventPriority.NORMAL
        assert handler.metadata == {}

    def test_on_error_registration(self, app):
        """Test on_error method registration"""
        called = []

        async def error_handler(ctx, error, handler, handler_type, context):
            called.append(str(error))

        # Register handler using on_error method
        app.on_error(error_handler)

        # Verify handler is registered
        assert len(app.event_manager.error_handlers) == 1
        assert app.event_manager.error_handlers[0] == error_handler

    def test_on_post_registration(self, app):
        """Test on_post method registration"""
        called = []

        async def post_handler(ctx, event):
            called.append(event.msg_id)

        # Register handler using on_post method
        app.on_post(post_handler, priority=EventPriority.HIGH, metadata={"test": "data"})

        # Verify handler is registered
        assert len(app.event_manager.post_handlers) == 1
        handler = app.event_manager.post_handlers[0]
        assert handler.callback == post_handler
        assert handler.priority == EventPriority.HIGH
        assert handler.metadata == {"test": "data"}

    def test_on_post_with_default_params(self, app):
        """Test on_post method with default parameters"""

        async def post_handler(ctx, event):
            pass

        # Register handler with defaults
        app.on_post(post_handler)

        # Verify handler is registered with defaults
        assert len(app.event_manager.post_handlers) == 1
        handler = app.event_manager.post_handlers[0]
        assert handler.callback == post_handler
        assert handler.priority == EventPriority.NORMAL
        assert handler.metadata == {}

    @pytest.mark.asyncio
    async def test_on_raw_execution(self, app, sample_webhook_message):
        """Test on_raw handler execution"""
        called = []

        async def raw_handler(ctx, raw_data):
            called.append(raw_data["d"]["content"])
            return True

        app.on_raw(raw_handler)

        request = type(
            "Request",
            (),
            {
                "args": {"compress": "0"},
                "body": orjson.dumps(sample_webhook_message),
            },
        )()

        response = await app._webhook_handler(request)
        assert response.status == 200
        assert called == ["Hello, World!"]

    @pytest.mark.asyncio
    async def test_on_message_execution(self, app, sample_webhook_message):
        """Test on_message handler execution"""
        called = []

        async def message_handler(ctx, event, extra, content):
            called.append(content)

        app.on_message(message_handler)

        request = type(
            "Request",
            (),
            {
                "args": {"compress": "0"},
                "body": orjson.dumps(sample_webhook_message),
            },
        )()

        response = await app._webhook_handler(request)
        assert response.status == 200
        assert called == ["Hello, World!"]

    @pytest.mark.asyncio
    async def test_on_command_execution(self, app, sample_command_message):
        """Test on_command handler execution"""
        called = []

        async def command_handler(ctx, event, extra, command, args):
            called.append((command, args))

        app.on_command("help", command_handler)

        request = type(
            "Request",
            (),
            {
                "args": {"compress": "0"},
                "body": orjson.dumps(sample_command_message),
            },
        )()

        response = await app._webhook_handler(request)
        assert response.status == 200
        assert called == [("help", "test args")]

    @pytest.mark.asyncio
    async def test_on_system_execution(self, app, sample_system_event):
        """Test on_system handler execution"""
        called = []

        async def system_handler(ctx, event, extra):
            called.append(extra.type)

        app.on_system("joined_guild", system_handler)

        request = type(
            "Request",
            (),
            {
                "args": {"compress": "0"},
                "body": orjson.dumps(sample_system_event),
            },
        )()

        response = await app._webhook_handler(request)
        assert response.status == 200
        assert called == ["joined_guild"]

    @pytest.mark.asyncio
    async def test_on_error_execution(self, app, sample_webhook_message):
        """Test on_error handler execution"""
        error_called = []

        async def failing_handler(ctx, event, extra, content):
            raise ValueError("Test error")

        async def error_handler(ctx, error, handler, handler_type, context):
            error_called.append((str(error), handler_type))

        app.on_message(failing_handler)
        app.on_error(error_handler)

        request = type(
            "Request",
            (),
            {
                "args": {"compress": "0"},
                "body": orjson.dumps(sample_webhook_message),
            },
        )()

        response = await app._webhook_handler(request)
        assert response.status == 200
        assert len(error_called) == 1
        assert error_called[0][0] == "Test error"
        assert error_called[0][1] == "message"

    @pytest.mark.asyncio
    async def test_on_post_execution(self, app, sample_webhook_message):
        """Test on_post handler execution"""
        called = []

        async def post_handler(ctx, event):
            called.append(event.msg_id)

        app.on_post(post_handler)

        request = type(
            "Request",
            (),
            {
                "args": {"compress": "0"},
                "body": orjson.dumps(sample_webhook_message),
            },
        )()

        response = await app._webhook_handler(request)
        assert response.status == 200
        assert called == ["abc123"]

    @pytest.mark.asyncio
    async def test_multiple_handlers_priority(self, app, sample_webhook_message):
        """Test multiple handlers with different priorities"""
        execution_order = []

        async def high_priority_handler(ctx, raw_data):
            execution_order.append("high")
            return True

        async def normal_priority_handler(ctx, raw_data):
            execution_order.append("normal")
            return True

        async def low_priority_handler(ctx, raw_data):
            execution_order.append("low")
            return True

        # Register in reverse order to test priority sorting
        app.on_raw(low_priority_handler, priority=EventPriority.LOW)
        app.on_raw(high_priority_handler, priority=EventPriority.HIGH)
        app.on_raw(normal_priority_handler, priority=EventPriority.NORMAL)

        request = type(
            "Request",
            (),
            {
                "args": {"compress": "0"},
                "body": orjson.dumps(sample_webhook_message),
            },
        )()

        response = await app._webhook_handler(request)
        assert response.status == 200
        # Should execute in priority order: HIGH -> NORMAL -> LOW
        assert execution_order == ["high", "normal", "low"]
