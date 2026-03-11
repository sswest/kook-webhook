"""Tests for models module"""

import pytest
from pydantic import ValidationError

from kook_webhook.models import (
    Attachment,
    Channel,
    ChannelType,
    Guild,
    MessageExtra,
    MessageType,
    Quote,
    Role,
    SystemEventExtra,
    User,
    WebhookChallenge,
    WebhookData,
    WebhookEncryptedMessage,
    WebhookEvent,
    WebhookMessage,
)


class TestUser:
    """Tests for User model"""

    def test_minimal_user(self):
        """Test user with minimal fields"""
        user = User(id="123", username="testuser")
        assert user.id == "123"
        assert user.username == "testuser"
        assert user.nickname is None

    def test_full_user(self):
        """Test user with all fields"""
        user = User(
            id="123",
            username="testuser",
            nickname="Test User",
            identify_num="0001",
            online=True,
            bot=False,
            status=1,
            avatar="avatar.png",
            roles=[1, 2, 3],
        )
        assert user.id == "123"
        assert user.username == "testuser"
        assert user.nickname == "Test User"
        assert user.identify_num == "0001"
        assert user.online is True
        assert user.bot is False
        assert user.roles == [1, 2, 3]


class TestRole:
    """Tests for Role model"""

    def test_role_creation(self):
        """Test role creation"""
        role = Role(
            role_id=1,
            name="Admin",
            color=255,
            position=1,
            hoist=0,
            mentionable=1,
            permissions=8,
        )
        assert role.role_id == 1
        assert role.name == "Admin"
        assert role.permissions == 8


class TestChannel:
    """Tests for Channel model"""

    def test_channel_creation(self):
        """Test channel creation"""
        channel = Channel(
            id="ch123",
            name="general",
            user_id="user123",
            guild_id="guild123",
            topic="General discussion",
            is_category=False,
            parent_id="",
            level=0,
            slow_mode=0,
            type=1,
            permission_sync=0,
            has_password=False,
        )
        assert channel.id == "ch123"
        assert channel.name == "general"
        assert channel.guild_id == "guild123"


class TestGuild:
    """Tests for Guild model"""

    def test_guild_creation(self):
        """Test guild creation"""
        guild = Guild(
            id="guild123",
            name="Test Guild",
            topic="Test",
            user_id="user123",
            icon="icon.png",
            notify_type=0,
            region="beijing",
            enable_open=True,
            open_id="open123",
            default_channel_id="ch123",
            welcome_channel_id="ch456",
        )
        assert guild.id == "guild123"
        assert guild.name == "Test Guild"
        assert guild.enable_open is True


class TestMessageType:
    """Tests for MessageType constants"""

    def test_message_types(self):
        """Test message type constants"""
        assert MessageType.TEXT == 1
        assert MessageType.IMAGE == 2
        assert MessageType.VIDEO == 3
        assert MessageType.FILE == 4
        assert MessageType.AUDIO == 8
        assert MessageType.KMARKDOWN == 9
        assert MessageType.CARD == 10
        assert MessageType.SYSTEM == 255


class TestChannelType:
    """Tests for ChannelType constants"""

    def test_channel_types(self):
        """Test channel type constants"""
        assert ChannelType.GROUP == "GROUP"
        assert ChannelType.PERSON == "PERSON"
        assert ChannelType.BROADCAST == "BROADCAST"


class TestQuote:
    """Tests for Quote model"""

    def test_quote_creation(self):
        """Test quote creation"""
        user = User(id="123", username="testuser")
        quote = Quote(
            id="quote123",
            type=1,
            content="Quoted message",
            create_at=1234567890,
            author=user,
        )
        assert quote.id == "quote123"
        assert quote.content == "Quoted message"
        assert quote.author.username == "testuser"


class TestAttachment:
    """Tests for Attachment model"""

    def test_attachment_creation(self):
        """Test attachment creation"""
        attachment = Attachment(
            type="image",
            url="https://example.com/image.png",
            name="image.png",
            size=1024,
        )
        assert attachment.type == "image"
        assert attachment.url == "https://example.com/image.png"
        assert attachment.size == 1024


