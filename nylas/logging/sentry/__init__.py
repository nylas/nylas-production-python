from pkgutil import extend_path

# Allow out-of-tree submodules.
__path__ = extend_path(__path__, __name__)

import raven
import raven.processors

from nylas.logging.log import get_logger, MAX_EXCEPTION_LENGTH

_sentry_client = None


def get_sentry_client(sentry_dsn=None):
    if _sentry_client is None:
        return raven.Client(
            sentry_dsn,
            processors=('nylas.logging.TruncatingProcessor',))
    return _sentry_client


class TruncatingProcessor(raven.processors.Processor):
    """Truncates the exception value string, and strips stack locals.
    Sending stack locals could potentially leak information."""

    # A whitelist of locals we don't want to strip.
    # They must be non-PII!
    locals_whitelist = ['account_id', 'message_id']

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
            stacktrace = item.get('stacktrace')
            if stacktrace is not None:
                if 'frames' in stacktrace:
                    for frame in stacktrace['frames']:
                        for stack_local in frame['vars'].keys():
                            if stack_local not in self.locals_whitelist:
                                frame['vars'].pop(stack_local)
        return data


def sentry_alert(*args, **kwargs):
    get_sentry_client().captureException(*args, **kwargs)


def log_uncaught_errors(logger=None, account_id=None, action_id=None,
                        log_to_sentry=False):
    """
    Helper to log uncaught exceptions.

    Parameters
    ----------
    logger: structlog.BoundLogger, optional
        The logging object to write to.

    """
    logger = logger or get_logger()
    logger.error('Uncaught error', exc_info=True, action_id=action_id)
    user_data = {'account_id': account_id, 'action_id': action_id}
    if log_to_sentry:
        sentry_alert(extra=user_data)
