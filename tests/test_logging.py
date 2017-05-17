import sys
import json
import logging

from nylas.logging import configure_logging, get_logger


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


def test_basic_log(logfile):
    configure_logging()
    log = get_logger()

    log.info("Hi")
    out = json.loads(logfile.readlines()[0])
    assert out['event'] == "Hi"
    assert out['level'] == "info"
    assert 'error_name' not in out
    assert 'error_message' not in out
    assert 'error_traceback' not in out
    assert 'error' not in out
    assert 'exc_info' not in out
    assert 'exception' not in out


def test_standard_error(logfile):
    configure_logging()
    log = get_logger()

    log.error("Oh no")
    out = json.loads(logfile.readlines()[0])
    assert out['event'] == "Oh no"
    assert out['level'] == "error"
    assert 'error_name' not in out
    assert 'error_message' not in out
    assert 'error_traceback' not in out
    assert 'error' not in out
    assert 'exc_info' not in out
    assert 'exception' not in out


def test_standard_exception(logfile):
    configure_logging()
    log = get_logger()

    try:
        raise ValueError("Test message")
    except ValueError:
        log.error("Oh no")
        out = json.loads(logfile.readlines()[0])
        assert out['event'] == "Oh no"
        assert out['level'] == "error"
        assert out['error_name'] == "ValueError"
        assert out['error_message'] == "Test message"
        assert 'error_traceback' in out
        assert 'error' not in out
        assert 'exc_info' not in out
        assert 'exception' not in out


def test_code(logfile):
    configure_logging()
    log = get_logger()

    class CodeError(Exception):
        def __init__(self, msg, code):
            self.message = msg
            self.code = code

    try:
        raise CodeError("Custom message", 404)
    except CodeError:
        log.error("Oh no")
        out = json.loads(logfile.readlines()[0])
        assert out['event'] == "Oh no"
        assert out['level'] == "error"
        assert out['error_name'] == "CodeError"
        assert out['error_message'] == "Custom message"
        assert 'error_traceback' in out
        assert out['error_code'] == 404
        assert 'error' not in out
        assert 'exc_info' not in out
        assert 'exception' not in out


def test_exclude_exception(logfile):
    configure_logging()
    log = get_logger()

    try:
        raise ValueError("Test message")
    except ValueError:
        log.error("Oh no", include_exception=False)
        out = json.loads(logfile.readlines()[0])
        assert out['event'] == "Oh no"
        assert out['level'] == "error"
        assert 'error_name' not in out
        assert 'error_message' not in out
        assert 'error_traceback' not in out
        assert 'error' not in out
        assert 'exc_info' not in out
        assert 'exception' not in out


def test_alternative_arg_errors(logfile):
    """
    Allow a user to pass an object to `error=err_obj`
    Allow a user to pass a string to `error='foo'`
    Also allow `exc_info=True`
    """
    configure_logging()
    log = get_logger()

    try:
        raise ValueError("Test message")
    except ValueError as err_obj:
        log.exception("0 test")
        log.error("1 test")
        log.warn("2 test", include_exception=True)
        log.info("3 test", include_exception=True)
        log.error("4 test", error=err_obj)
        log.error("5 test", exc_info=sys.exc_info())
        log.error("6 test", exc_info=True)
        log.error("7 test", error="OVERRIDDEN MESSAGE")
        log.error("8 test", error=100.0)
        log.error("9 test", error=True)

    lines = logfile.readlines()
    for i, line in enumerate(lines):
        out = json.loads(line)
        assert out['event'] == "{} test".format(i)
        assert out['error_name'] == "ValueError"
        if i == 7:
            assert out['error_message'] == "OVERRIDDEN MESSAGE"
        elif i == 8:
            assert out['error_message'] == 100.0
        elif i == 9:
            assert out['error_message'] is True
        else:
            assert out['error_message'] == "Test message"
        assert 'error_traceback' in out


def test_out_of_scope_passed_error(logfile):
    """
    If an error is thrown out of band ensure there's no error data

    Unless we pass a value to the `error` field, in which case stuff it
    in `error_message`
    """
    configure_logging()
    log = get_logger()

    log.error("0 test", exc_info=sys.exc_info())
    log.error("1 test", exc_info=True)
    log.error("2 test", error="OVERRIDDEN MESSAGE")
    log.error("3 test", error=100.0)
    log.error("4 test", error=True)
    log.warn("5 test", include_exception=True)
    log.info("6 test", include_exception=True)
    log.exception("7 test")

    lines = logfile.readlines()
    for i, line in enumerate(lines):
        out = json.loads(line)
        assert out['event'] == "{} test".format(i)
        assert 'error_name' not in out
        assert 'error_traceback' not in out
        if i == 2:
            assert out['error_message'] == "OVERRIDDEN MESSAGE"
        elif i == 3:
            assert out['error_message'] == 100.0
        elif i == 4:
            assert out['error_message'] is True
        else:
            assert 'error_message' not in out


def test_out_of_scope_exception(logfile):
    configure_logging()
    log = get_logger()

    log.exception("Oh no")
    out = json.loads(logfile.readlines()[0])
    assert out['event'] == "Oh no"
    assert out['level'] == "error"
    assert 'error_name' not in out
    assert 'error_message' not in out
    assert 'error_traceback' not in out
