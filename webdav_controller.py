import os
from wsgidav.wsgidav_app import WsgiDAVApp
from wsgidav.fs_dav_provider import FilesystemProvider
from wsgidav.dir_browser import WsgiDavDirBrowser
from cheroot import wsgi
import threading

class WebDAVController:
    def __init__(self, port=8001):
        self.port = port
        self.config = {
            "host": "0.0.0.0",
            "port": self.port,
            "provider_mapping": {
                "/": FilesystemProvider("./shared"),
            },
            "simple_dc": {
                "user_mapping": {
                    "*": {  # Root folder
                        "admin": {"password": "admin123"},
                        "user": {"password": "user123"},
                    }
                }
            },
            "dir_browser": {
                "enable": True,
                "response_handler": WsgiDavDirBrowser,
            },
            "verbose": 1,
        }
        
        # Create shared directory if it doesn't exist
        if not os.path.exists("./shared"):
            os.makedirs("./shared")
            
    def start(self):
        app = WsgiDAVApp(self.config)
        server = wsgi.Server(
            (self.config["host"], self.config["port"]),
            app,
            server_name="WebDAV Server"
        )
        server_thread = threading.Thread(target=server.start)
        server_thread.daemon = True
        server_thread.start()
