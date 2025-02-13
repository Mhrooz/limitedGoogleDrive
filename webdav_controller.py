from wsgidav.wsgidav_app import WsgiDAVApp
from wsgidav.fs_dav_provider import FilesystemProvider
import threading
from wsgiref.simple_server import make_server
import os

class WebDAVController:
    def __init__(self, host="0.0.0.0", port=8001):
        self.host = host
        self.port = port
        self.base_path = os.path.join(os.path.dirname(__file__), "shared")
        os.makedirs(self.base_path, exist_ok=True)
        
        self.config = {
            "host": host,
            "port": port,
            "provider_mapping": {
                "/": FilesystemProvider(self.base_path)
            },
            "simple_dc": {
                "user_mapping": {
                    "*": True  # Allow all users for now, will be restricted by P4
                }
            },
            "verbose": 1,
        }
        
        self.app = WsgiDAVApp(self.config)
        self.server = make_server(host, port, self.app)
        self.server_thread = None

    def start(self):
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()

    def stop(self):
        if self.server:
            self.server.shutdown()
