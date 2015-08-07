import socket
import errno
from gevent.pywsgi import WSGIHandler

from nylas.logging import get_logger
log = get_logger()


class NylasWSGIHandler(WSGIHandler):
    """Custom WSGI handler class to customize request logging. Based on
    gunicorn.workers.ggevent.PyWSGIHandler."""
    def log_request(self):
        # gevent.pywsgi tries to call log.write(), but Python logger objects
        # implement log.debug(), log.info(), etc., so we need to monkey-patch
        # log_request(). See
        # http://stackoverflow.com/questions/9444405/gunicorn-and-websockets
        log = self.server.log
        length = self.response_length
        if self.time_finish:
            request_time = round(self.time_finish - self.time_start, 6)
        if isinstance(self.client_address, tuple):
            client_address = self.client_address[0]
        else:
            client_address = self.client_address

        # client_address is '' when requests are forwarded from nginx via
        # Unix socket. In that case, replace with a meaningful value
        if client_address == '':
            client_address = self.headers.get('X-Forward-For')
        status = getattr(self, 'status', None)
        requestline = getattr(self, 'requestline', None)

        additional_context = self.environ.get('log_context') or {}

        log.info('request handled',
                 length=length,
                 request_time=request_time,
                 client_address=client_address,
                 status=status,
                 requestline=requestline,
                 **additional_context)

    def get_environ(self):
        env = super(NylasWSGIHandler, self).get_environ()
        env['gunicorn.sock'] = self.socket
        env['RAW_URI'] = self.path
        return env

    def handle_error(self, type, value, tb):
        # Suppress tracebacks when e.g. a client disconnects from the streaming
        # API.
        if (issubclass(type, socket.error) and value.args[0] == errno.EPIPE and
                self.response_length):
            self.server.log.info('Socket error', exc=value)
            self.close_connection = True
        else:
            super(NylasWSGIHandler, self).handle_error(type, value, tb)
