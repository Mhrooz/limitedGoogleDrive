import click
import requests
import webdav3.client as webdav
from rich.console import Console
from rich.table import Table
import json
import os
import jwt

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

            # Print username and roles
            decoded_token = jwt.decode(self.token, options={"verify_signature": False})
            self.roles = decoded_token.get('roles', [])
            console.print(f"Successfully signed in as {username} with roles: {', '.join(self.roles)}", style="green")

            return True
        return False

    def check_permissions(self, allowed_roles):
        if not any(role in self.roles for role in allowed_roles):
            console.print("Permission denied. You do not have the required role to perform this action.", style="red")
            return False
        return True

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
        if not self.check_permissions(["administrator", "user"]):
            return False

        if not self.webdav_client:
            if not self.reconnect():
                console.print("Not connected. Please connect first.", style="red")
                return False

        try:
            # Path handling
            local_path = os.path.expanduser(local_path)
            local_path = os.path.abspath(local_path)
            console.print(f"Looking for file at: {local_path}", style="blue")

            if not os.path.exists(local_path):
                console.print(f"File not found at: {local_path}", style="red")
                console.print(f"Current directory: {os.getcwd()}", style="blue")
                console.print(f"Available files:", style="blue")
                os.system('ls -la')
                return False

            # Get just the filename for remote path
            filename = os.path.basename(local_path)
            if remote_path == "/" or remote_path.endswith('/'):
                remote_path = f"{remote_path.rstrip('/')}/{filename}"

            console.print(f"Uploading to: {remote_path}", style="blue")

            # Try both upload methods
            try:
                self.webdav_client.upload_sync(local_path=local_path, remote_path=remote_path)
            except:
                self.webdav_client.upload(local_path=local_path, remote_path=remote_path)

            console.print(f"Successfully uploaded {local_path}", style="green")
            return True

        except Exception as e:
            console.print(f"Upload error: {str(e)}", style="red")
            return False

    def download_file(self, remote_path, local_path):
        if not self.webdav_client:
            if not self.reconnect():
                console.print("Not connected. Please connect first.", style="red")
                return False

        try:
            # Check if the remote file exists
            if not self.webdav_client.check(remote_path):
                console.print(f"Unable to locate file: {remote_path}", style="red")
                return False

            # Ensure the local directory exists
            local_dir = os.path.dirname(local_path)
            if not os.path.exists(local_dir):
                os.makedirs(local_dir)

            # Download the file
            self.webdav_client.download_sync(remote_path=remote_path, local_path=local_path)
            console.print(f"Successfully downloaded {remote_path} to {local_path}", style="green")
            return True

        except Exception as e:
            console.print(f"Download error: {str(e)}", style="red")
            return False

    def delete_file(self, remote_path):
        if not self.check_permissions(["administrator", "user"]):
            return False

        if not self.webdav_client:
            if not self.reconnect():
                console.print("Not connected. Please connect first.", style="red")
                return False

        try:
            # Check if the remote file exists
            if not self.webdav_client.check(remote_path):
                console.print(f"Unable to locate file: {remote_path}", style="red")
                return False

            # Delete the file
            self.webdav_client.clean(remote_path)
            console.print(f"Successfully deleted {remote_path}", style="green")
            return True

        except Exception as e:
            console.print(f"Delete error: {str(e)}", style="red")
            return False

    def rename_file(self, old_remote_path, new_remote_path):
        if not self.check_permissions(["administrator", "user"]):
            return False

        if not self.webdav_client:
            if not self.reconnect():
                console.print("Not connected. Please connect first.", style="red")
                return False

        try:
            # Check if the old remote file exists
            if not self.webdav_client.check(old_remote_path):
                console.print(f"Unable to locate file: {old_remote_path}", style="red")
                return False

            # Rename the file
            self.webdav_client.move(remote_path_from=old_remote_path, remote_path_to=new_remote_path)
            console.print(f"Successfully renamed {old_remote_path} to {new_remote_path}", style="green")
            return True

        except Exception as e:
            console.print(f"Rename error: {str(e)}", style="red")
            return False

    def create_user(self, new_username, new_password, new_role):
        if not self.check_permissions(["administrator"]):
            return False

        if new_role not in ["administrator", "user", "visitor"]:
            console.print("Invalid role. Role must be one of: administrator, user, visitor.", style="red")
            return False

        url = f"{self.api_url}/create_user"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.token}"}
        data = {
            "username": new_username,
            "password": new_password,
            "roles": [new_role]
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            console.print(f"Successfully created user {new_username} with role {new_role}", style="green")
            return True
        except requests.exceptions.RequestException as e:
            console.print(f"Error creating user: {e}", style="red")
            return False

    def reconnect(self):
        """Try to reconnect using saved credentials"""
        if self.config.get('last_server') and self.config.get('credentials'):
            creds = self.config.get('credentials', {})
            return self.connect(
                self.config['last_server'],
                creds.get('username'),
                creds.get('password')
            )
        return False

    def create_directory(self, remote_path):
        if not self.check_permissions(["administrator", "user"]):
            return False

        if not self.webdav_client:
            if not self.reconnect():
                console.print("Not connected. Please connect first.", style="red")
                return False

        try:
            self.webdav_client.mkdir(remote_path)
            console.print(f"Successfully created directory {remote_path}", style="green")
            return True
        except Exception as e:
            console.print(f"Error creating directory: {str(e)}", style="red")
            return False

    def show_user_info(self):
        if not self.token:
            console.print("Not connected. Please connect first.", style="red")
            return

        decoded_token = jwt.decode(self.token, options={"verify_signature": False})
        username = decoded_token.get('user', 'Unknown')
        roles = decoded_token.get('roles', [])

        allowed_functions = []
        if "administrator" in roles:
            allowed_functions = ["connect", "ls", "upload", "download", "delete", "rename", "create_user", "create_directory"]
        elif "user" in roles:
            allowed_functions = ["connect", "ls", "upload", "download", "delete", "rename", "create_directory"]
        elif "visitor" in roles:
            allowed_functions = ["connect", "ls", "download"]

        console.print(f"Username: {username}", style="green")
        console.print(f"Roles: {', '.join(roles)}", style="green")
        console.print(f"Allowed Functions: {', '.join(allowed_functions)}", style="green")

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
    # Show current working directory and file location
    console.print(f"Current directory: {os.getcwd()}", style="blue")
    console.print(f"Attempting to upload: {local_path}", style="blue")
    client.upload_file(local_path, remote_path)

@cli.command()
@click.pass_obj
@click.argument('remote_path')
@click.argument('local_path', type=click.Path())
def download(client, remote_path, local_path):
    """Download a file from the server.
    REMOTE_PATH is the path to the file on the server
    LOCAL_PATH is the destination path on your computer
    """
    client.download_file(remote_path, local_path)

@cli.command()
@click.pass_obj
@click.argument('remote_path')
def delete(client, remote_path):
    """Delete a file from the server.
    REMOTE_PATH is the path to the file on the server
    """
    client.delete_file(remote_path)

@cli.command()
@click.pass_obj
@click.argument('old_remote_path')
@click.argument('new_remote_path')
def rename(client, old_remote_path, new_remote_path):
    """Rename a file on the server.
    OLD_REMOTE_PATH is the current path to the file on the server
    NEW_REMOTE_PATH is the new path to the file on the server
    """
    client.rename_file(old_remote_path, new_remote_path)

@cli.command()
@click.pass_obj
@click.argument('new_username')
@click.argument('new_password')
@click.argument('new_role')
def create_user(client, new_username, new_password, new_role):
    """Create a new user.
    NEW_USERNAME is the username for the new user
    NEW_PASSWORD is the password for the new user
    NEW_ROLE is the role for the new user (administrator, user, visitor)
    """
    client.create_user(new_username, new_password, new_role)

@cli.command()
@click.pass_obj
@click.argument('remote_path')
def create_directory(client, remote_path):
    """Create a new directory on the server.
    REMOTE_PATH is the path to the new directory on the server
    """
    client.create_directory(remote_path)

@cli.command()
@click.pass_obj
def show_user_info(client):
    """Show user information including username, roles, and allowed functions."""
    client.show_user_info()

if __name__ == '__main__':
    cli()