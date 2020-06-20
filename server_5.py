from utils import MessageQueueUtils
import datetime


TOPIC_ROUTING_KEY = "law-1606875806-server2-topic"


def print_every_second():
	mq_object = MessageQueueUtils(
		routing_key=TOPIC_ROUTING_KEY,
		exchange_mode=MessageQueueUtils.MQ_TOPIC_EXCHANGE_TYPE
	)

	start_time = datetime.datetime.now()
	mq_object.send_message(f"System Date & Time: {start_time}")
	while True:
		if (datetime.datetime.now() - start_time).seconds == 1:
			start_time = datetime.datetime.now()
			mq_object.send_message(f"System Date & Time: {start_time}")


if __name__ == "__main__":
	print_every_second()