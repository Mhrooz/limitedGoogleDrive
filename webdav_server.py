from flask import Flask, request, jsonify
from flask_restful import Api
import os
from wsgidav.wsgidav_app import WsgiDAVApp
from wsgidav.fs_dav_provider import FilesystemProvider
from wsgidav.dir_browser import WsgiDavDirBrowser
from cheroot import wsgi
import threading
import jwt
import datetime
import requests
import json

app = Flask(__name__)
api = Api(app)

# Load users from accounts.json
with open('accounts.json') as f:
    USERS = json.load(f)

# Auth configuration
SECRET_KEY = 'your-secret-key'

# WebDAV configuration
WEBDAV_PORT = 8001
SHARE_DIR = "./shared"

def start_webdav():
    if not os.path.exists(SHARE_DIR):
        os.makedirs(SHARE_DIR)

    config = {
        "host": "0.0.0.0",
        "port": WEBDAV_PORT,
        "provider_mapping": {
            "/": FilesystemProvider(SHARE_DIR)
        },
        "simple_dc": {
            "user_mapping": {
                "*": USERS  # Use same users as main app
            }
        },
        "dir_browser": {
            "enable": True,
            "response_handler": WsgiDavDirBrowser,
        },
        "verbose": 1,
    }

    app = WsgiDAVApp(config)
    server = wsgi.Server(
        (config["host"], config["port"]),
        app,
        server_name="WebDAV Server"
    )
    server.start()

def set_bandwidth_for_role(user_ip, role):
    url = f"http://192.168.0.22:8080/bandwidth"
    headers = {"Content-Type": "application/json"}
    if role == "administrator":
        data = {
            "src_ip": user_ip,
            "dst_ip": "0.0.0.0/0",
            "rates": [[1000000, 1000000], [1000000, 1000000]],  # No limit
            "dst_port": "0"
        }
    elif role == "user":
        data = {
            "src_ip": user_ip,
            "dst_ip": "0.0.0.0/0",
            "rates": [[12500, 12500], [12500, 12500]],  # Limited to 100 Kbps
            "dst_port": "0"
        }
    elif role == "visitor":
        data = {
            "src_ip": user_ip,
            "dst_ip": "0.0.0.0/0",
            "rates": [[0, 12500], [0, 12500]],  # Download only
            "dst_port": "0"
        }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error setting bandwidth: {e}")
        return {"error": str(e)}

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if username in USERS and USERS[username]['password'] == password:
        token = jwt.encode({
            'user': username,
            'roles': USERS[username]['roles'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, SECRET_KEY)
        
        # Set bandwidth based on user role
        user_ip = request.remote_addr
        for role in USERS[username]['roles']:
            set_bandwidth_for_role(user_ip, role)
        
        return jsonify({"token": token}), 200

    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/create_user', methods=['POST'])
def create_user():
    data = request.get_json()
    new_username = data.get('username')
    new_password = data.get('password')
    new_roles = data.get('roles')

    if not new_username or not new_password or not new_roles:
        return jsonify({"error": "Missing required fields: username, password, roles"}), 400

    if new_username in USERS:
        return jsonify({"error": "User already exists"}), 409

    USERS[new_username] = {
        "password": new_password,
        "roles": new_roles
    }

    # Save the updated users to the accounts.json file
    with open('accounts.json', 'w') as f:
        json.dump(USERS, f, indent=4)

    return jsonify({"message": f"User {new_username} created successfully"}), 201

if __name__ == '__main__':
    print("Starting WebDAV server...")
    webdav_thread = threading.Thread(target=start_webdav)
    webdav_thread.daemon = True
    webdav_thread.start()

    print("Starting main server...")
    app.run(host='0.0.0.0', port=8080, debug=True, threaded=True)