class TestMessageExtra:
    """Tests for MessageExtra model"""

    def test_minimal_message_extra(self):
        """Test message extra with minimal fields"""
        user = User(id="123", username="testuser")
        extra = MessageExtra(
            type=1,
            guild_id="guild123",
            channel_name="test-channel",
            author=user,
        )
        assert extra.type == 1
        assert extra.guild_id == "guild123"
        assert extra.channel_name == "test-channel"
        assert extra.mention == []
        assert extra.mention_all is False

    def test_full_message_extra(self):
        """Test message extra with all fields"""
        user = User(id="123", username="testuser")
        quote = Quote(
            id="quote123",
            type=1,
            content="Quoted",
            create_at=123456,
            author=user,
        )
        extra = MessageExtra(
            type=9,
            guild_id="guild123",
            channel_name="test-channel",
            author=user,
            mention=["user456"],
            mention_all=True,
            mention_roles=[1, 2],
            mention_here=False,
            quote=quote,
        )
        assert extra.mention == ["user456"]
        assert extra.mention_all is True
        assert extra.mention_roles == [1, 2]
        assert extra.quote.id == "quote123"


class TestSystemEventExtra:
    """Tests for SystemEventExtra model"""

    def test_system_event_extra(self):
        """Test system event extra"""
        extra = SystemEventExtra(
            type="joined_guild",
            body={"user_id": "123", "joined_at": 1234567890},
        )
        assert extra.type == "joined_guild"
        assert extra.body["user_id"] == "123"
        assert extra.body["joined_at"] == 1234567890


class TestWebhookEvent:
    """Tests for WebhookEvent model"""

    def test_webhook_event(self):
        """Test webhook event"""
        event = WebhookEvent(
            channel_type="GROUP",
            type=1,
            target_id="target123",
            author_id="author123",
            content="Hello",
            msg_id="msg123",
            msg_timestamp=1234567890,
            nonce="nonce123",
            extra={},
        )
        assert event.channel_type == "GROUP"
        assert event.type == 1
        assert event.content == "Hello"
        assert event.msg_id == "msg123"


class TestWebhookChallenge:
    """Tests for WebhookChallenge model"""

    def test_webhook_challenge(self):
        """Test webhook challenge"""
        challenge = WebhookChallenge(
            type=255,
            challenge="challenge_token",
            verify_token="verify_token",
        )
        assert challenge.channel_type == "WEBHOOK_CHALLENGE"
        assert challenge.challenge == "challenge_token"
        assert challenge.verify_token == "verify_token"


class TestWebhookData:
    """Tests for WebhookData model"""

    def test_webhook_data_message(self):
        """Test webhook data for message"""
        data = WebhookData(
            channel_type="GROUP",
            type=1,
            target_id="target123",
            author_id="author123",
            content="Hello",
            msg_id="msg123",
            msg_timestamp=1234567890,
        )
        assert data.channel_type == "GROUP"
        assert data.type == 1
        assert data.content == "Hello"

    def test_webhook_data_challenge(self):
        """Test webhook data for challenge"""
        data = WebhookData(
            channel_type="WEBHOOK_CHALLENGE",
            type=255,
            challenge="challenge_token",
            verify_token="verify_token",
        )
        assert data.channel_type == "WEBHOOK_CHALLENGE"
        assert data.challenge == "challenge_token"


class TestWebhookMessage:
    """Tests for WebhookMessage model"""

    def test_webhook_message(self):
        """Test webhook message"""
        data = WebhookData(
            channel_type="GROUP",
            type=1,
            target_id="target123",
            author_id="author123",
            content="Hello",
            msg_id="msg123",
            msg_timestamp=1234567890,
        )
        message = WebhookMessage(s=0, d=data)
        assert message.s == 0
        assert message.d.channel_type == "GROUP"
        assert message.d.content == "Hello"

    def test_webhook_message_from_dict(self):
        """Test webhook message from dict"""
        message_dict = {
            "s": 0,
            "d": {
                "channel_type": "GROUP",
                "type": 1,
                "target_id": "target123",
                "author_id": "author123",
                "content": "Hello",
                "msg_id": "msg123",
                "msg_timestamp": 1234567890,
            },
        }
        message = WebhookMessage(**message_dict)
        assert message.s == 0
        assert message.d.content == "Hello"


class TestWebhookEncryptedMessage:
    """Tests for WebhookEncryptedMessage model"""

    def test_encrypted_message(self):
        """Test encrypted message"""
        message = WebhookEncryptedMessage(encrypt="encrypted_data_here")
        assert message.encrypt == "encrypted_data_here"
