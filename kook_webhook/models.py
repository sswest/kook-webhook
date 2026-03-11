from typing import Any, Optional

from pydantic import BaseModel, Field


class User(BaseModel):
    """User object"""

    id: str
    username: str
    nickname: Optional[str] = None
    identify_num: Optional[str] = None
    online: Optional[bool] = None
    bot: Optional[bool] = None
    status: Optional[int] = None
    avatar: Optional[str] = None
    vip_avatar: Optional[str] = None
    banner: Optional[str] = None
    mobile_verified: Optional[bool] = None
    roles: Optional[list[int]] = Field(default_factory=list)
    is_vip: Optional[bool] = None
    vip_amp: Optional[bool] = None
    nameplate: Optional[list[Any]] = Field(default_factory=list)
    kpm_vip: Optional[Any] = None
    wealth_level: Optional[int] = None
    decorations_id_map: Optional[Any] = None
    is_sys: Optional[bool] = None
    os: Optional[str] = None
    joined_at: Optional[int] = None
    active_time: Optional[int] = None


class Role(BaseModel):
    """Role object"""

    role_id: int
    name: str
    color: int
    position: int
    hoist: int
    mentionable: int
    permissions: int


class PermissionOverwrite(BaseModel):
    """Permission overwrite"""

    role_id: int
    allow: int
    deny: int


class PermissionUser(BaseModel):
    """User permission overwrite"""

    user: User
    allow: int
    deny: int


class Channel(BaseModel):
    """Channel object"""

    id: str
    name: str
    user_id: str
    guild_id: str
    topic: str
    is_category: bool
    parent_id: str
    level: int
    slow_mode: int
    type: int
    permission_overwrites: list[PermissionOverwrite] = Field(default_factory=list)
    permission_users: list[PermissionUser] = Field(default_factory=list)
    permission_sync: int
    has_password: bool


class Guild(BaseModel):
    """Guild object"""

    id: str
    name: str
    topic: str
    user_id: str
    icon: str
    notify_type: int
    region: str
    enable_open: bool
    open_id: str
    default_channel_id: str
    welcome_channel_id: str
    roles: list[Role] = Field(default_factory=list)
    channels: list[Channel] = Field(default_factory=list)


class Quote(BaseModel):
    """Quote message object"""

    id: str
    type: int
    content: str
    create_at: int
    author: User


class Attachment(BaseModel):
    """Attachment object"""

    type: str
    url: str
    name: str
    size: int
    file_type: Optional[str] = None
    duration: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None


class TargetInfo(BaseModel):
    """Target user info"""

    id: str
    username: str
    online: bool
    avatar: str


class MessageType:
    TEXT = 1  # Text message
    IMAGE = 2  # Image message
    VIDEO = 3  # Video message
    FILE = 4  # File message
    AUDIO = 8  # Audio message
    KMARKDOWN = 9  # KMarkdown
    CARD = 10  # Card message
    SYSTEM = 255  # System message


class ChannelType:
    GROUP = "GROUP"  # Group message
    PERSON = "PERSON"  # Direct message
    BROADCAST = "BROADCAST"  # Broadcast message


class MessageExtra(BaseModel):
    """Text channel message Extra (non-system messages)"""

    type: int
    code: Optional[str] = None
    guild_id: str
    guild_type: Optional[int] = None
    channel_name: str
    visible_only: Optional[str] = None
    mention: list[str] = Field(default_factory=list)
    mention_no_at: list[str] = Field(default_factory=list)
    mention_all: bool = False
    mention_roles: list[int] = Field(default_factory=list)
    mention_here: bool = False
    nav_channels: Optional[list[Any]] = Field(default_factory=list)
    author: User
    quote: Optional[Quote] = None
    attachments: Optional[list[Attachment]] = None
    kmarkdown: Optional[dict[str, Any]] = None
    emoji: Optional[list[Any]] = Field(default_factory=list)
    preview_content: Optional[str] = None
    channel_type: Optional[int] = None
    last_msg_content: Optional[str] = None
    send_msg_device: Optional[int] = None


class SystemEventExtra(BaseModel):
    """System event message Extra (type=255)"""

    type: str
    body: dict[str, Any] = Field(default_factory=dict)


class WebhookEvent(BaseModel):
    """Webhook event data"""

    channel_type: str
    type: int
    target_id: str
    author_id: str
    content: str
    msg_id: str
    msg_timestamp: int
    nonce: Optional[str] = None
    extra: dict[str, Any] = Field(default_factory=dict)


