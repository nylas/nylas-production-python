"""
Logging configuration.

Mostly based off http://www.structlog.org/en/16.1.0/standard-library.html.

"""
import os
import sys
import json
import traceback
import logging
import logging.handlers

import gevent
import colorlog
import structlog

from structlog.threadlocal import wrap_dict


MAX_EXCEPTION_LENGTH = 10000


def find_first_app_frame_and_name(ignores=None):
    """
    Remove ignorable calls and return the relevant app frame. Borrowed from
    structlog, but fixes an issue when the stack includes an 'exec' statement
    or similar (f.f_globals doesn't have a '__name__' key in that case).

    Parameters
    ----------
    ignores: list, optional
        Additional names with which the first frame must not start.

    Returns
    -------
    tuple of (frame, name)
    """
    ignores = ignores or []
    f = sys._getframe()
    name = f.f_globals.get('__name__')
    while f is not None and f.f_back is not None and \
            (name is None or any(name.startswith(i) for i in ignores)):
        f = f.f_back
        name = f.f_globals.get('__name__')
    return f, name


def _record_level(logger, name, event_dict):
    """Processor that records the log level ('info', 'warning', etc.) in the
    structlog event dictionary."""
    event_dict['level'] = name
    return event_dict


def _record_module(logger, name, event_dict):
    """Processor that records the module and line where the logging call was
    invoked."""
    f, name = find_first_app_frame_and_name(
        ignores=['structlog', 'nylas.logging', 'inbox.sqlalchemy_ext.util',
                 'inbox.models.session', 'sqlalchemy', 'gunicorn.glogging'])
    event_dict['module'] = '{}:{}'.format(name, f.f_lineno)
    return event_dict


def safe_format_exception(etype, value, tb, limit=None):
    """Similar to structlog._format_exception, but truncate the exception part.
    This is because SQLAlchemy exceptions can sometimes have ludicrously large
    exception strings."""
    if tb:
        list = ['Traceback (most recent call last):\n']
        list = list + traceback.format_tb(tb, limit)
    else:
        list = []
    exc_only = traceback.format_exception_only(etype, value)
    # Normally exc_only is a list containing a single string.  For syntax
    # errors it may contain multiple elements, but we don't really need to
    # worry about that here.
    exc_only[0] = exc_only[0][:MAX_EXCEPTION_LENGTH]
    list = list + exc_only
    return ''.join(list)


def _safe_exc_info_renderer(_, __, event_dict):
    """Processor that formats exception info safely."""
    exc_info = event_dict.pop('exc_info', None)
    if exc_info:
        if not isinstance(exc_info, tuple):
            exc_info = sys.exc_info()
        event_dict['exception'] = safe_format_exception(*exc_info)
    return event_dict


def _safe_encoding_renderer(_, __, event_dict):
    """Processor that converts all strings to unicode.
       Note that we ignore conversion errors.
    """
    for key in event_dict:
        entry = event_dict[key]
        if isinstance(entry, str):
            event_dict[key] = unicode(entry, encoding='utf-8',
                                      errors='replace')

    return event_dict


class BoundLogger(structlog.stdlib.BoundLogger):
    """ BoundLogger which always adds greenlet_id and env to positional args """

    def _proxy_to_logger(self, method_name, event, *event_args, **event_kw):
        event_kw['greenlet_id'] = id(gevent.getcurrent())

        # 'prod', 'staging', 'dev' ...
        env = os.environ.get('NYLAS_ENV')
        if env is not None:
            event_kw['env'] = env

        return super(BoundLogger, self)._proxy_to_logger(
                method_name, event, *event_args, **event_kw)

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt='iso', utc=True),
        structlog.processors.StackInfoRenderer(),
        _safe_exc_info_renderer,
        _safe_encoding_renderer,
        _record_module,
        _record_level,
        structlog.processors.JSONRenderer(),
    ],
    context_class=wrap_dict(dict),
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=BoundLogger,
    cache_logger_on_first_use=True,
)
get_logger = structlog.get_logger

# Convenience map to let users set level with a string
LOG_LEVELS = {"debug": logging.DEBUG,
              "info": logging.INFO,
              "warning": logging.WARNING,
              "error": logging.ERROR,
              "critical": logging.CRITICAL}


def json_excepthook(etype, value, tb):
    log = get_logger()
    log.error(**create_error_log_context((etype, value, tb)))


def configure_logging(log_level=None):
    """ Idempotently configure logging.

    Infers options based on whether or not the output is a TTY.

    Sets the root log level to INFO if not otherwise specified.

    Overrides top-level exceptions to also print as JSON, rather than
    printing to stderr as plaintext.

    """
    sys.excepthook = json_excepthook

    # Set loglevel INFO if not otherwise specified. (We don't set a
    # default in the case that you're loading a value from a config and
    # may be passing in None explicitly if it's not defined.)
    if log_level is None:
        log_level = logging.INFO
    elif log_level in LOG_LEVELS:
        log_level = LOG_LEVELS[log_level]

    tty_handler = logging.StreamHandler(sys.stdout)
    if sys.stdout.isatty():
        # Use a more human-friendly format.
        formatter = colorlog.ColoredFormatter(
            '%(log_color)s[%(levelname)s]%(reset)s %(message)s',
            reset=True, log_colors={'DEBUG': 'cyan', 'INFO': 'green',
                                    'WARNING': 'yellow', 'ERROR': 'red',
                                    'CRITICAL': 'red'})
    else:
        formatter = logging.Formatter('%(message)s')
    tty_handler.setFormatter(formatter)
    tty_handler._nylas = True

    # Configure the root logger.
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        # If the handler was previously installed, remove it so that repeated
        # calls to configure_logging() are idempotent.
        if getattr(handler, '_nylas', False):
            root_logger.removeHandler(handler)
    root_logger.addHandler(tty_handler)
    root_logger.setLevel(log_level)


def create_error_log_context(exc_info):
    exc_type, exc_value, exc_tb = exc_info

    # Break down the info as much as Python gives us, for easier aggregation of
    # similar error types.
    error = exc_type.__name__
    error_message = exc_value.message
    error_tb = safe_format_exception(exc_type, exc_value, exc_tb)

    return dict(
        error=error,
        error_message=error_message,
        error_tb=error_tb)
