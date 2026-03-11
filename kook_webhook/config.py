import os
from dataclasses import dataclass, field


def _str_to_bool(value: str) -> bool:
    """Convert string to boolean

    :param value: String value to convert
    :return: Boolean value
    """
    return value.lower() in ("true", "1", "yes", "on")


@dataclass
class LoggingConfig:
    """Logging configuration"""

    level: str = field(default_factory=lambda: os.getenv("KOOK_WEBHOOK_LOG_LEVEL", "INFO"))
    format: str = field(
        default_factory=lambda: os.getenv(
            "KOOK_WEBHOOK_LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    )
    use_colors: bool = field(
        default_factory=lambda: _str_to_bool(os.getenv("KOOK_WEBHOOK_LOG_USE_COLORS", "true"))
    )


@dataclass
class Config:
    """Webhook configuration

    Configuration can be set via environment variables with KOOK_WEBHOOK_ prefix:
        - KOOK_WEBHOOK_NAME
        - KOOK_WEBHOOK_HOST
        - KOOK_WEBHOOK_PORT
        - KOOK_WEBHOOK_ACCESS_LOG
        - KOOK_WEBHOOK_WEBHOOK_ENDPOINT
        - KOOK_WEBHOOK_HEALTHZ_ENDPOINT
        - KOOK_WEBHOOK_STATS_ENDPOINT
        - KOOK_WEBHOOK_COMMAND_PREFIX
        - KOOK_WEBHOOK_AUTH_ENABLED
        - KOOK_WEBHOOK_AUTH_HEADER_NAME
        - KOOK_WEBHOOK_AUTH_TOKEN
        - KOOK_WEBHOOK_BOT_USER_ID
        - KOOK_WEBHOOK_BOT_TOKEN
        - KOOK_WEBHOOK_VERIFY_TOKEN
        - KOOK_WEBHOOK_ENCRYPT_KEY
        - KOOK_WEBHOOK_AUTO_COMPRESS
        - KOOK_WEBHOOK_LOG_LEVEL
        - KOOK_WEBHOOK_LOG_FORMAT
        - KOOK_WEBHOOK_LOG_USE_COLORS

    Example:
        >>> import os
        >>> os.environ["KOOK_WEBHOOK_HOST"] = "127.0.0.1"
        >>> os.environ["KOOK_WEBHOOK_PORT"] = "9000"
        >>> config = Config()
        >>> print(config.host, config.port)
        127.0.0.1 9000
    """

    # Server configuration
    name: str = field(default_factory=lambda: os.getenv("KOOK_WEBHOOK_NAME", "kook_webhook"))
    host: str = field(default_factory=lambda: os.getenv("KOOK_WEBHOOK_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("KOOK_WEBHOOK_PORT", "8000")))
    access_log: bool = field(
        default_factory=lambda: _str_to_bool(os.getenv("KOOK_WEBHOOK_ACCESS_LOG", "true"))
    )
    webhook_endpoint: str = field(
        default_factory=lambda: os.getenv("KOOK_WEBHOOK_WEBHOOK_ENDPOINT", "/webhook")
    )
    healthz_endpoint: str = field(
        default_factory=lambda: os.getenv("KOOK_WEBHOOK_HEALTHZ_ENDPOINT", "/healthz")
    )
    stats_endpoint: str = field(
        default_factory=lambda: os.getenv("KOOK_WEBHOOK_STATS_ENDPOINT", "/stats")
    )
    auth_enabled: bool = field(
        default_factory=lambda: _str_to_bool(os.getenv("KOOK_WEBHOOK_AUTH_ENABLED", "false"))
    )
    auth_header_name: str = field(
        default_factory=lambda: os.getenv("KOOK_WEBHOOK_AUTH_HEADER_NAME", "X-Webhook-Token")
    )
    auth_token: str = field(default_factory=lambda: os.getenv("KOOK_WEBHOOK_AUTH_TOKEN", ""))

    # KOOK configuration
    bot_user_id: str = field(default_factory=lambda: os.getenv("KOOK_WEBHOOK_BOT_USER_ID", ""))
    bot_token: str = field(default_factory=lambda: os.getenv("KOOK_WEBHOOK_BOT_TOKEN", ""))
    verify_token: str = field(default_factory=lambda: os.getenv("KOOK_WEBHOOK_VERIFY_TOKEN", ""))
    encrypt_key: str = field(default_factory=lambda: os.getenv("KOOK_WEBHOOK_ENCRYPT_KEY", ""))
    command_prefix: str = field(
        default_factory=lambda: os.getenv("KOOK_WEBHOOK_COMMAND_PREFIX", "/")
    )

    # Logging configuration
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    # Other configuration
    auto_compress: bool = field(
        default_factory=lambda: _str_to_bool(os.getenv("KOOK_WEBHOOK_AUTO_COMPRESS", "true"))
    )
