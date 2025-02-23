import click
import requests
import webdav3.client as webdav
from rich.console import Console
from rich.table import Table
import json

console = Console()

class Client:
    def __init__(self):
        self.config_file = 'client_config.json'
        self.api_url = None
        self.webdav_url = None
        self.token = None
        self.webdav_client = None
        self.load_config()

    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = {
                'last_server': None,
                'credentials': {'username': None, 'password': None}
            }

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    def connect(self, server_ip, username, password):
        self.api_url = f"http://{server_ip}:8080"
        self.webdav_url = f"http://{server_ip}:8001"
        
        # Try to login
        response = requests.post(
            f"{self.api_url}/login",
            json={"username": username, "password": password}
        )
        
        if response.status_code == 200:
            self.token = response.json()["token"]
            self.setup_webdav(username, password)
            self.config['last_server'] = server_ip
            self.config['credentials'] = {'username': username, 'password': password}
            self.save_config()
            return True
        return False

    def setup_webdav(self, username, password):
        options = {
            'webdav_hostname': self.webdav_url,
            'webdav_login': username,
            'webdav_password': password
        }
        self.webdav_client = webdav.Client(options)

    def list_files(self, path="/"):
        if not self.webdav_client:
            console.print("Not connected. Please connect first.", style="red")
            return
        
        try:
            files = self.webdav_client.list(path)
            table = Table(title="Files", show_header=True)
            table.add_column("Name")
            table.add_column("Type")
            
            for file in files:
                name = file
                file_type = "DIR" if self.webdav_client.is_dir(file) else "FILE"
                table.add_row(name, file_type)
            
            console.print(table)
        except Exception as e:
            console.print(f"Error listing files: {e}", style="red")

@click.group()
def cli():
    pass

@cli.command()
def connect():
    client = Client()
    
    # Check for last server
    last_server = client.config.get('last_server')
    if last_server:
        use_last = click.prompt(
            f"Use last server {last_server}? [y/N]",
            default='n'
        )
        if use_last.lower() == 'y':
            last_creds = client.config.get('credentials', {})
            if client.connect(
                last_server,
                last_creds.get('username'),
                last_creds.get('password')
            ):
                console.print("Connected successfully!", style="green")
                return
    
    # New connection
    server_ip = click.prompt("Server IP")
    username = click.prompt("Username")
    password = click.prompt("Password", hide_input=True)
    
    if client.connect(server_ip, username, password):
        console.print("Connected successfully!", style="green")
    else:
        console.print("Connection failed!", style="red")

@cli.command()
@click.argument('path', default="/")
def ls(path):
    client = Client()
    client.list_files(path)

if __name__ == '__main__':
    cli()
