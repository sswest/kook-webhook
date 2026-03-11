"""Tests for sdk module."""

from __future__ import annotations

from typing import Any

import pytest

import kook_webhook.sdk as sdk
from kook_webhook.models import APIError
from kook_webhook.sdk import KookClient


class DummyRequest:
    """Simple request object with model_dump compatibility."""

    def __init__(self, **data: Any):
        self._data = data

    def model_dump(self, exclude_none: bool = True) -> dict[str, Any]:
        if not exclude_none:
            return dict(self._data)
        return {k: v for k, v in self._data.items() if v is not None}


class EchoModel:
    """Model stub that accepts arbitrary keyword args."""

    def __init__(self, **kwargs: Any):
        self.data = kwargs


class FakeResponse:
    def __init__(self, payload: dict[str, Any]):
        self.payload = payload

    def json(self) -> dict[str, Any]:
        return self.payload


class FakeAsyncClient:
    def __init__(self, timeout: float):
        self.timeout = timeout
        self.closed = False
        self.last_request = None
        self.next_payload = {"code": 0, "data": {"ok": True}}

    def build_request(self, **kwargs: Any) -> dict[str, Any]:
        self.last_request = kwargs
        return kwargs

    async def send(self, request: Any) -> FakeResponse:
        self.last_request = request
        return FakeResponse(self.next_payload)

    async def aclose(self) -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_core_client_and_request_flows(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(sdk.httpx, "AsyncClient", FakeAsyncClient)

    client = KookClient(token="test-token", timeout=12.5)
    built = client._build_request("GET", "/health", params={"a": 1}, data={"b": 2})
    assert built["url"].endswith("/health")
    assert built["headers"]["Authorization"] == "Bot test-token"
    assert built["params"] == {"a": 1}
    assert built["json"] == {"b": 2}

    result = await client._request("GET", "/ok")
    assert result == {"ok": True}

    async_client = client.client
    async_client.next_payload = {"code": 4001, "message": "boom"}
    with pytest.raises(APIError):
        await client._request("GET", "/boom")

    await client.close()
    assert client._client is None

    class FakeSyncClient:
        def __init__(self, timeout: float):
            self.timeout = timeout

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def send(self, request: Any) -> FakeResponse:
            return FakeResponse({"code": 0, "data": {"id": "sync-user"}})

    monkeypatch.setattr(sdk.httpx, "Client", FakeSyncClient)
    sync_ok = client._request_sync("GET", "/user/me")
    assert sync_ok == {"id": "sync-user"}

    class FakeSyncClientError(FakeSyncClient):
        def send(self, request: Any) -> FakeResponse:
            return FakeResponse({"code": 9001, "message": "sync error"})

    monkeypatch.setattr(sdk.httpx, "Client", FakeSyncClientError)
    with pytest.raises(APIError):
        client._request_sync("GET", "/user/me")


@pytest.mark.asyncio
async def test_sdk_method_wrappers(monkeypatch: pytest.MonkeyPatch):
    response_model_names = [
        "MessageViewResponse",
        "MessageListResponse",
        "MessageCreateResponse",
        "ReactionUserWithTagInfo",
        "UserChatListResponse",
        "UserChatViewResponse",
        "ChannelUserResponse",
        "GuildListResponse",
        "GuildDetailResponse",
        "GuildUserListResponse",
        "GuildMuteListResponse",
        "GuildBoostHistoryResponse",
        "ChannelListResponse",
        "ChannelDetailResponse",
        "ChannelRolePermissionResponse",
        "ChannelRolePermissionResult",
        "User",
    ]
    for name in response_model_names:
        monkeypatch.setattr(sdk, name, EchoModel)

    monkeypatch.setattr(sdk, "MessageCreateRequest", DummyRequest)
    monkeypatch.setattr(sdk, "DirectMessageCreateRequest", DummyRequest)

    client = KookClient(token="token")
    calls: list[tuple[str, str, dict[str, Any] | None, dict[str, Any] | None]] = []
    channel_user_call_count = 0

    async def fake_request(
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> Any:
        nonlocal channel_user_call_count
        calls.append((method, path, params, data))
        if "reaction-list" in path:
            return [{"id": "u1"}, {"id": "u2"}]
        if path == "/channel/user-list":
            channel_user_call_count += 1
            if channel_user_call_count == 1:
                return [{"id": "voice-1"}]
            return {"id": "voice-2"}
        if path.endswith("/list"):
            return {"items": [{"id": "m1"}]}
        return {"id": "ok"}

    async def fake_message_create(request: Any):
        return EchoModel(created=request.model_dump())

    async def fake_direct_message_create(request: Any):
        return EchoModel(created=request.model_dump())

    def fake_request_sync(method: str, path: str, params=None, data=None) -> dict[str, Any]:
        return {"id": "sync-me"}

    monkeypatch.setattr(client, "_request", fake_request)
    monkeypatch.setattr(client, "_request_sync", fake_request_sync)
    monkeypatch.setattr(client, "message_create", fake_message_create)
    monkeypatch.setattr(client, "direct_message_create", fake_direct_message_create)

    await client.message_list("ch1", msg_id="m1", pin=1, flag="before")
    await client.message_view("m1")
    await client.message_create(DummyRequest(target_id="ch1", content="hello"))
    await client.message_update(DummyRequest(msg_id="m1", content="updated"))
    await client.message_delete(DummyRequest(msg_id="m1"))
    await client.message_reaction_list("m1", ":)")
    await client.message_add_reaction(DummyRequest(msg_id="m1", emoji=":a:"))
    await client.message_delete_reaction(DummyRequest(msg_id="m1", emoji=":a:", user_id="u1"))
    await client.message_pin(DummyRequest(msg_id="m1", target_id="ch1"))
    await client.message_unpin(DummyRequest(msg_id="m1", target_id="ch1"))

    await client.direct_message_list(
        chat_code="chat-1",
        target_id="u1",
        msg_id="m1",
        flag="after",
    )
    await client.direct_message_view("chat-1", "m1")
    await client.direct_message_create(DummyRequest(target_id="u1", content="dm"))
    await client.direct_message_update(DummyRequest(msg_id="m1", content="new"))
    await client.direct_message_delete(DummyRequest(msg_id="m1"))
    await client.direct_message_reaction_list("m1", ":)")
    await client.direct_message_add_reaction(DummyRequest(msg_id="m1", emoji=":a:"))
    await client.direct_message_delete_reaction(
        DummyRequest(msg_id="m1", emoji=":a:", user_id="u1")
    )

    await client.user_chat_list(page=2, page_size=10)
    await client.user_chat_view("chat-1")
    await client.user_chat_create(DummyRequest(target_id="u2"))
    await client.user_chat_delete(DummyRequest(chat_code="chat-1"))
    await client.channel_user_get_joined("g1", "u1")

    await client.guild_list(page=1, page_size=20, sort="name")
    await client.guild_view("g1")
    await client.guild_user_list(
        guild_id="g1",
        channel_id="ch1",
        search="abc",
        role_id=2,
        mobile_verified=1,
        active_time=1,
        joined_at=0,
        filter_user_id="u1",
    )
    await client.guild_nickname(DummyRequest(guild_id="g1", user_id="u1", nickname="nick"))
    await client.guild_leave(DummyRequest(guild_id="g1"))
    await client.guild_kickout(DummyRequest(guild_id="g1", target_id="u1"))
    await client.guild_mute_list("g1", return_type="detail")
    await client.guild_mute_create(DummyRequest(guild_id="g1", user_id="u1", type=1))
    await client.guild_mute_delete(DummyRequest(guild_id="g1", user_id="u1", type=1))
    await client.guild_boost_history("g1", start_time=1, end_time=2)

    await client.channel_list("g1", type=2, parent_id="p1")
    await client.channel_view("ch1", need_children=True)
    await client.channel_create(DummyRequest(guild_id="g1", name="new"))
    await client.channel_update(DummyRequest(channel_id="ch1", name="upd"))
    await client.channel_delete(DummyRequest(channel_id="ch1"))
    users_first = await client.channel_user_list("ch1")
    users_second = await client.channel_user_list("ch1")
    await client.channel_move_user(DummyRequest(user_id="u1", target_channel_id="ch2"))
    await client.channel_kickout(DummyRequest(channel_id="ch2", target_id="u1"))

    await client.channel_role_index("ch1")
    await client.channel_role_create(DummyRequest(channel_id="ch1", type=1, value="1"))
    await client.channel_role_update(DummyRequest(channel_id="ch1", type=1, value="2"))
    await client.channel_role_sync("ch1")
    await client.channel_role_delete(DummyRequest(channel_id="ch1", type=1))

    await client.send_message("ch1", "hello", type=1, nonce="abc")
    await client.send_direct_message("u1", "hello dm", type=1, nonce="def")
    await client.get_me()
    me_sync = client.get_me_sync()

    assert isinstance(users_first, list)
    assert isinstance(users_second, list)
    assert isinstance(me_sync, EchoModel)
    assert len(calls) > 30
