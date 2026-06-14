import time
import uuid
import json
import logging
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
        self.user = user
        self.password = password
        # heartbeats=(send_ms, recv_ms) — broker must reply within recv_ms or
        # the stomp library fires on_heartbeat_timeout automatically.
        self.connection = stomp.Connection([(host, port)], heartbeats=(4000, 4000))
        self.connection.set_listener('MessagingListener', self)
        self.topic = topic
        self.callback = callback
        self.connection.connect(self.user, self.password, wait=True)

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
        # Let on_disconnected handle reconnection by forcing a clean disconnect.
        log.warning('ActiveMQ heartbeat timeout. Forcing disconnect to trigger reconnect...')
        try:
            self.connection.disconnect()
        except Exception:
            pass

    def _reconnect(self):
        delay = 5
        attempt = 0
        while True:
            attempt += 1
            try:
                log.info(f'Reconnect attempt {attempt}...')
                self.connection.connect(self.user, self.password, wait=True)
                return
            except Exception as e:
                log.warning(f'Reconnect attempt {attempt} failed: {e}. Retry in {delay}s...')
                time.sleep(delay)
                delay = min(delay * 2, _RECONNECT_DELAY_MAX)

    def on_message(self, frame):
        message = frame.body[:-1]  # Skip EOT
        try:
            content = json.loads(message)
            self.callback(content)
        except Exception as e:
            log.warning('Failed to process message: (%s) %s' % (type(e).__name__, e))
            log.warning(message)
            raise

    def on_error(self, frame):
        log.error(f'ActiveMQ error: {frame.body}')
