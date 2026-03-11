"""Pytest configuration and shared fixtures"""

import uuid

import pytest
from sanic import Sanic

from kook_webhook.app import WebhookApp
from kook_webhook.config import Config


@pytest.fixture
def config():
    """Create a test configuration"""
    # Use unique name for each test to avoid Sanic app name conflicts
    unique_name = f"test_app_{uuid.uuid4().hex[:8]}"
    return Config(
        name=unique_name,
        host="127.0.0.1",
        port=8888,
        verify_token="test_verify_token",
        encrypt_key="test_encrypt_key",
        access_log=False,
    )


@pytest.fixture
def app(config):
    """Create a test WebhookApp"""
    # Enable Sanic test mode to avoid app name conflicts
    Sanic.test_mode = True
    app = WebhookApp(config=config)
    yield app
    # Cleanup: remove app from Sanic registry
    try:
        if config.name in Sanic._app_registry:
            del Sanic._app_registry[config.name]
    except Exception:
        pass
    Sanic.test_mode = False


@pytest.fixture
def sample_webhook_message():
    """Sample webhook message data"""
    return {
        "s": 0,
        "d": {
            "channel_type": "GROUP",
            "type": 1,
            "target_id": "1234567890",
            "author_id": "9876543210",
            "content": "Hello, World!",
            "msg_id": "abc123",
            "msg_timestamp": 1234567890,
            "nonce": "nonce123",
            "extra": {
                "type": 1,
                "guild_id": "guild123",
                "channel_name": "test-channel",
                "mention": [],
                "mention_all": False,
                "mention_roles": [],
                "mention_here": False,
                "author": {
                    "id": "9876543210",
                    "username": "testuser",
                    "identify_num": "1234",
                    "online": True,
                    "status": 1,
                    "avatar": "avatar.png",
                    "bot": False,
                },
            },
        },
    }


@pytest.fixture
def sample_system_event():
    """Sample system event data"""
    return {
        "s": 0,
        "d": {
            "channel_type": "GROUP",
            "type": 255,
            "target_id": "1234567890",
            "author_id": "9876543210",
            "content": "",
            "msg_id": "sys123",
            "msg_timestamp": 1234567890,
            "nonce": "nonce456",
            "extra": {
                "type": "joined_guild",
                "body": {
                    "user_id": "9876543210",
                    "joined_at": 1234567890,
                },
            },
        },
    }


@pytest.fixture
def sample_challenge():
    """Sample WEBHOOK_CHALLENGE data"""
    return {
        "s": 0,
        "d": {
            "channel_type": "WEBHOOK_CHALLENGE",
            "type": 255,
            "challenge": "challenge_token_123",
            "verify_token": "test_verify_token",
        },
    }


@pytest.fixture
def sample_command_message():
    """Sample command message data"""
    return {
        "s": 0,
        "d": {
            "channel_type": "GROUP",
            "type": 9,
            "target_id": "1234567890",
            "author_id": "9876543210",
            "content": "/help test args",
            "msg_id": "cmd123",
            "msg_timestamp": 1234567890,
            "nonce": "nonce789",
            "extra": {
                "type": 9,
                "guild_id": "guild123",
                "channel_name": "test-channel",
                "mention": [],
                "mention_all": False,
                "mention_roles": [],
                "mention_here": False,
                "author": {
                    "id": "9876543210",
                    "username": "testuser",
                    "identify_num": "1234",
                    "online": True,
                    "status": 1,
                    "avatar": "avatar.png",
                    "bot": False,
                },
            },
        },
    }
