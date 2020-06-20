from flask import Flask, request, jsonify
from http import HTTPStatus

import os
import base64
import hashlib
import calendar
import datetime


app = Flask(__name__)
PORT = 3034
STORED_FILE_DIR = "./server_4_stored"


@app.route('/', methods=['GET', 'POST'])
def handle_generate_url():
	if request.method == 'POST':
		compressed_uploaded_file = request.files['file']
		compressed_uploaded_file.save(generate_path(compressed_uploaded_file.filename))
		secure_url = generate_secure_url(
			file_name=compressed_uploaded_file.filename,
			nginx_install_location="/usr/local/nginx",
			nginx_host="127.0.0.1",
			nginx_port="80"
		)

		return jsonify({
			"status": "Generate Secure Link Success!",
			"secure_link": secure_url
		}), HTTPStatus.OK

	return jsonify({
		"error": "No parameters specified!"
	}), HTTPStatus.BAD_REQUEST


def generate_path(file_name):
	return os.path.join(STORED_FILE_DIR, file_name)


def generate_secure_url(file_name, nginx_install_location, nginx_host, nginx_port):
	secret = "enigma"
	file_path = generate_path(file_name)

	# Do command `export MY_SUDO_PASS=<your_user_password> first!`
	os.system(f"echo $MY_SUDO_PASS | sudo -S mkdir -p {nginx_install_location}/html/compressed")
	os.system(f"echo $MY_SUDO_PASS | sudo -S cp {file_path} {nginx_install_location}/html/compressed")

	url = f"/compressed/{file_name}"

	future = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
	expiry = calendar.timegm(future.timetuple())

	secure_link = f"{secret}{url}{expiry}".encode("utf-8")
	hash = hashlib.md5(secure_link).digest()
	base64_hash = base64.urlsafe_b64encode(hash)
	str_hash = base64_hash.decode('utf-8').rstrip('=')

	return f"http://{nginx_host}:{nginx_port}{url}?st={str_hash}&e={expiry}"


if __name__ == "__main__":
	os.system(f'mkdir -p {STORED_FILE_DIR}')
	app.run(debug=True, port=PORT)
