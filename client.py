import click
import requests
import os
import webdav3.client as webdav
from rich.console import Console
from rich.table import Table

console = Console()

class Client:
    def __init__(self):
        self.api_url = "http://localhost:8080"
        self.webdav_url = "http://localhost:8001"
        self.token = None
        self.webdav_client = None

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

    def list_files(self, path="/"):
        if not self.webdav_client:
            console.print("Not authenticated", style="red")
            return
        
        files = self.webdav_client.list(path)
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Type")
        table.add_column("Name")
        table.add_column("Size")
        
        for file in files:
            table.add_row(
                "DIR" if file.is_dir() else "FILE",
                file.name,
                str(file.size) if not file.is_dir() else ""
            )
        console.print(table)

@click.group()
def cli():
    pass

@cli.command()
@click.option('--username', prompt=True)
@click.option('--password', prompt=True, hide_input=True)
def login(username, password):
    client = Client()
    if client.login(username, password):
        console.print("Login successful!", style="green")
    else:
        console.print("Login failed!", style="red")

@cli.command()
@click.argument('path', default="/")
def ls(path):
    client = Client()
    client.list_files(path)

if __name__ == '__main__':
    cli()
