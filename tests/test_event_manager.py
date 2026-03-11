"""Tests for event_manager module"""

import pytest

from kook_webhook.event_manager import (
    CommandHandlerWrapper,
    Context,
    EventHandler,
    EventManager,
    EventPriority,
    MessageHandlerWrapper,
)
from kook_webhook.models import MessageExtra, SystemEventExtra, User, WebhookEvent


class TestContext:
    """Tests for Context class"""

    def test_context_creation(self, app):
        """Test context creation"""
        ctx = Context(app)
        assert ctx.app is app

    def test_config_property(self, app):
        """Test config property"""
        ctx = Context(app)
        assert ctx.config is app.config

    def test_logger_property(self, app):
        """Test logger property"""
        ctx = Context(app)
        assert ctx.logger is app.logger

    def test_custom_attribute_access(self, app):
        """Test custom attribute access"""
        app.custom_attr = "test_value"
        ctx = Context(app)
        assert ctx.custom_attr == "test_value"

    def test_missing_attribute(self, app):
        """Test missing attribute raises AttributeError"""
        ctx = Context(app)
        with pytest.raises(AttributeError):
            _ = ctx.nonexistent_attribute


class TestEventPriority:
    """Tests for EventPriority enum"""

    def test_priority_values(self):
        """Test priority values"""
        assert EventPriority.HIGHEST.value == 0
        assert EventPriority.HIGH.value == 1
        assert EventPriority.NORMAL.value == 2
        assert EventPriority.LOW.value == 3
        assert EventPriority.LOWEST.value == 4

    def test_priority_ordering(self):
        """Test priority ordering"""
        priorities = [
            EventPriority.LOWEST,
            EventPriority.NORMAL,
            EventPriority.HIGHEST,
            EventPriority.LOW,
            EventPriority.HIGH,
        ]
        sorted_priorities = sorted(priorities, key=lambda p: p.value)
        assert sorted_priorities[0] == EventPriority.HIGHEST
        assert sorted_priorities[-1] == EventPriority.LOWEST


class TestCommandHandlerWrapper:
    """Tests for CommandHandlerWrapper"""

    def test_exact_match(self):
        """Test exact command match"""

        async def handler(ctx, event, extra, command, args):
            pass

        wrapper = CommandHandlerWrapper(pattern="help", callback=handler)
        assert wrapper.match("help") is True
        assert wrapper.match("help with args") is True
        assert wrapper.match("hello") is False

    def test_wildcard_match(self):
        """Test wildcard match"""

        async def handler(ctx, event, extra, command, args):
            pass

        wrapper = CommandHandlerWrapper(pattern="*", callback=handler)
        assert wrapper.match("anything") is True
        assert wrapper.match("help") is True
        assert wrapper.match("test command") is True

    def test_regex_match(self):
        """Test regex match"""

        async def handler(ctx, event, extra, command, args):
            pass

        wrapper = CommandHandlerWrapper(pattern="regex:^test.*", callback=handler)
        assert wrapper.match("test") is True
        assert wrapper.match("testing") is True
        assert wrapper.match("help") is False

    def test_metadata(self):
        """Test command metadata"""

        async def handler(ctx, event, extra, command, args):
            pass

        wrapper = CommandHandlerWrapper(
            pattern="help",
            callback=handler,
            name="Help Command",
            description="Show help",
            priority=EventPriority.HIGH,
            metadata={"category": "general"},
        )
        assert wrapper.name == "Help Command"
        assert wrapper.description == "Show help"
        assert wrapper.priority == EventPriority.HIGH
        assert wrapper.metadata["category"] == "general"


