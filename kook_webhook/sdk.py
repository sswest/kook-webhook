"""
KOOK API Client

Async client for interacting with KOOK API
"""

from typing import Any, Literal, Optional

import httpx

from .models import (
    APIError,
    ChannelCreateRequest,
    ChannelDeleteRequest,
    ChannelDetailResponse,
    ChannelKickoutRequest,
    ChannelListResponse,
    ChannelMoveUserRequest,
    ChannelRolePermissionRequest,
    ChannelRolePermissionResponse,
    ChannelRolePermissionResult,
    ChannelUpdateRequest,
    ChannelUserResponse,
    DirectMessageCreateRequest,
    DirectMessageDeleteReactionRequest,
    DirectMessageDeleteRequest,
    DirectMessageReactionRequest,
    DirectMessageUpdateRequest,
    GuildBoostHistoryResponse,
    GuildDetailResponse,
    GuildKickoutRequest,
    GuildLeaveRequest,
    GuildListResponse,
    GuildMuteListResponse,
    GuildMuteRequest,
    GuildNicknameRequest,
    GuildUserListResponse,
    MessageCreateRequest,
    MessageCreateResponse,
    MessageDeleteReactionRequest,
    MessageDeleteRequest,
    MessageListResponse,
    MessagePinRequest,
    MessageReactionRequest,
    MessageUpdateRequest,
    MessageViewResponse,
    ReactionUserWithTagInfo,
    User,
    UserChatCreateRequest,
    UserChatDeleteRequest,
    UserChatListResponse,
    UserChatViewResponse,
)


