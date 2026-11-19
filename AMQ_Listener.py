import time
import uuid
import json
import logging
import threading
import stomp

log = logging.getLogger(__name__)

_RECONNECT_DELAY_MAX = 60  # seconds


class ActiveMqListener(stomp.ConnectionListener):
    """
    ActiveMQ client
    """

    def __init__(self, host, port, topic, callback, user, password):
        """
        Constructor
        """
        self.id = str(uuid.uuid4())
        self.host_and_port = f'{host}:{port}'
        self._last_error = None  # most recent broker ERROR frame text
        self.user = user
        self.password = password
        self._reconnect_lock = threading.Lock()
        # heartbeats=(send_ms, recv_ms) — broker must reply within recv_ms
        # or the stomp library fires on_heartbeat_timeout automatically.
        # reconnect_attempts_max is the number of socket-open attempts stomp.py
        # makes inside a single connect() call (not a background thread).
        # It must be >= 1: with 0 the socket loop never runs and connect()
        # immediately raises an empty ConnectFailedException. We use 1 so
        # retry/backoff is owned entirely by _reconnect() below.
        self.connection = stomp.Connection(
            [(host, port)], heartbeats=(4000, 4000), reconnect_attempts_max=1
        )
        self.connection.set_listener('MessagingListener', self)
        self.topic = topic
        self.callback = callback
        # Handles initial connect with backoff so startup failures don't
        # crash the process.
        self._reconnect()

    def on_connecting(self, host_and_port):
        log.debug(f'ActiveMQ connected socket to {str(host_and_port)}')

    def on_connected(self, frame):
        log.info(f'ActiveMQ connected {frame.body}')
        self.connection.subscribe(
            destination=self.topic,
            id=f'activemq-listener-{self.id}',
            ack='auto',
            headers={"durable": True, "auto-delete": False}
        )

    def on_disconnected(self):
        log.warning('ActiveMQ connection lost. Reconnecting with backoff...')
        self._reconnect()

    def on_heartbeat_timeout(self):
        # stomp.py already disconnects the socket when a heartbeat times out,
        # which fires on_disconnected — that handler owns reconnection.
        # Calling disconnect() here races with an already-completed reconnect
        # and sends a duplicate CONNECT frame, which the broker rejects with
        # "duplicate CONNECT or STOMP frame".
        log.warning(
            'ActiveMQ heartbeat timeout '
            '(reconnect handled by on_disconnected).'
        )

    def _reconnect(self):
        # on_disconnected() and on_heartbeat_timeout() can both fire around
        # the same time; without this guard they would call connect()
        # concurrently and send overlapping CONNECT frames on the same
        # socket, which the broker rejects as a duplicate CONNECT.
        if not self._reconnect_lock.acquire(blocking=False):
            log.debug('Reconnect already in progress, skipping.')
            return
        try:
            delay = 5
            attempt = 0
            while True:
                attempt += 1
                self._last_error = None
                try:
                    log.info(
                        f'Connect attempt {attempt} to {self.host_and_port} '
                        f'as user {self.user!r}...'
                    )
                    self.connection.connect(
                        self.user, self.password, wait=True
                    )
                    return
                except Exception as e:
                    # stomp.py's ConnectFailedException has an empty message;
                    # the real reason is in the broker's ERROR frame (captured
                    # in on_error) or in the exception's cause/type.
                    reason = str(e) or repr(e)
                    if e.__cause__ or e.__context__:
                        reason += f' (caused by {e.__cause__ or e.__context__!r})'
                    if self._last_error:
                        reason += f' | broker said: {self._last_error}'
                    log.warning(
                        f'Connect attempt {attempt} to {self.host_and_port} '
                        f'failed: {type(e).__name__}: {reason}. '
                        f'Retry in {delay}s...'
                    )
                    log.debug('Connect failure traceback', exc_info=True)
                    time.sleep(delay)
                    delay = min(delay * 2, _RECONNECT_DELAY_MAX)
        finally:
            self._reconnect_lock.release()

    def on_message(self, frame):
        message = frame.body[:-1]  # Skip EOT
        try:
            content = json.loads(message)
            self.callback(content)
        except Exception as e:
            log.warning(
                'Failed to process message: (%s) %s' % (type(e).__name__, e)
            )
            log.warning(message)
            raise

    def on_error(self, frame):
        # Brokers usually put the reason (e.g. auth failure) in the 'message'
        # header; the body is often empty or holds extra details.
        headers = frame.headers or {}
        msg = headers.get('message', '')
        body = (frame.body or '').strip()
        self._last_error = ' '.join(p for p in (msg, body) if p) or str(headers)
        log.error(
            f'ActiveMQ error from {self.host_and_port}: {self._last_error} '
            f'(headers={headers})'
        )
