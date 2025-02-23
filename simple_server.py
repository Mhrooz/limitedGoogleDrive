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

app = Flask(__name__)
api = Api(app)

# Auth configuration
SECRET_KEY = 'your-secret-key'
USERS = {
    'admin': {'password': 'admin123', 'roles': ['administrator']},
    'user': {'password': 'user123', 'roles': ['user']}
}

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
        return jsonify({"token": token}), 200
    
    return jsonify({"error": "Invalid credentials"}), 401

if __name__ == '__main__':
    print("Starting WebDAV server...")
    webdav_thread = threading.Thread(target=start_webdav)
    webdav_thread.daemon = True
    webdav_thread.start()
    
    print("Starting main server...")
    app.run(host='0.0.0.0', port=8080, debug=True, threaded=True)
