import logging
import sys
from typing import Optional

from .config import LoggingConfig


class Logger:
    """Logger manager"""

    def __init__(self, name: str = "kook_webhook", config: Optional[LoggingConfig] = None):
        self.name = name
        self.config = config or LoggingConfig()
        self._logger: Optional[logging.Logger] = None

    def setup(self):
        """Setup logger"""
        self._logger = logging.getLogger(self.name)
        self._logger.setLevel(getattr(logging, self.config.level.upper()))

        # Clear existing handlers
        self._logger.handlers.clear()

        # Console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)

        # Formatter
        if self.config.use_colors:
            try:
                from colorlog import ColoredFormatter

                formatter = ColoredFormatter(
                    "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    log_colors={
                        "DEBUG": "cyan",
                        "INFO": "green",
                        "WARNING": "yellow",
                        "ERROR": "red",
                        "CRITICAL": "red,bg_white",
                    },
                )
            except ImportError:
                formatter = logging.Formatter(self.config.format)
        else:
            formatter = logging.Formatter(self.config.format)

        handler.setFormatter(formatter)
        self._logger.addHandler(handler)

    @property
    def logger(self) -> logging.Logger:
        """Get logger instance"""
        if self._logger is None:
            self.setup()
        return self._logger

    def info(self, msg: str, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)

    def debug(self, msg: str, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs):
        self.logger.critical(msg, *args, **kwargs)


# Default logger instance
default_logger = Logger()


def get_logger(name: Optional[str] = None) -> Logger:
    """Get logger instance"""
    if name is None:
        return default_logger
    return Logger(name=name)