class WebhookChallenge(BaseModel):
    """Webhook Challenge verification request"""

    type: int
    channel_type: str = "WEBHOOK_CHALLENGE"
    challenge: str
    verify_token: str


class WebhookData(BaseModel):
    """Webhook message data d field"""

    channel_type: str
    type: int
    challenge: Optional[str] = None
    verify_token: Optional[str] = None
    target_id: Optional[str] = None
    author_id: Optional[str] = None
    content: Optional[str] = None
    msg_id: Optional[str] = None
    msg_timestamp: Optional[int] = None
    nonce: Optional[str] = None
    extra: Optional[Any] = None


class WebhookMessage(BaseModel):
    """Webhook message"""

    s: int
    d: WebhookData
    t: Optional[str] = None  # event type (e.g., "message")
    verify_token: Optional[str] = None


class WebhookEncryptedMessage(BaseModel):
    """Encrypted webhook message"""

    encrypt: str


class PaginationMeta(BaseModel):
    """Pagination metadata"""

    page: int
    page_total: int
    page_size: int
    total: int


class APIError(Exception):
    """KOOK API Error"""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


class GuildRole(BaseModel):
    """Guild role"""

    role_id: int
    name: str
    color: int
    position: int
    hoist: int
    mentionable: int
    permissions: int


class GuildInfo(BaseModel):
    """Guild info"""

    id: str
    name: str
    topic: str
    master_id: str
    is_master: bool
    user_id: str
    icon: str
    notify_type: int
    region: str
    enable_open: bool
    open_id: str
    default_channel_id: str
    welcome_channel_id: str
    boost_num: int = 0
    level: int = 0


class GuildDetailResponse(GuildInfo):
    """Guild detail response"""

    roles: list[GuildRole] = Field(default_factory=list)
    channels: list[Channel] = Field(default_factory=list)


class GuildlistResponse(BaseModel):
    """Guild list response"""

    items: list[GuildInfo]
    meta: PaginationMeta
    sort: Optional[dict[str, int]] = None


class ChannelInfo(BaseModel):
    """Channel info"""

    id: str
    guild_id: Optional[str] = None
    user_id: str
    parent_id: str
    name: str
    topic: str
    type: int
    level: int
    slow_mode: int
    limit_amount: int
    is_category: bool


class ChannelDetailResponse(ChannelInfo):
    """Channel detail response"""

    has_password: bool = False
    permission_sync: int = 0
    permission_overwrites: list[PermissionOverwrite] = Field(default_factory=list)
    permission_users: list[PermissionUser] = Field(default_factory=list)
    voice_quality: Optional[str] = None
    server_url: Optional[str] = None
    children: list[str] = Field(default_factory=list)


class ChannellistResponse(BaseModel):
    """Channel list response"""

    items: list[ChannelInfo]
    meta: PaginationMeta


class GuildUserlistResponse(BaseModel):
    """Guild user list response"""

    items: list[User]
    meta: PaginationMeta
    sort: Optional[dict[str, int]] = None
    user_count: int
    online_count: int
    offline_count: int


class MessageCreateRequest(BaseModel):
    """Request model for creating message"""

    type: Optional[int] = Field(9, description="Message type, default 9 (KMarkdown)")
    target_id: str = Field(..., description="Target channel ID")
    content: str = Field(..., description="Message content")
    quote: Optional[str] = Field(None, description="Message ID to reply")
    nonce: Optional[str] = Field(None, description="Random string")
    temp_target_id: Optional[str] = Field(None, description="User ID for temporary message")
    template_id: Optional[str] = Field(None, description="Template message ID")
    reply_msg_id: Optional[str] = Field(None, description="Message ID to reply (within 5 minutes)")


class MessageCreateResponse(BaseModel):
    """Response for creating message"""

    msg_id: str
    msg_timestamp: int
    nonce: Optional[str] = None


class Embed(BaseModel):
    """Embed object"""

    type: str
    url: str


class Emoji(BaseModel):
    """Emoji object"""

    id: str
    name: str


class TagInfo(BaseModel):
    """Tag info"""

    color: str
    text: str


class ReactionUserInfo(BaseModel):
    """Reaction user info"""

    id: str
    username: str
    nickname: Optional[str] = None
    identify_num: Optional[str] = None
    online: bool
    status: int
    avatar: str
    bot: bool
    reaction_time: int


class ReactionUserWithTagInfo(ReactionUserInfo):
    """Reaction user with tag info"""

    tag_info: Optional[TagInfo] = None