class TestMessageHandlerWrapper:
    """Tests for MessageHandlerWrapper"""

    def test_no_filters(self):
        """Test message handler with no filters"""

        async def handler(ctx, event, extra, content):
            pass

        wrapper = MessageHandlerWrapper(callback=handler)
        assert wrapper.match("GROUP", 1, "guild123", "user456") is True
        assert wrapper.match("PERSON", 9, None, "user789") is True

    def test_channel_type_filter(self):
        """Test channel type filter"""

        async def handler(ctx, event, extra, content):
            pass

        wrapper = MessageHandlerWrapper(
            callback=handler,
            channel_types=["GROUP"],
        )
        assert wrapper.match("GROUP", 1) is True
        assert wrapper.match("PERSON", 1) is False

    def test_message_type_filter(self):
        """Test message type filter"""

        async def handler(ctx, event, extra, content):
            pass

        wrapper = MessageHandlerWrapper(
            callback=handler,
            message_types=[1, 9],
        )
        assert wrapper.match("GROUP", 1) is True
        assert wrapper.match("GROUP", 9) is True
        assert wrapper.match("GROUP", 2) is False

    def test_guild_filter(self):
        """Test guild ID filter"""

        async def handler(ctx, event, extra, content):
            pass

        wrapper = MessageHandlerWrapper(
            callback=handler,
            guild_ids=["guild123", "guild456"],
        )
        assert wrapper.match("GROUP", 1, "guild123") is True
        assert wrapper.match("GROUP", 1, "guild789") is False

    def test_user_filter(self):
        """Test user ID filter"""

        async def handler(ctx, event, extra, content):
            pass

        wrapper = MessageHandlerWrapper(
            callback=handler,
            user_ids=["user123", "user456"],
        )
        assert wrapper.match("GROUP", 1, None, "user123") is True
        assert wrapper.match("GROUP", 1, None, "user789") is False

    def test_combined_filters(self):
        """Test combined filters"""

        async def handler(ctx, event, extra, content):
            pass

        wrapper = MessageHandlerWrapper(
            callback=handler,
            channel_types=["GROUP"],
            message_types=[1],
            guild_ids=["guild123"],
        )
        assert wrapper.match("GROUP", 1, "guild123") is True
        assert wrapper.match("PERSON", 1, "guild123") is False
        assert wrapper.match("GROUP", 2, "guild123") is False
        assert wrapper.match("GROUP", 1, "guild456") is False


