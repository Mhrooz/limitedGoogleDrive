import click
import requests
import webdav3.client as webdav
from rich.console import Console
from rich.table import Table
import json
import os

console = Console()

class Client:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Client, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if not self.initialized:
            self.config_file = 'client_config.json'
            self.api_url = None
            self.webdav_url = None
            self.token = None
            self.webdav_client = None
            self.load_config()
            self.initialized = True
            # Auto-connect if we have last server and credentials
            if self.config.get('last_server') and self.config.get('credentials'):
                creds = self.config['credentials']
                self.connect(
                    self.config['last_server'],
                    creds.get('username'),
                    creds.get('password')
                )

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

    def upload_file(self, local_path, remote_path="/"):
        if not self.webdav_client:
            console.print("Not connected. Please connect first.", style="red")
            return False
        
        try:
            # Ensure local file exists
            if not os.path.exists(local_path):
                console.print(f"Local file {local_path} not found", style="red")
                return False

            # Get just the filename if remote_path is a directory
            if remote_path.endswith('/'):
                remote_path = remote_path + os.path.basename(local_path)

            with console.status(f"Uploading {local_path} to {remote_path}..."):
                self.webdav_client.upload_file(local_path, remote_path)
            console.print(f"Successfully uploaded {local_path}", style="green")
            return True
        except Exception as e:
            console.print(f"Error uploading file: {e}", style="red")
            return False

@click.group()
@click.pass_context
def cli(ctx):
    ctx.obj = Client()

@cli.command()
@click.pass_obj
def connect(client):
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
@click.pass_obj
@click.argument('path', default="/")
def ls(client, path):
    client.list_files(path)

@cli.command()
@click.pass_obj
@click.argument('local_path', type=click.Path(exists=True))
@click.argument('remote_path', default="/")
def upload(client, local_path, remote_path):
    """Upload a file to the server.
    LOCAL_PATH is the path to the file on your computer
    REMOTE_PATH is the destination path on the server (default: /)
    """
    client.upload_file(local_path, remote_path)

if __name__ == '__main__':
    cli()