class ReactionInfo(BaseModel):
    """Reaction info"""

    emoji: Emoji
    count: int
    me: bool


class MessageAuthor(BaseModel):
    """Message author"""

    id: str
    username: str
    nickname: Optional[str] = None
    identify_num: Optional[str] = None
    online: Optional[bool] = None
    avatar: Optional[str] = None
    bot: Optional[bool] = None
    status: Optional[int] = None
    is_vip: Optional[bool] = None


class MessageViewResponse(BaseModel):
    """Response for viewing message detail"""

    id: str
    type: int
    content: str
    mention: list[str] = Field(default_factory=list)
    mention_all: bool = False
    mention_roles: list[int] = Field(default_factory=list)
    mention_here: bool = False
    embeds: list[Embed] = Field(default_factory=list)
    attachments: Optional[Attachment] = None
    create_at: int
    updated_at: int
    reactions: list[ReactionInfo] = Field(default_factory=list)
    author: MessageAuthor
    quote: Optional[dict[str, Any]] = None
    mention_info: Optional[dict[str, Any]] = None
    read_status: bool = False
    image_name: str = ""


class MessageListResponse(BaseModel):
    """Response for message list"""

    items: list[MessageViewResponse]


class UserChatInfo(BaseModel):
    """User chat info"""

    code: str
    last_read_time: int
    latest_msg_time: int
    unread_count: int
    is_friend: Optional[bool] = None
    is_blocked: Optional[bool] = None
    is_target_blocked: Optional[bool] = None
    target_info: TargetInfo


class UserChatListResponse(BaseModel):
    """Response for user chat list"""

    items: list[UserChatInfo]
    meta: PaginationMeta
    sort: Optional[dict[str, int]] = None


class UserChatViewResponse(UserChatInfo):
    """Response for viewing user chat detail"""

    pass


class ChannelUserInfo(BaseModel):
    """Channel user info"""

    id: str
    guild_id: str
    user_id: str
    parent_id: str
    name: str
    topic: str
    type: int
    level: int
    slow_mode: int
    limit_amount: int
    is_category: bool
    permission_sync: int
    permission_overwrites: list[dict[str, int]]
    permission_users: list[Any]


class ChannelUserResponse(BaseModel):
    """Response for channel user"""

    items: list[ChannelUserInfo]
    meta: PaginationMeta


class GuildMuteRequest(BaseModel):
    """Request for guild mute"""

    guild_id: str
    user_id: str
    type: int  # 1 for mic, 2 for headset


class GuildBoostHistoryItem(BaseModel):
    """Guild boost history item"""

    user_id: str
    guild_id: str
    start_time: int
    end_time: int
    user: dict[str, Any]


class GuildBoostHistoryResponse(BaseModel):
    """Guild boost history response"""

    items: list[GuildBoostHistoryItem]
    meta: PaginationMeta


class GuildKickoutRequest(BaseModel):
    """Request for kicking user from guild"""

    guild_id: str
    target_id: str


class GuildMuteListResponse(BaseModel):
    """Guild mute list response"""

    mic: dict[str, Any]
    headset: dict[str, Any]


class ChannelListResponse(BaseModel):
    """Channel list response"""

    items: list[ChannelInfo]
    meta: PaginationMeta


class ChannelCreateRequest(BaseModel):
    """Request for creating channel"""

    guild_id: str
    name: str
    parent_id: Optional[str] = None
    type: Optional[int] = None
    limit_amount: Optional[int] = None
    voice_quality: Optional[str] = None
    is_category: Optional[int] = None


class ChannelUpdateRequest(BaseModel):
    """Request for updating channel"""

    channel_id: str
    name: Optional[str] = None
    level: Optional[int] = None
    parent_id: Optional[str] = None
    topic: Optional[str] = None
    slow_mode: Optional[int] = None
    limit_amount: Optional[int] = None
    voice_quality: Optional[str] = None
    password: Optional[str] = None


class ChannelDeleteRequest(BaseModel):
    """Request for deleting channel"""

    channel_id: str


class ChannelMoveUserRequest(BaseModel):
    """Request for moving user to channel"""

    target_id: str
    user_ids: list[str]


class ChannelKickoutRequest(BaseModel):
    """Request for kicking user from channel"""

    channel_id: str
    user_id: str


class ChannelRolePermissionResponse(BaseModel):
    """Channel role permission response"""

    permission_overwrites: list[PermissionOverwrite]
    permission_users: list[PermissionUser]
    permission_sync: int


