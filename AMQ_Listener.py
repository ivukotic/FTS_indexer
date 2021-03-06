import uuid
import json
import logging
import stomp

log = logging.getLogger(__name__)


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
        self.connection = stomp.Connection([(host, port)], use_ssl=False)
        self.connection.set_listener('MessagingListener', self)
        self.connection.start()
        self.connection.connect(self.user, self.password, wait=False)
        self.topic = topic
        self.callback = callback

    def on_connecting(self, host_and_port):
        log.debug('ActiveMQ connected socket to %s' % str(host_and_port))

    def on_connected(self, headers, body):
        log.info('ActiveMQ connected %s' % headers)
        self.connection.subscribe(
            destination=self.topic,
            id='activemq-listener-%s' % self.id,
            ack='auto',
            headers={"durable": True, "auto-delete": False}
        )

    def on_disconnected(self):
        log.warning('ActiveMQ connection lost. Try to reconnect...')
        self.connection.connect(self.user, self.password, wait=False)

    def on_heartbeat_timeout(self):
        log.warning('ActiveMQ heartbeat timeout. Try to reconnect...')
        self.connection.stop()
        self.connection.start()
        self.connection.connect(self.user, self.password, wait=False)

    def on_message(self, headers, message):
        message = message[:-1]  # Skip EOT
        try:
            content = json.loads(message)
            self.callback(content)
        except Exception as e:
            log.warning('Failed to process message: (%s) %s' % (type(e).__name__, e.message))
            log.warning(message)
            raise

    def on_error(self, headers, body):
        log.error('ActiveMQ error: %s' % body)
