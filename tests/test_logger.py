"""Tests for logger module"""

import logging

import pytest

from kook_webhook.config import LoggingConfig
from kook_webhook.logger import Logger, default_logger, get_logger


class TestLogger:
    """Tests for Logger class"""

    def test_default_initialization(self):
        """Test default logger initialization"""
        logger = Logger()
        assert logger.name == "kook_webhook"
        assert logger.config.level == "INFO"
        assert logger._logger is None

    def test_custom_initialization(self):
        """Test custom logger initialization"""
        config = LoggingConfig(level="DEBUG", use_colors=False)
        logger = Logger(name="test_logger", config=config)
        assert logger.name == "test_logger"
        assert logger.config.level == "DEBUG"
        assert logger.config.use_colors is False

    def test_setup(self):
        """Test logger setup"""
        logger = Logger(name="test_setup")
        logger.setup()

        assert logger._logger is not None
        assert isinstance(logger._logger, logging.Logger)
        assert logger._logger.name == "test_setup"
        assert len(logger._logger.handlers) > 0

    def test_logger_property(self):
        """Test logger property auto-setup"""
        logger = Logger(name="test_property")

        # First access should trigger setup
        log_instance = logger.logger
        assert log_instance is not None
        assert logger._logger is not None

    def test_logging_methods(self):
        """Test logging methods"""
        logger = Logger(name="test_methods")
        logger.setup()

        # These should not raise exceptions
        logger.info("Info message")
        logger.debug("Debug message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")

    def test_log_level(self):
        """Test different log levels"""
        config = LoggingConfig(level="ERROR")
        logger = Logger(name="test_level", config=config)
        logger.setup()

        assert logger._logger.level == logging.ERROR

    def test_colored_formatter(self):
        """Test colored formatter setup"""
        config = LoggingConfig(use_colors=True)
        logger = Logger(name="test_color", config=config)
        logger.setup()

        # Check that handler is set up
        assert len(logger._logger.handlers) > 0

    def test_plain_formatter(self):
        """Test plain formatter setup"""
        config = LoggingConfig(use_colors=False)
        logger = Logger(name="test_plain", config=config)
        logger.setup()

        # Check that handler is set up
        assert len(logger._logger.handlers) > 0
        handler = logger._logger.handlers[0]
        assert isinstance(handler.formatter, logging.Formatter)

    def test_handlers_clear_on_setup(self):
        """Test that handlers are cleared on setup"""
        logger = Logger(name="test_clear")
        logger.setup()
        initial_count = len(logger._logger.handlers)

        # Setup again
        logger.setup()
        assert len(logger._logger.handlers) == initial_count


class TestGetLogger:
    """Tests for get_logger function"""

    def test_default_logger(self):
        """Test getting default logger"""
        logger = get_logger()
        assert logger is default_logger

    def test_named_logger(self):
        """Test getting named logger"""
        logger = get_logger("custom_logger")
        assert logger.name == "custom_logger"
        assert logger is not default_logger

    def test_multiple_calls_same_name(self):
        """Test multiple calls with same name create different instances"""
        logger1 = get_logger("test_logger")
        logger2 = get_logger("test_logger")
        # Each call creates a new instance
        assert logger1 is not logger2
        assert logger1.name == logger2.name
