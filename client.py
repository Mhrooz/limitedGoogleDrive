import click
import requests
import os
import webdav3.client as webdav
from rich.console import Console
from rich.table import Table

console = Console()

class Client:
    def __init__(self):
        self.api_url = None
        self.webdav_url = None
        self.token = None
        self.webdav_client = None

    def connect(self, ip):
        self.api_url = f"http://{ip}:8080"
        self.webdav_url = f"http://{ip}:8001"

    def login(self, username, password):
        response = requests.post(f"{self.api_url}/login", 
                               json={"username": username, "password": password})
        if response.status_code == 200:
            self.token = response.json()["token"]
            self._setup_webdav(username, password)
            return True
        return False

    def _setup_webdav(self, username, password):
        options = {
            'webdav_hostname': self.webdav_url,
            'webdav_login': username,
            'webdav_password': password
        }
        self.webdav_client = webdav.Client(options)

    def _get_headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    # File operations
    def list_files(self, path="/"):
        if not self.webdav_client:
            console.print("Not authenticated", style="red")
            return
        files = self.webdav_client.list(path)
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name")
        table.add_column("Type")
        table.add_column("Size")
        for file in files:
            table.add_row(
                file["name"],
                "DIR" if file["isdir"] else "FILE",
                str(file["size"]) if not file["isdir"] else ""
            )
        console.print(table)

    # Policy operations with authentication
    def get_policies(self):
        response = requests.get(f"{self.api_url}/policies", headers=self._get_headers())
        return self._handle_response(response)

    def add_policy(self, src_ip, dst_ip, action):
        data = {"src_ip": src_ip, "dst_ip": dst_ip, "action": action}
        response = requests.post(f"{self.api_url}/policies", 
                               json=data, headers=self._get_headers())
        return self._handle_response(response)

    def _handle_response(self, response):
        if response.status_code == 401:
            console.print("Authentication required. Please login first.", style="red")
            return None
        elif response.status_code == 403:
            console.print("Insufficient permissions.", style="red")
            return None
        return response.json()

@click.group()
def cli():
    pass

@cli.command()
def connect():
    client = Client()
    ip = click.prompt("Enter NAS IP")
    client.connect(ip)
    username = click.prompt("Username")
    password = click.prompt("Password", hide_input=True)
    if client.login(username, password):
        console.print("Connected and authenticated!", style="green")
    else:
        console.print("Connection failed!", style="red")

@cli.command()
@click.argument('path', default="/")
def ls(path):
    client = Client()
    client.list_files(path)

if __name__ == '__main__':
    cli()
