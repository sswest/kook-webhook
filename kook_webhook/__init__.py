"""
KOOK Webhook SDK

A Python SDK for receiving and handling KOOK webhook messages
"""

from .app import Config, WebhookApp
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
from .models import *
from .sdk import KookClient

__version__ = "0.1.0"
__all__ = [
    "WebhookApp",
    "Config",
    "EventManager",
    "EventPriority",
    "Context",
    "ContextDataT",
    # Type aliases for handler callbacks
    "RawHandler",
    "MessageHandler",
    "CommandHandler",
    "SystemHandler",
    "ErrorHandler",
    "PostHandler",
    # SDK Client
    "KookClient",
    "APIError",
    # SDK Request Models
    "MessageCreateRequest",
    "MessageUpdateRequest",
    "MessageDeleteRequest",
    "MessageReactionRequest",
    "MessageDeleteReactionRequest",
    "MessagePinRequest",
    "DirectMessageCreateRequest",
    "DirectMessageUpdateRequest",
    "DirectMessageDeleteRequest",
    "DirectMessageReactionRequest",
    "DirectMessageDeleteReactionRequest",
    "UserChatCreateRequest",
    "UserChatDeleteRequest",
    "ChannelCreateRequest",
    "ChannelUpdateRequest",
    "ChannelDeleteRequest",
    "ChannelMoveUserRequest",
    "ChannelKickoutRequest",
    "ChannelRolePermissionRequest",
    "GuildNicknameRequest",
    "GuildLeaveRequest",
    "GuildKickoutRequest",
    "GuildMuteRequest",
    # SDK Response Models
    "MessageCreateResponse",
    "MessageListResponse",
    "MessageViewResponse",
    "UserChatListResponse",
    "UserChatViewResponse",
    "ChannelUserResponse",
    "ReactionUserWithTagInfo",
    "ChannelListResponse",
    "ChannelDetailResponse",
    "ChannelRolePermissionResponse",
    "ChannelRolePermissionResult",
    "GuildListResponse",
    "GuildDetailResponse",
    "GuildUserListResponse",
    "GuildMuteListResponse",
    "GuildBoostHistoryResponse",
    # Webhook Models
    "User",
    "Role",
    "Channel",
    "Guild",
    "Quote",
    "Attachment",
    "MessageType",
    "ChannelType",
    "MessageExtra",
    "SystemEventExtra",
    "WebhookEvent",
    "WebhookChallenge",
    "WebhookData",
    "WebhookMessage",
    "WebhookEncryptedMessage",
]
