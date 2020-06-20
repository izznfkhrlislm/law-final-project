from pika import BlockingConnection, ConnectionParameters, PlainCredentials


class MessageQueueUtils:
	MQ_DIRECT_EXCHANGE_TYPE = "direct"
	MQ_TOPIC_EXCHANGE_TYPE = "topic"
	MQ_DIRECT_EXCHANGE_NAME = "1606875806_DIRECT"
	MQ_TOPIC_EXCHANGE_NAME = "1606875806_TOPIC"
	MQ_HOST = "152.118.148.95"
	MQ_PORT = 5672
	MQ_USERNAME = "0806444524"
	MQ_PASSWORD = "0806444524"
	MQ_VIRTUAL_HOST = "/0806444524"

	def __init__(self, routing_key, exchange_mode):
		self.routing_key = routing_key
		self.exchange_mode = exchange_mode
		self.exchange_name = self.MQ_DIRECT_EXCHANGE_NAME if self.exchange_mode == self.MQ_DIRECT_EXCHANGE_TYPE \
			else self.MQ_TOPIC_EXCHANGE_NAME

		self.pika_connection = BlockingConnection(
			ConnectionParameters(
				host=self.MQ_HOST,
				virtual_host=self.MQ_VIRTUAL_HOST,
				port=self.MQ_PORT,
				credentials=PlainCredentials(self.MQ_USERNAME, self.MQ_PASSWORD)
			)
		)

		self.connection_channel = self.pika_connection.channel()
		self.connection_channel.exchange_declare(
			exchange=self.exchange_name,
			exchange_type=self.exchange_mode
		)
		self.connection_channel.queue_declare(queue=self.routing_key)

	def send_message(self, message):
		self.connection_channel.basic_publish(
			exchange=self.exchange_name,
			routing_key=self.routing_key,
			body=message
		)

	def consume_message(self, callback_function):
		self.connection_channel.queue_bind(
			exchange=self.exchange_name,
			queue=self.routing_key
		)

		def __callback(ch, method, properties, body):
			callback_function(body)

		self.connection_channel.basic_consume(
			queue=self.routing_key,
			on_message_callback=__callback,
			auto_ack=True
		)
		self.connection_channel.start_consuming()

	def close_connection(self):
		self.pika_connection.close()