class TestEventManager:
    """Tests for EventManager"""

    def test_initialization(self):
        """Test event manager initialization"""
        manager = EventManager()
        assert manager._app is None
        assert manager.raw_handlers == []
        assert manager.message_handlers == []
        assert manager.command_handlers == []
        assert manager.system_handlers == {}
        assert manager.error_handlers == []
        assert manager.post_handlers == []

    def test_set_app(self, app):
        """Test setting app"""
        manager = EventManager()
        manager.set_app(app)
        assert manager._app is app

    def test_get_context_without_app(self):
        """Test getting context without app raises error"""
        manager = EventManager()
        with pytest.raises(RuntimeError):
            manager._get_context()

    def test_get_context_with_app(self, app):
        """Test getting context with app"""
        manager = EventManager()
        manager.set_app(app)
        ctx = manager._get_context()
        assert isinstance(ctx, Context)
        assert ctx.app is app

    def test_on_raw_decorator(self, app):
        """Test raw event handler registration"""
        manager = app.event_manager

        @manager.on_raw()
        async def handler(ctx, raw_data):
            pass

        assert len(manager.raw_handlers) == 1
        assert manager.raw_handlers[0].callback == handler

    def test_on_message_decorator(self, app):
        """Test message handler registration"""
        manager = app.event_manager

        @manager.on_message(channel_types=["GROUP"])
        async def handler(ctx, event, extra, content):
            pass

        assert len(manager.message_handlers) == 1
        assert manager.message_handlers[0].callback == handler
        assert manager.message_handlers[0].channel_types == ["GROUP"]

    def test_on_command_decorator(self, app):
        """Test command handler registration"""
        manager = app.event_manager

        @manager.on_command("help")
        async def handler(ctx, event, extra, command, args):
            pass

        assert len(manager.command_handlers) == 1
        assert manager.command_handlers[0].callback == handler
        assert manager.command_handlers[0].pattern == "help"

    def test_on_system_decorator(self, app):
        """Test system event handler registration"""
        manager = app.event_manager

        @manager.on_system("joined_guild")
        async def handler(ctx, event, extra):
            pass

        assert "joined_guild" in manager.system_handlers
        assert len(manager.system_handlers["joined_guild"]) == 1

    def test_on_error_decorator(self, app):
        """Test error handler registration"""
        manager = app.event_manager

        @manager.on_error()
        async def handler(ctx, error, handler, handler_type, context):
            pass

        assert len(manager.error_handlers) == 1

    def test_on_post_decorator(self, app):
        """Test post handler registration"""
        manager = app.event_manager

        @manager.on_post()
        async def handler(ctx, event):
            pass

        assert len(manager.post_handlers) == 1

    @pytest.mark.asyncio
    async def test_emit_raw(self, app):
        """Test emitting raw events"""
        manager = app.event_manager
        called = []

        @manager.on_raw()
        async def handler(ctx, raw_data):
            called.append(raw_data)

        result = await manager.emit_raw({"test": "data"})
        assert result is True
        assert len(called) == 1
        assert called[0] == {"test": "data"}

    @pytest.mark.asyncio
    async def test_emit_raw_blocking(self, app):
        """Test raw event blocking"""
        manager = app.event_manager
        called = []

        @manager.on_raw()
        async def handler1(ctx, raw_data):
            called.append(1)
            return False  # Block

        @manager.on_raw()
        async def handler2(ctx, raw_data):
            called.append(2)

        result = await manager.emit_raw({})
        assert result is False
        assert called == [1]  # handler2 should not be called

    @pytest.mark.asyncio
    async def test_emit_message(self, app):
        """Test emitting message events"""
        manager = app.event_manager
        called = []

        @manager.on_message()
        async def handler(ctx, event, extra, content):
            called.append(content)

        user = User(id="123", username="test")
        event = WebhookEvent(
            channel_type="GROUP",
            type=1,
            target_id="target",
            author_id="123",
            content="Hello",
            msg_id="msg123",
            msg_timestamp=123456,
            extra={},
        )
        extra = MessageExtra(type=1, guild_id="guild", channel_name="test", author=user)

        await manager.emit_message(event, extra, "Hello")
        assert len(called) == 1
        assert called[0] == "Hello"

    @pytest.mark.asyncio
    async def test_emit_command(self, app):
        """Test emitting command events"""
        manager = app.event_manager
        called = []

        @manager.on_command("test")
        async def handler(ctx, event, extra, command, args):
            called.append((command, args))

        user = User(id="123", username="test")
        event = WebhookEvent(
            channel_type="GROUP",
            type=1,
            target_id="target",
            author_id="123",
            content="/test arg1 arg2",
            msg_id="msg123",
            msg_timestamp=123456,
            extra={},
        )
        extra = MessageExtra(type=1, guild_id="guild", channel_name="test", author=user)

        await manager.emit_message(event, extra, "/test arg1 arg2")
        assert len(called) == 1
        assert called[0] == ("test", "arg1 arg2")

    @pytest.mark.asyncio
    async def test_emit_system(self, app):
        """Test emitting system events"""
        manager = app.event_manager
        called = []

        @manager.on_system("joined_guild")
        async def handler(ctx, event, extra):
            called.append(extra.type)

        event = WebhookEvent(
            channel_type="GROUP",
            type=255,
            target_id="target",
            author_id="123",
            content="",
            msg_id="msg123",
            msg_timestamp=123456,
            extra={},
        )
        extra = SystemEventExtra(type="joined_guild", body={})

        await manager.emit_system("joined_guild", event, extra)
        assert len(called) == 1
        assert called[0] == "joined_guild"

    @pytest.mark.asyncio
    async def test_emit_post(self, app):
        """Test emitting post events"""
        manager = app.event_manager
        called = []

        @manager.on_post()
        async def handler(ctx, event):
            called.append(event.msg_id)

        event = WebhookEvent(
            channel_type="GROUP",
            type=1,
            target_id="target",
            author_id="123",
            content="Hello",
            msg_id="msg123",
            msg_timestamp=123456,
            extra={},
        )

        await manager.emit_post(event)
        assert len(called) == 1
        assert called[0] == "msg123"

    @pytest.mark.asyncio
    async def test_error_handling(self, app):
        """Test error handling"""
        manager = app.event_manager
        errors = []

        @manager.on_error()
        async def error_handler(ctx, error, handler, handler_type, context):
            errors.append((type(error).__name__, handler_type))

        @manager.on_raw()
        async def failing_handler(ctx, raw_data):
            raise ValueError("Test error")

        await manager.emit_raw({})
        assert len(errors) == 1
        assert errors[0][0] == "ValueError"
        assert errors[0][1] == "raw"

    def test_disable_handler(self, app):
        """Test disabling a handler"""
        manager = app.event_manager

        @manager.on_raw()
        async def handler(ctx, raw_data):
            pass

        assert manager.raw_handlers[0].enabled is True
        manager.disable_handler(handler)
        assert manager.raw_handlers[0].enabled is False

    def test_enable_handler(self, app):
        """Test enabling a handler"""
        manager = app.event_manager

        @manager.on_raw()
        async def handler(ctx, raw_data):
            pass

        manager.disable_handler(handler)
        assert manager.raw_handlers[0].enabled is False
        manager.enable_handler(handler)
        assert manager.raw_handlers[0].enabled is True

    def test_remove_handler(self, app):
        """Test removing a handler"""
        manager = app.event_manager

        @manager.on_raw()
        async def handler(ctx, raw_data):
            pass

        assert len(manager.raw_handlers) == 1
        manager.remove_handler(handler)
        assert len(manager.raw_handlers) == 0

    def test_list_commands(self, app):
        """Test listing commands"""
        manager = app.event_manager

        @manager.on_command("help", description="Show help")
        async def help_handler(ctx, event, extra, command, args):
            pass

        @manager.on_command("test")
        async def test_handler(ctx, event, extra, command, args):
            pass

        commands = manager.list_commands()
        assert len(commands) == 2
        assert commands[0]["pattern"] == "help"
        assert commands[0]["description"] == "Show help"

    def test_list_handlers(self, app):
        """Test listing handlers"""
        manager = app.event_manager

        @manager.on_raw()
        async def raw_handler(ctx, raw_data):
            pass

        @manager.on_message()
        async def msg_handler(ctx, event, extra, content):
            pass

        @manager.on_command("test")
        async def cmd_handler(ctx, event, extra, command, args):
            pass

        stats = manager.list_handlers()
        assert stats["raw"] == 1
        assert stats["message"] == 1
        assert stats["command"] == 1

    def test_priority_sorting(self, app):
        """Test handler priority sorting"""
        manager = app.event_manager
        order = []

        @manager.on_raw(priority=EventPriority.LOW)
        async def low_handler(ctx, raw_data):
            order.append("low")

        @manager.on_raw(priority=EventPriority.HIGH)
        async def high_handler(ctx, raw_data):
            order.append("high")

        @manager.on_raw(priority=EventPriority.HIGHEST)
        async def highest_handler(ctx, raw_data):
            order.append("highest")

        # Check handlers are sorted by priority
        assert manager.raw_handlers[0].priority == EventPriority.HIGHEST
        assert manager.raw_handlers[1].priority == EventPriority.HIGH
        assert manager.raw_handlers[2].priority == EventPriority.LOW

    @pytest.mark.asyncio
    async def test_disabled_handler_not_called(self, app):
        """Test that disabled handlers are not called"""
        manager = app.event_manager
        called = []

        @manager.on_raw()
        async def handler(ctx, raw_data):
            called.append(1)

        manager.disable_handler(handler)
        await manager.emit_raw({})
        assert len(called) == 0
