"""Tests for builtin_handlers module"""

import pytest

from kook_webhook.builtin_handlers import (
    builtin_help_command,
    log_message_summary,
    log_raw_event,
    log_system_event,
)
from kook_webhook.event_manager import Context
from kook_webhook.models import MessageExtra, SystemEventExtra, User, WebhookEvent


class TestBuiltinHandlers:
    """Tests for builtin event handlers"""

    @pytest.mark.asyncio
    async def test_log_raw_event(self, app):
        """Test log_raw_event handler"""
        ctx = Context(app)
        raw_data = {
            "d": {
                "msg_id": "msg123",
                "type": 1,
                "channel_type": "GROUP",
            }
        }

        # Should not raise exception
        await log_raw_event(ctx, raw_data)

    @pytest.mark.asyncio
    async def test_log_raw_event_missing_fields(self, app):
        """Test log_raw_event with missing fields"""
        ctx = Context(app)
        raw_data = {"d": {}}

        # Should handle missing fields gracefully
        await log_raw_event(ctx, raw_data)

    @pytest.mark.asyncio
    async def test_log_message_summary(self, app):
        """Test log_message_summary handler"""
        ctx = Context(app)
        user = User(id="123", username="testuser", identify_num="0001")
        event = WebhookEvent(
            channel_type="GROUP",
            type=1,
            target_id="target123",
            author_id="123",
            content="Hello, World!",
            msg_id="msg123",
            msg_timestamp=1234567890,
            extra={},
        )
        extra = MessageExtra(
            type=1,
            guild_id="guild123",
            channel_name="test-channel",
            author=user,
        )
        content = "Hello, World!"

        # Should not raise exception
        await log_message_summary(ctx, event, extra, content)

    @pytest.mark.asyncio
    async def test_log_message_summary_long_content(self, app):
        """Test log_message_summary with long content"""
        ctx = Context(app)
        user = User(id="123", username="testuser", identify_num="0001")
        event = WebhookEvent(
            channel_type="GROUP",
            type=1,
            target_id="target123",
            author_id="123",
            content="A" * 100,
            msg_id="msg123",
            msg_timestamp=1234567890,
            extra={},
        )
        extra = MessageExtra(
            type=1,
            guild_id="guild123",
            channel_name="test-channel",
            author=user,
        )
        content = "A" * 100

        # Should not raise exception and truncate content
        await log_message_summary(ctx, event, extra, content)

    @pytest.mark.asyncio
    async def test_builtin_help_command(self, app):
        """Test builtin_help_command handler"""
        ctx = Context(app)
        user = User(id="123", username="testuser")
        event = WebhookEvent(
            channel_type="GROUP",
            type=9,
            target_id="target123",
            author_id="123",
            content="/help",
            msg_id="msg123",
            msg_timestamp=1234567890,
            extra={},
        )
        extra = MessageExtra(
            type=9,
            guild_id="guild123",
            channel_name="test-channel",
            author=user,
        )

        # Register some commands
        @app.events.on_command("test", description="Test command")
        async def test_command(ctx, event, extra, command, args):
            pass

        # Should return False to block subsequent handlers
        result = await builtin_help_command(ctx, event, extra, "help", "")
        assert result is False

    @pytest.mark.asyncio
    async def test_builtin_help_command_with_args(self, app):
        """Test builtin_help_command with arguments"""
        ctx = Context(app)
        user = User(id="123", username="testuser")
        event = WebhookEvent(
            channel_type="GROUP",
            type=9,
            target_id="target123",
            author_id="123",
            content="/help test",
            msg_id="msg123",
            msg_timestamp=1234567890,
            extra={},
        )
        extra = MessageExtra(
            type=9,
            guild_id="guild123",
            channel_name="test-channel",
            author=user,
        )

        result = await builtin_help_command(ctx, event, extra, "help", "test")
        assert result is False

    @pytest.mark.asyncio
    async def test_log_system_event(self, app):
        """Test log_system_event handler"""
        ctx = Context(app)
        event = WebhookEvent(
            channel_type="GROUP",
            type=255,
            target_id="target123",
            author_id="123",
            content="",
            msg_id="sys123",
            msg_timestamp=1234567890,
            extra={},
        )
        extra = SystemEventExtra(
            type="joined_guild",
            body={"user_id": "123", "joined_at": 1234567890},
        )

        # Should not raise exception
        await log_system_event(ctx, event, extra)

    @pytest.mark.asyncio
    async def test_log_system_event_various_types(self, app):
        """Test log_system_event with various event types"""
        ctx = Context(app)
        event = WebhookEvent(
            channel_type="GROUP",
            type=255,
            target_id="target123",
            author_id="123",
            content="",
            msg_id="sys123",
            msg_timestamp=1234567890,
            extra={},
        )

        event_types = [
            "joined_guild",
            "exited_guild",
            "updated_guild",
            "deleted_guild",
            "added_reaction",
            "deleted_reaction",
            "updated_message",
            "deleted_message",
        ]

        for event_type in event_types:
            extra = SystemEventExtra(type=event_type, body={})
            await log_system_event(ctx, event, extra)

    @pytest.mark.asyncio
    async def test_handlers_with_custom_attributes(self, app):
        """Test handlers accessing custom app attributes"""
        ctx = Context(app)

        # Add custom attribute to app
        app.custom_data = {"test": "value"}

        # Access through context
        assert ctx.custom_data == {"test": "value"}

        user = User(id="123", username="testuser", identify_num="0001")
        event = WebhookEvent(
            channel_type="GROUP",
            type=1,
            target_id="target123",
            author_id="123",
            content="Hello",
            msg_id="msg123",
            msg_timestamp=1234567890,
            extra={},
        )
        extra = MessageExtra(
            type=1,
            guild_id="guild123",
            channel_name="test-channel",
            author=user,
        )

        # Handlers should be able to access custom attributes through context
        await log_message_summary(ctx, event, extra, "Hello")
