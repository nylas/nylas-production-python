import os
import logging
import tempfile

from pytest import fixture


@fixture(scope='function')
def logfile(request):
    """
    Returns an open file handle to a log file.

    Testing log file is removed at the end of the test run!

    """
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        root_logger.removeHandler(handler)

    logfile = tempfile.NamedTemporaryFile(delete=False)
    fileHandler = logging.FileHandler(logfile.name, encoding='utf-8')
    root_logger.addHandler(fileHandler)
    root_logger.setLevel(logging.DEBUG)

    def remove_logs():
        try:
            logfile.close()
            os.remove(logfile.name)
        except OSError:
            pass
    request.addfinalizer(remove_logs)

    return logfile
