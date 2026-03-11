"""Tests for config module"""

import os

import pytest

from kook_webhook.config import Config, LoggingConfig, _str_to_bool


class TestStrToBool:
    """Tests for _str_to_bool function"""

    def test_true_values(self):
        """Test various true values"""
        assert _str_to_bool("true") is True
        assert _str_to_bool("True") is True
        assert _str_to_bool("TRUE") is True
        assert _str_to_bool("1") is True
        assert _str_to_bool("yes") is True
        assert _str_to_bool("YES") is True
        assert _str_to_bool("on") is True
        assert _str_to_bool("ON") is True

    def test_false_values(self):
        """Test various false values"""
        assert _str_to_bool("false") is False
        assert _str_to_bool("False") is False
        assert _str_to_bool("0") is False
        assert _str_to_bool("no") is False
        assert _str_to_bool("off") is False
        assert _str_to_bool("random") is False


class TestLoggingConfig:
    """Tests for LoggingConfig"""

    def test_default_values(self):
        """Test default logging configuration"""
        config = LoggingConfig()
        assert config.level == "INFO"
        assert "%(asctime)s" in config.format
        assert config.use_colors is True

    def test_custom_values(self):
        """Test custom logging configuration"""
        config = LoggingConfig(
            level="DEBUG",
            format="%(message)s",
            use_colors=False,
        )
        assert config.level == "DEBUG"
        assert config.format == "%(message)s"
        assert config.use_colors is False

    def test_env_override(self):
        """Test environment variable override"""
        os.environ["KOOK_WEBHOOK_LOG_LEVEL"] = "WARNING"
        os.environ["KOOK_WEBHOOK_LOG_USE_COLORS"] = "false"

        config = LoggingConfig()

        assert config.level == "WARNING"
        assert config.use_colors is False

        # Cleanup
        del os.environ["KOOK_WEBHOOK_LOG_LEVEL"]
        del os.environ["KOOK_WEBHOOK_LOG_USE_COLORS"]


class TestConfig:
    """Tests for Config"""

    def test_default_values(self):
        """Test default configuration values"""
        config = Config()
        assert config.name == "kook_webhook"
        assert config.host == "0.0.0.0"
        assert config.port == 8000
        assert config.access_log is True
        assert config.webhook_endpoint == "/webhook"
        assert config.healthz_endpoint == "/healthz"
        assert config.stats_endpoint == "/stats"
        assert config.auth_enabled is False
        assert config.auth_header_name == "X-Webhook-Token"
        assert config.auth_token == ""
        assert config.verify_token == ""
        assert config.encrypt_key == ""
        assert config.auto_compress is True
        assert isinstance(config.logging, LoggingConfig)

    def test_custom_values(self):
        """Test custom configuration values"""
        config = Config(
            name="custom_app",
            host="192.168.1.1",
            port=9000,
            webhook_endpoint="/kook-webhook",
            healthz_endpoint="/status",
            stats_endpoint="/metrics",
            auth_enabled=True,
            auth_header_name="X-Test-Token",
            auth_token="token_abc",
            verify_token="my_token",
            encrypt_key="my_key",
            access_log=False,
            auto_compress=False,
        )
        assert config.name == "custom_app"
        assert config.host == "192.168.1.1"
        assert config.port == 9000
        assert config.webhook_endpoint == "/kook-webhook"
        assert config.healthz_endpoint == "/status"
        assert config.stats_endpoint == "/metrics"
        assert config.auth_enabled is True
        assert config.auth_header_name == "X-Test-Token"
        assert config.auth_token == "token_abc"
        assert config.verify_token == "my_token"
        assert config.encrypt_key == "my_key"
        assert config.access_log is False
        assert config.auto_compress is False

    def test_env_override(self):
        """Test environment variable override"""
        os.environ["KOOK_WEBHOOK_NAME"] = "env_app"
        os.environ["KOOK_WEBHOOK_HOST"] = "127.0.0.1"
        os.environ["KOOK_WEBHOOK_PORT"] = "7777"
        os.environ["KOOK_WEBHOOK_WEBHOOK_ENDPOINT"] = "/hook"
        os.environ["KOOK_WEBHOOK_HEALTHZ_ENDPOINT"] = "/ping"
        os.environ["KOOK_WEBHOOK_STATS_ENDPOINT"] = "/metrics"
        os.environ["KOOK_WEBHOOK_AUTH_ENABLED"] = "true"
        os.environ["KOOK_WEBHOOK_AUTH_HEADER_NAME"] = "X-Env-Token"
        os.environ["KOOK_WEBHOOK_AUTH_TOKEN"] = "env_auth_token"
        os.environ["KOOK_WEBHOOK_VERIFY_TOKEN"] = "env_token"
        os.environ["KOOK_WEBHOOK_ENCRYPT_KEY"] = "env_key"
        os.environ["KOOK_WEBHOOK_ACCESS_LOG"] = "false"
        os.environ["KOOK_WEBHOOK_AUTO_COMPRESS"] = "0"

        config = Config()

        assert config.name == "env_app"
        assert config.host == "127.0.0.1"
        assert config.port == 7777
        assert config.webhook_endpoint == "/hook"
        assert config.healthz_endpoint == "/ping"
        assert config.stats_endpoint == "/metrics"
        assert config.auth_enabled is True
        assert config.auth_header_name == "X-Env-Token"
        assert config.auth_token == "env_auth_token"
        assert config.verify_token == "env_token"
        assert config.encrypt_key == "env_key"
        assert config.access_log is False
        assert config.auto_compress is False

        # Cleanup
        del os.environ["KOOK_WEBHOOK_NAME"]
        del os.environ["KOOK_WEBHOOK_HOST"]
        del os.environ["KOOK_WEBHOOK_PORT"]
        del os.environ["KOOK_WEBHOOK_WEBHOOK_ENDPOINT"]
        del os.environ["KOOK_WEBHOOK_HEALTHZ_ENDPOINT"]
        del os.environ["KOOK_WEBHOOK_STATS_ENDPOINT"]
        del os.environ["KOOK_WEBHOOK_AUTH_ENABLED"]
        del os.environ["KOOK_WEBHOOK_AUTH_HEADER_NAME"]
        del os.environ["KOOK_WEBHOOK_AUTH_TOKEN"]
        del os.environ["KOOK_WEBHOOK_VERIFY_TOKEN"]
        del os.environ["KOOK_WEBHOOK_ENCRYPT_KEY"]
        del os.environ["KOOK_WEBHOOK_ACCESS_LOG"]
        del os.environ["KOOK_WEBHOOK_AUTO_COMPRESS"]

    def test_custom_logging_config(self):
        """Test custom logging configuration"""
        logging_config = LoggingConfig(level="ERROR", use_colors=False)
        config = Config(logging=logging_config)

        assert config.logging.level == "ERROR"
        assert config.logging.use_colors is False