class ChannelRolePermissionRequest(BaseModel):
    """Request for channel role permission"""

    channel_id: str
    type: Optional[str] = None
    value: Optional[str] = None
    allow: Optional[int] = None
    deny: Optional[int] = None


class ChannelRolePermissionResult(BaseModel):
    """Channel role permission result"""

    user_id: Optional[str] = None
    role_id: Optional[int] = None
    allow: int
    deny: int


class GuildListResponse(BaseModel):
    """Guild list response"""

    items: list[GuildInfo]
    meta: PaginationMeta
    sort: Optional[dict[str, int]] = None


class GuildUserListResponse(BaseModel):
    """Guild user list response"""

    items: list[Any]
    meta: PaginationMeta
    sort: Optional[dict[str, int]] = None
    user_count: int
    online_count: int
    offline_count: int


class GuildNicknameRequest(BaseModel):
    """Request for guild nickname"""

    guild_id: str
    nickname: Optional[str] = None
    user_id: Optional[str] = None


class GuildLeaveRequest(BaseModel):
    """Request for leaving guild"""

    guild_id: str


class MessageUpdateRequest(BaseModel):
    """Request model for updating message"""

    msg_id: str = Field(..., description="Message ID")
    content: str = Field(..., description="New content")
    quote: Optional[str] = Field(None, description="Message ID to reply")
    temp_target_id: Optional[str] = Field(None, description="User ID for temporary message")
    template_id: Optional[str] = Field(None, description="Template message ID")
    reply_msg_id: Optional[str] = Field(None, description="Message ID to reply (within 5 minutes)")


class MessageDeleteRequest(BaseModel):
    """Request model for deleting message"""

    msg_id: str = Field(..., description="Message ID")


class MessageReactionRequest(BaseModel):
    """Request model for adding reaction"""

    msg_id: str = Field(..., description="Message ID")
    emoji: str = Field(..., description="Emoji ID")


class MessageDeleteReactionRequest(BaseModel):
    """Request model for deleting reaction"""

    msg_id: str = Field(..., description="Message ID")
    emoji: str = Field(..., description="Emoji ID")
    user_id: Optional[str] = Field(None, description="User ID")


class MessagePinRequest(BaseModel):
    """Request model for pinning message"""

    msg_id: str = Field(..., description="Message ID")
    target_id: str = Field(..., description="Channel ID")


class DirectMessageCreateRequest(BaseModel):
    """Request model for creating direct message"""

    type: Optional[int] = Field(1, description="Message type, default 1 (text)")
    target_id: Optional[str] = Field(None, description="Target user ID")
    chat_code: Optional[str] = Field(None, description="Chat code")
    content: str = Field(..., description="Message content")
    quote: Optional[str] = Field(None, description="Message ID to reply")
    nonce: Optional[str] = Field(None, description="Random string")
    template_id: Optional[str] = Field(None, description="Template message ID")
    reply_msg_id: Optional[str] = Field(None, description="Message ID to reply (within 5 minutes)")


class DirectMessageUpdateRequest(BaseModel):
    """Request model for updating direct message"""

    msg_id: str = Field(..., description="Message ID")
    content: str = Field(..., description="New content")
    quote: Optional[str] = Field(None, description="Message ID to reply")
    template_id: Optional[str] = Field(None, description="Template message ID")
    reply_msg_id: Optional[str] = Field(None, description="Message ID to reply (within 5 minutes)")


class DirectMessageDeleteRequest(BaseModel):
    """Request model for deleting direct message"""

    msg_id: str = Field(..., description="Message ID")


class DirectMessageCreateResponse(BaseModel):
    """Response for creating direct message"""

    msg_id: str
    msg_timestamp: int
    nonce: Optional[str] = None


class DirectMessageReactionRequest(BaseModel):
    """Request model for adding reaction to direct message"""

    msg_id: str = Field(..., description="Message ID")
    emoji: str = Field(..., description="Emoji ID")


class DirectMessageDeleteReactionRequest(BaseModel):
    """Request model for deleting reaction from direct message"""

    msg_id: str = Field(..., description="Message ID")
    emoji: str = Field(..., description="Emoji ID")
    user_id: Optional[str] = Field(None, description="User ID")


class UserChatCreateRequest(BaseModel):
    """Request model for creating user chat"""

    target_id: str = Field(..., description="Target user ID")


class UserChatDeleteRequest(BaseModel):
    """Request model for deleting user chat"""

    chat_code: str = Field(..., description="Chat code")
