from utils import MessageQueueUtils
from http import HTTPStatus

import json
import requests
import os
import time
import threading

DIRECT_ROUTING_KEY = "law-1606875806-server1-server2"
TOPIC_ROUTING_KEY = "law-1606875806-server2-topic"
DOWNLOADED_FILE_DIR = "./server_2_downloads"
FILE_CHUNK_SIZE = 2048
DOWNLOAD_PAYLOAD = {}
DOWNLOADED_FILE_PAYLOAD = {}
SERVER_3_URL = "http://localhost:3032/"


def generate_path(file_name):
	return os.path.join(DOWNLOADED_FILE_DIR, file_name)


def receive_from_producer():
	direct_mq_connection = MessageQueueUtils(
		routing_key=DIRECT_ROUTING_KEY,
		exchange_mode=MessageQueueUtils.MQ_DIRECT_EXCHANGE_TYPE
	)

	direct_mq_connection.consume_message(callback_function=callback)
	direct_mq_connection.close_connection()


def callback(body):
	received_json = json.loads(body)
	for key in list(received_json.keys()):
		run_download_in_background(
			download_url=received_json[key]["download_url"],
			file_name=received_json[key]["file_name"]
		)

	requests.post(
		SERVER_3_URL,
		files=DOWNLOADED_FILE_PAYLOAD
	)


def download(download_url, file_name):
	global DOWNLOADED_FILE_PAYLOAD
	mq_object = MessageQueueUtils(
		routing_key=TOPIC_ROUTING_KEY,
		exchange_mode=MessageQueueUtils.MQ_TOPIC_EXCHANGE_TYPE
	)
	download_file_request = requests.get(download_url, stream=True)

	if download_file_request.status_code == HTTPStatus.OK:
		file_size = download_file_request.headers['content-length']

		with open(generate_path(file_name), 'wb') as f:
			downloaded_percentage = 0
			if float(file_size) == 0.0:
				f.write(download_file_request.content())
			else:
				for chunk in download_file_request.iter_content(FILE_CHUNK_SIZE):
					time.sleep(0.1)
					f.write(chunk)
					downloaded_percentage += len(chunk)
					percentage_done = (downloaded_percentage / int(file_size)) * 100.0
					if downloaded_percentage != percentage_done:
						DOWNLOAD_PAYLOAD[file_name] = f'Download Progress for file {file_name}: {percentage_done}%'
						mq_object.send_message(json.dumps(DOWNLOAD_PAYLOAD))

				DOWNLOADED_FILE_PAYLOAD[f'file_{len(list(DOWNLOADED_FILE_PAYLOAD.keys()))+1}'] = open(generate_path(file_name), 'rb')

		mq_object.close_connection()


def run_download_in_background(download_url, file_name):
	background_thread = threading.Thread(target=download, args=(download_url, file_name))
	background_thread.start()
	background_thread.join()


if __name__ == '__main__':
	os.system(f'mkdir -p {DOWNLOADED_FILE_DIR}')
	receive_from_producer()
