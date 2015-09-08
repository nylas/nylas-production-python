from pkgutil import extend_path

# Allow out-of-tree submodules.
__path__ = extend_path(__path__, __name__)

import raven
import raven.processors

from nylas.logging.log import get_logger, MAX_EXCEPTION_LENGTH

# Monkeypatch with values from your app's config to configure.
SENTRY_DSN = {}

_sentry_client = {}


def sentry_exceptions_enabled():
    return SENTRY_DSN is not None


def get_sentry_client(app_name):
    if app_name not in _sentry_client:
        _sentry_client[app_name] = raven.Client(
            SENTRY_DSN[app_name],
            processors=('nylas.logging.sentry.TruncatingProcessor',))
    return _sentry_client[app_name]


class TruncatingProcessor(raven.processors.Processor):
    """Truncates the exception value string"""

    # Note(emfree): raven.processors.Processor provides a filter_stacktrace
    # method to implement, but won't actually call it correctly. We can
    # simplify this if it gets fixed upstream.
    def process(self, data, **kwargs):
        if 'exception' not in data:
            return data
        if 'values' not in data['exception']:
            return data
        for item in data['exception']['values']:
            item['value'] = item['value'][:MAX_EXCEPTION_LENGTH]
        return data


def sentry_alert(*args, **kwargs):
    _kwargs = kwargs
    if 'extra' in kwargs:
        _kwargs = kwargs['extra']
    if 'app_name' not in _kwargs:
        raise Exception("app_name needed to get sentry client")
    app_name = _kwargs.pop('app_name')

    if sentry_exceptions_enabled():
        get_sentry_client(app_name).captureException(*args, **kwargs)


def log_uncaught_errors(logger=None, **kwargs):
    """
    Helper to log uncaught exceptions.

    All additional kwargs supplied will be sent to Sentry as extra data.

    Parameters
    ----------
    logger: structlog.BoundLogger, optional
        The logging object to write to.

    """
    logger = logger or get_logger()
    logger.error('Uncaught error', exc_info=True, **kwargs)
    sentry_alert(extra=kwargs)