class KookClient:
    """KOOK API Client

    Async-only client for interacting with KOOK API.

    Example:
        >>> client = KookClient(token="your_bot_token")
        >>> await client.send_message(target_id="123", content="Hello!")
        >>> await client.send_direct_message(target_id="456", content="DM!")
    """

    BASE_URL = "https://www.kookapp.cn/api/v3"

    def __init__(self, token: str, timeout: float = 30.0):
        """Initialize client

        :param token: Bot token
        :param timeout: Request timeout in seconds
        """
        self.token = token
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        self.bot_user_id: Optional[str] = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create async client"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self) -> None:
        """Close the client"""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    def _build_request(
        self,
        method: str,
        path: str,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
    ) -> httpx.Request:
        url = f"{self.BASE_URL}{path}"
        headers = {"Authorization": f"Bot {self.token}"}
        return self.client.build_request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=data,
        )

    def _request_sync(
        self,
        method: str,
        path: str,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
    ) -> dict[str, Any]:
        request = self._build_request(method, path, params=params, data=data)
        with httpx.Client(timeout=self.timeout) as client:
            response = client.send(request)
            result = response.json()
            if result.get("code") != 0:
                raise APIError(
                    code=result.get("code", -1),
                    message=result.get("message", "Unknown error"),
                )
            return result.get("data", {})

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Internal request method

        :param method: HTTP method (GET, POST)
        :param path: API path
        :param params: Query parameters
        :param data: POST data
        :return: Response data
        :raises APIError: If API returns error
        """
        request = self._build_request(method, path, params=params, data=data)
        response = await self.client.send(request)
        result = response.json()

        if result.get("code") != 0:
            raise APIError(
                code=result.get("code", -1),
                message=result.get("message", "Unknown error"),
            )

        return result.get("data", {})

    async def message_list(
        self,
        target_id: str,
        msg_id: Optional[str] = None,
        pin: Optional[int] = None,
        flag: Optional[Literal["before", "around", "after"]] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> MessageListResponse:
        """Get channel message list

        :param target_id: Channel ID
        :param msg_id: Reference message ID
        :param pin: 0 or 1, whether to query pinned messages
        :param flag: Query mode (before/around/after)
        :param page: Page number
        :param page_size: Number of messages per page
        :return: Message list response
        """
        params = {"target_id": target_id, "page_size": page_size, "page": page}
        if msg_id:
            params["msg_id"] = msg_id
        if pin is not None:
            params["pin"] = pin
        if flag:
            params["flag"] = flag

        result = await self._request("GET", "/message/list", params=params)
        # Parse each message item
        items = [MessageViewResponse(**item) for item in result.get("items", [])]
        return MessageListResponse(items=items)

    async def message_view(self, msg_id: str) -> MessageViewResponse:
        """Get message detail

        :param msg_id: Message ID
        :return: Message detail
        """
        result = await self._request("GET", "/message/view", params={"msg_id": msg_id})
        return MessageViewResponse(**result)

    async def message_create(self, request: MessageCreateRequest) -> MessageCreateResponse:
        """Create channel message

        :param request: Message create request
        :return: Created message info
        """
        data = request.model_dump(exclude_none=True)
        result = await self._request("POST", "/message/create", data=data)
        return MessageCreateResponse(**result)

    async def message_update(self, request: MessageUpdateRequest) -> None:
        """Update channel message

        :param request: Message update request
        """
        data = request.model_dump(exclude_none=True)
        await self._request("POST", "/message/update", data=data)

    async def message_delete(self, request: MessageDeleteRequest) -> None:
        """Delete channel message

        :param request: Message delete request
        """
        data = request.model_dump(exclude_none=True)
        await self._request("POST", "/message/delete", data=data)

    async def message_reaction_list(self, msg_id: str, emoji: str) -> list[ReactionUserWithTagInfo]:
        """Get reaction user list

        :param msg_id: Message ID
        :param emoji: Emoji ID
        :return: User list
        """
        import urllib.parse

        params = {"msg_id": msg_id, "emoji": urllib.parse.quote(emoji)}
        result = await self._request("GET", "/message/reaction-list", params=params)

        # Result can be a list of users or a single user
        if isinstance(result, list):
            return [ReactionUserWithTagInfo(**user) for user in result]
        return [ReactionUserWithTagInfo(**result)]

    async def message_add_reaction(self, request: MessageReactionRequest) -> None:
        """Add reaction to message

        :param request: Reaction request
        """
        data = request.model_dump(exclude_none=True)
        await self._request("POST", "/message/add-reaction", data=data)

    async def message_delete_reaction(self, request: MessageDeleteReactionRequest) -> None:
        """Delete reaction from message

        :param request: Delete reaction request
        """
        data = request.model_dump(exclude_none=True)
        await self._request("POST", "/message/delete-reaction", data=data)

    async def message_pin(self, request: MessagePinRequest) -> None:
        """Pin message

        :param request: Pin request
        """
        data = request.model_dump(exclude_none=True)
        await self._request("POST", "/message/pin", data=data)

    async def message_unpin(self, request: MessagePinRequest) -> None:
        """Unpin message

        :param request: Pin request (msg_id and target_id)
        """
        data = request.model_dump(exclude_none=True)
        await self._request("POST", "/message/unpin", data=data)

    async def direct_message_list(
        self,
        chat_code: Optional[str] = None,
        target_id: Optional[str] = None,
        msg_id: Optional[str] = None,
        flag: Optional[Literal["before", "around", "after"]] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> MessageListResponse:
        """Get direct message list

        :param chat_code: Chat code
        :param target_id: Target user ID
        :param msg_id: Reference message ID
        :param flag: Query mode (before/around/after)
        :param page: Page number
        :param page_size: Number of messages per page
        :return: Message list response
        """
        params: dict[str, Any] = {"page_size": page_size, "page": page}
        if chat_code:
            params["chat_code"] = chat_code
        if target_id:
            params["target_id"] = target_id
        if msg_id:
            params["msg_id"] = msg_id
        if flag:
            params["flag"] = flag

        result = await self._request("GET", "/direct-message/list", params=params)
        items = [MessageViewResponse(**item) for item in result.get("items", [])]
        return MessageListResponse(items=items)

    async def direct_message_view(self, chat_code: str, msg_id: str) -> MessageViewResponse:
        """Get direct message detail

        :param chat_code: Chat code
        :param msg_id: Message ID
        :return: Message detail
        """
        result = await self._request(
            "GET",
            "/direct-message/view",
            params={"chat_code": chat_code, "msg_id": msg_id},
        )
        return MessageViewResponse(**result)

    async def direct_message_create(
        self, request: DirectMessageCreateRequest
    ) -> MessageCreateResponse:
        """Create direct message

        :param request: Direct message create request
        :return: Created message info
        """
        data = request.model_dump(exclude_none=True)
        result = await self._request("POST", "/direct-message/create", data=data)
        return MessageCreateResponse(**result)

    async def direct_message_update(self, request: DirectMessageUpdateRequest) -> None:
        """Update direct message

        :param request: Direct message update request
        """
        data = request.model_dump(exclude_none=True)
        await self._request("POST", "/direct-message/update", data=data)

    async def direct_message_delete(self, request: DirectMessageDeleteRequest) -> None:
        """Delete direct message

        :param request: Direct message delete request
        """
        data = request.model_dump(exclude_none=True)
        await self._request("POST", "/direct-message/delete", data=data)

    async def direct_message_reaction_list(
        self,
        msg_id: str,
        emoji: str,
    ) -> list[ReactionUserWithTagInfo]:
        """Get direct message reaction user list

        :param msg_id: Message ID
        :param emoji: Emoji ID
        :return: User list
        """
        import urllib.parse

        params = {"msg_id": msg_id, "emoji": urllib.parse.quote(emoji)}
        result = await self._request("GET", "/direct-message/reaction-list", params=params)

        if isinstance(result, list):
            return [ReactionUserWithTagInfo(**user) for user in result]
        return [ReactionUserWithTagInfo(**result)]

    async def direct_message_add_reaction(self, request: DirectMessageReactionRequest) -> None:
        """Add reaction to direct message

        :param request: Reaction request
        """
        data = request.model_dump(exclude_none=True)
        await self._request("POST", "/direct-message/add-reaction", data=data)

    async def direct_message_delete_reaction(
        self, request: DirectMessageDeleteReactionRequest
    ) -> None:
        """Delete reaction from direct message

        :param request: Delete reaction request
        """
        data = request.model_dump(exclude_none=True)
        await self._request("POST", "/direct-message/delete-reaction", data=data)

    async def user_chat_list(self, page: int = 1, page_size: int = 50) -> UserChatListResponse:
        """Get user chat list

        :param page: Page number
        :param page_size: Page size
        :return: Chat list with meta
        """
        params = {"page": page, "page_size": page_size}
        result = await self._request("GET", "/user-chat/list", params=params)
        return UserChatListResponse(**result)

    async def user_chat_view(self, chat_code: str) -> UserChatViewResponse:
        """Get user chat detail

        :param chat_code: Chat code
        :return: Chat detail
        """
        result = await self._request("GET", "/user-chat/view", params={"chat_code": chat_code})
        return UserChatViewResponse(**result)

    async def user_chat_create(self, request: UserChatCreateRequest) -> UserChatViewResponse:
        """Create user chat

        :param request: Create chat request
        :return: Created chat info
        """
        data = request.model_dump(exclude_none=True)
        result = await self._request("POST", "/user-chat/create", data=data)
        return UserChatViewResponse(**result)

    async def user_chat_delete(self, request: UserChatDeleteRequest) -> None:
        """Delete user chat

        :param request: Delete chat request
        """
        data = request.model_dump(exclude_none=True)
        await self._request("POST", "/user-chat/delete", data=data)

    async def channel_user_get_joined(
        self,
        guild_id: str,
        user_id: str,
        page: int = 1,
        page_size: int = 50,
    ) -> ChannelUserResponse:
        """Get user's joined voice channel

        :param guild_id: Guild ID
        :param user_id: User ID
        :param page: Page number
        :param page_size: Page size
        :return: Channel list with meta
        """
        params = {"guild_id": guild_id, "user_id": user_id, "page": page, "page_size": page_size}
        result = await self._request("GET", "/channel-user/get-joined-channel", params=params)
        return ChannelUserResponse(**result)

    async def guild_list(
        self,
        page: int = 1,
        page_size: int = 50,
        sort: Optional[str] = None,
    ) -> GuildListResponse:
        """Get guild list

        :param page: Page number
        :param page_size: Page size
        :param sort: Sort field
        :return: Guild list with meta
        """
        params: dict[str, Any] = {"page": page, "page_size": page_size}
        if sort:
            params["sort"] = sort

        result = await self._request("GET", "/guild/list", params=params)
        return GuildListResponse(**result)

    async def guild_view(self, guild_id: str) -> GuildDetailResponse:
        """Get guild detail

        :param guild_id: Guild ID
        :return: Guild detail
        """
        result = await self._request("GET", "/guild/view", params={"guild_id": guild_id})
        return GuildDetailResponse(**result)

    async def guild_user_list(
        self,
        guild_id: str,
        channel_id: Optional[str] = None,
        search: Optional[str] = None,
        role_id: Optional[int] = None,
        mobile_verified: Optional[int] = None,
        active_time: Optional[int] = None,
        joined_at: Optional[int] = None,
        page: int = 1,
        page_size: int = 50,
        filter_user_id: Optional[str] = None,
    ) -> GuildUserListResponse:
        """Get guild user list

        :param guild_id: Guild ID
        :param channel_id: Channel ID
        :param search: Search keyword
        :param role_id: Role ID
        :param mobile_verified: Mobile verified (0 or 1)
        :param active_time: Active time sort (0 asc, 1 desc)
        :param joined_at: Joined time sort (0 asc, 1 desc)
        :param page: Page number
        :param page_size: Page size
        :param filter_user_id: Filter by user ID
        :return: User list with meta
        """
        params = {"guild_id": guild_id, "page": page, "page_size": page_size}
        if channel_id:
            params["channel_id"] = channel_id
        if search:
            params["search"] = search
        if role_id:
            params["role_id"] = role_id
        if mobile_verified is not None:
            params["mobile_verified"] = mobile_verified
        if active_time is not None:
            params["active_time"] = active_time
        if joined_at is not None:
            params["joined_at"] = joined_at
        if filter_user_id:
            params["filter_user_id"] = filter_user_id

        result = await self._request("GET", "/guild/user-list", params=params)
        return GuildUserListResponse(**result)

    async def guild_nickname(self, request: GuildNicknameRequest) -> None:
        """Modify user nickname in guild

        :param request: Nickname request
        """
        data = request.model_dump(exclude_none=True)
        await self._request("POST", "/guild/nickname", data=data)

    async def guild_leave(self, request: GuildLeaveRequest) -> None:
        """Leave guild

        :param request: Leave request
        """
        data = request.model_dump(exclude_none=True)
        await self._request("POST", "/guild/leave", data=data)

    async def guild_kickout(self, request: GuildKickoutRequest) -> None:
        """Kick user from guild

        :param request: Kickout request
        """
        data = request.model_dump(exclude_none=True)
        await self._request("POST", "/guild/kickout", data=data)

    async def guild_mute_list(
        self,
        guild_id: str,
        return_type: str = "detail",
    ) -> GuildMuteListResponse:
        """Get guild mute list

        :param guild_id: Guild ID
        :param return_type: Return type, default "detail"
        :return: Mute list
        """
        params = {"guild_id": guild_id, "return_type": return_type}
        result = await self._request("GET", "/guild-mute/list", params=params)
        return GuildMuteListResponse(**result)

    async def guild_mute_create(self, request: GuildMuteRequest) -> None:
        """Add guild mute

        :param request: Mute request
        """
        data = request.model_dump(exclude_none=True)
        await self._request("POST", "/guild-mute/create", data=data)

    async def guild_mute_delete(self, request: GuildMuteRequest) -> None:
        """Delete guild mute

        :param request: Mute request
        """
        data = request.model_dump(exclude_none=True)
        await self._request("POST", "/guild-mute/delete", data=data)

    async def guild_boost_history(
        self,
        guild_id: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> GuildBoostHistoryResponse:
        """Get guild boost history

        :param guild_id: Guild ID
        :param start_time: Start time (unix timestamp)
        :param end_time: End time (unix timestamp)
        :return: Boost history
        """
        params: dict[str, Any] = {"guild_id": guild_id}
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time

        result = await self._request("GET", "/guild-boost/history", params=params)
        return GuildBoostHistoryResponse(**result)

    async def channel_list(
        self,
        guild_id: str,
        page: int = 1,
        page_size: int = 50,
        type: Optional[int] = None,
        parent_id: Optional[str] = None,
    ) -> ChannelListResponse:
        """Get channel list

        :param guild_id: Guild ID
        :param page: Page number
        :param page_size: Page size
        :param type: Channel type (1 text, 2 voice)
        :param parent_id: Parent category ID
        :return: Channel list with meta
        """
        params = {"guild_id": guild_id, "page": page, "page_size": page_size}
        if type:
            params["type"] = type
        if parent_id:
            params["parent_id"] = parent_id

        result = await self._request("GET", "/channel/list", params=params)
        return ChannelListResponse(**result)

    async def channel_view(
        self,
        target_id: str,
        need_children: bool = False,
    ) -> ChannelDetailResponse:
        """Get channel detail

        :param target_id: Channel ID
        :param need_children: Whether to get children channels
        :return: Channel detail
        """
        params = {"target_id": target_id, "need_children": need_children}
        result = await self._request("GET", "/channel/view", params=params)
        return ChannelDetailResponse(**result)

    async def channel_create(self, request: ChannelCreateRequest) -> ChannelDetailResponse:
        """Create channel

        :param request: Create request
        :return: Created channel detail
        """
        data = request.model_dump(exclude_none=True)
        result = await self._request("POST", "/channel/create", data=data)
        return ChannelDetailResponse(**result)

    async def channel_update(self, request: ChannelUpdateRequest) -> None:
        """Update channel

        :param request: Update request
        """
        data = request.model_dump(exclude_none=True)
        await self._request("POST", "/channel/update", data=data)

    async def channel_delete(self, request: ChannelDeleteRequest) -> None:
        """Delete channel

        :param request: Delete request
        """
        data = request.model_dump(exclude_none=True)
        await self._request("POST", "/channel/delete", data=data)

    async def channel_user_list(self, channel_id: str) -> list[Any]:
        """Get voice channel user list

        :param channel_id: Channel ID
        :return: User list
        """
        result = await self._request("GET", "/channel/user-list", params={"channel_id": channel_id})
        return result if isinstance(result, list) else [result]

    async def channel_move_user(self, request: ChannelMoveUserRequest) -> None:
        """Move user between voice channels

        :param request: Move user request
        """
        data = request.model_dump(exclude_none=True)
        await self._request("POST", "/channel/move-user", data=data)

    async def channel_kickout(self, request: ChannelKickoutRequest) -> None:
        """Kick user from voice channel

        :param request: Kickout request
        """
        data = request.model_dump(exclude_none=True)
        await self._request("POST", "/channel/kickout", data=data)

    async def channel_role_index(self, channel_id: str) -> ChannelRolePermissionResponse:
        """Get channel role permission index

        :param channel_id: Channel ID
        :return: Role permission response
        """
        result = await self._request(
            "GET", "/channel-role/index", params={"channel_id": channel_id}
        )
        return ChannelRolePermissionResponse(**result)

    async def channel_role_create(
        self,
        request: ChannelRolePermissionRequest,
    ) -> ChannelRolePermissionResult:
        """Create channel role permission

        :param request: Permission request
        :return: Permission result
        """
        data = request.model_dump(exclude_none=True)
        result = await self._request("POST", "/channel-role/create", data=data)
        return ChannelRolePermissionResult(**result)

    async def channel_role_update(
        self,
        request: ChannelRolePermissionRequest,
    ) -> ChannelRolePermissionResult:
        """Update channel role permission

        :param request: Permission request
        :return: Permission result
        """
        data = request.model_dump(exclude_none=True)
        result = await self._request("POST", "/channel-role/update", data=data)
        return ChannelRolePermissionResult(**result)

    async def channel_role_sync(self, channel_id: str) -> ChannelRolePermissionResponse:
        """Sync channel role permissions

        :param channel_id: Channel ID
        :return: Role permission response
        """
        data = {"channel_id": channel_id}
        result = await self._request("POST", "/channel-role/sync", data=data)
        return ChannelRolePermissionResponse(**result)

    async def channel_role_delete(self, request: ChannelRolePermissionRequest) -> None:
        """Delete channel role permission

        :param request: Permission request
        """
        data = request.model_dump(exclude_none=True)
        await self._request("POST", "/channel-role/delete", data=data)

    async def send_message(self, target_id: str, content: str, **kwargs) -> MessageCreateResponse:
        """Convenience method to send channel message

        :param target_id: Channel ID
        :param content: Message content
        :param kwargs: Additional parameters (type, quote, nonce, etc.)
        :return: Created message info
        """
        request = MessageCreateRequest(target_id=target_id, content=content, **kwargs)
        return await self.message_create(request)

    async def send_direct_message(
        self,
        target_id: str,
        content: str,
        **kwargs,
    ) -> MessageCreateResponse:
        """Convenience method to send direct message

        :param target_id: User ID
        :param content: Message content
        :param kwargs: Additional parameters (type, quote, nonce, etc.)
        :return: Created message info
        """
        request = DirectMessageCreateRequest(target_id=target_id, content=content, **kwargs)
        return await self.direct_message_create(request)

    async def get_me(self) -> User:
        result = await self._request("GET", "/user/me")
        return User(**result)

    def get_me_sync(self) -> User:
        result = self._request_sync("GET", "/user/me")
        return User(**result)
