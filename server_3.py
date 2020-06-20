from flask import Flask, request, jsonify
from http import HTTPStatus
from utils import MessageQueueUtils

import os
import json
import requests
from zipfile import ZipFile, ZIP_DEFLATED
from threading import Thread

app = Flask(__name__)
PORT = 3032
TOPIC_ROUTING_KEY = "law-1606875806-server2-topic"
COMPRESSED_FILE_DIR = "./server_3_compressed"
FILENAMES_TO_BE_COMPRESSED_PAYLOAD = []
SERVER_4_URL = "http://localhost:3034/"


@app.route('/', methods=['GET', 'POST'])
def handle_uploads():
	if request.method == 'POST':
		if 'file_1' not in list(dict(request.files).keys()):
			return jsonify({
				"Error": "File payload empty!"
			}), HTTPStatus.BAD_REQUEST

		for key in list(dict(request.files).keys()):
			downloaded_file = request.files[key]
			downloaded_file.save(generate_path(downloaded_file.filename))
			FILENAMES_TO_BE_COMPRESSED_PAYLOAD.append(str(downloaded_file.filename))

		compress_file_in_background(file_names_list=FILENAMES_TO_BE_COMPRESSED_PAYLOAD)

		return jsonify({
			"Status": "Compression Successful!"
		}), HTTPStatus.OK


def generate_path(file_name):
	return os.path.join(COMPRESSED_FILE_DIR, file_name)


def compress(file_names_list):
	zipped_file_path = generate_path("compressed.zip")
	zip_output = ZipFile(zipped_file_path, mode='w')
	for file_name in file_names_list:
		try:
			file_path = generate_path(file_name)
			zip_output.write(file_path, file_name, compress_type=ZIP_DEFLATED)
		except FileNotFoundError as e:
			print(f"ERROR - File with path {file_name} not found!")
			raise e
		finally:
			os.remove(file_path)
	zip_output.close()


def get_folder_size(folder_path):
	total_size = 0
	for dir_path, dir_names, file_names in os.walk(folder_path):
		for f in file_names:
			file_path = os.path.join(dir_path, f)
			if not os.path.islink(file_path):
				total_size += os.path.getsize(file_path)
	return total_size


def compress_file_in_background(file_names_list):
	total_files_size_unzipped = get_folder_size(COMPRESSED_FILE_DIR)
	mq_object = MessageQueueUtils(
		routing_key=TOPIC_ROUTING_KEY,
		exchange_mode=MessageQueueUtils.MQ_TOPIC_EXCHANGE_TYPE
	)
	background_thread = Thread(target=compress, args=(file_names_list,))
	background_thread.start()
	while background_thread.is_alive():
		compressed_file_path = generate_path("compressed.zip")
		if os.path.isfile(compressed_file_path):
			current_size = os.path.getsize(compressed_file_path)
			mq_object.send_message(f"Compression Progress: {(current_size/total_files_size_unzipped)*100.0}%")

	mq_object.send_message("Compression completed!")
	server_4_request = requests.post(
		SERVER_4_URL,
		files={
			'file': open(generate_path("compressed.zip"), 'rb')
		}
	)

	if server_4_request.status_code == HTTPStatus.OK:
		mq_object.send_message(f"Secure URL generated. Download it here: {dict(server_4_request.json())['secure_link']}")
	else:
		mq_object.send_message("Secure URL failed to generate, please try again!")

	mq_object.close_connection()


if __name__ == '__main__':
	os.system(f'mkdir -p {COMPRESSED_FILE_DIR}')
	app.run(debug=True, port=PORT)
