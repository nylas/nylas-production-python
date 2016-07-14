import logging

from nylas.logging import configure_logging


def test_configure_logging():
    root_logger = logging.getLogger()
    configure_logging(log_level="error")
    assert root_logger.getEffectiveLevel() == logging.ERROR
    configure_logging(log_level="critical")
    assert root_logger.getEffectiveLevel() == logging.CRITICAL
    configure_logging(log_level=10)
    assert root_logger.getEffectiveLevel() == logging.DEBUG
    configure_logging()
    assert root_logger.getEffectiveLevel() == logging.INFO
