from flask import Flask, render_template, request, jsonify
from http import HTTPStatus
from utils import MessageQueueUtils

import json
import re

app = Flask(__name__)
PORT = 3030
ROUTING_KEY = "law-1606875806-server1-server2"
TOPIC_ROUTING_KEY = "law-1606875806-server2-topic"
MQ_WEBSOCKET_PORT = 15674


@app.route('/', methods=['GET', 'POST'])
def show_index_page():
	if request.method == 'POST':
		url_payloads = {}
		routing_key = ROUTING_KEY
		direct_pika_connection = MessageQueueUtils(
			routing_key=routing_key,
			exchange_mode=MessageQueueUtils.MQ_DIRECT_EXCHANGE_TYPE
		)

		for download_url_key in list(dict(request.form).keys()):
			download_url = request.form[download_url_key]
			if not download_url or not is_download_url_valid(download_url):
				return jsonify({
					"Error": "Invalid Download URL in one of the forms!"
				}), HTTPStatus.BAD_REQUEST

			file_name = download_url.split('/')[-1]
			url_payloads[download_url_key] = {
				"download_url": download_url,
				"file_name": file_name
			}

		direct_pika_connection.send_message(json.dumps(url_payloads))
		direct_pika_connection.close_connection()

		return render_template(
			'download_progress.html',
			mq_username=MessageQueueUtils.MQ_USERNAME,
			mq_password=MessageQueueUtils.MQ_PASSWORD,
			mq_virtual_host=MessageQueueUtils.MQ_VIRTUAL_HOST,
			ws_url=f'http://{MessageQueueUtils.MQ_HOST}:{MQ_WEBSOCKET_PORT}/stomp',
			subscription_channel=f'/exchange/{MessageQueueUtils.MQ_TOPIC_EXCHANGE_NAME}/{TOPIC_ROUTING_KEY}',
			downloads_data=url_payloads
		)

	return render_template('index.html')


def is_download_url_valid(url):
	regex = re.compile(
		r'^https?://'  # http:// or https://
		r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
		r'localhost|'  # localhost...
		r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
		r'(?::\d+)?'  # optional port
		r'(?:/?|[/?]\S+)$', re.IGNORECASE)
	return url is not None and regex.search(url)


if __name__ == '__main__':
	app.run(debug=True, port=PORT)
