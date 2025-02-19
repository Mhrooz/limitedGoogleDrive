import easywebdav
import global_value
from config import WEBDAV_URL, WEBDAV_USER, WEBDAV_PASSWORD


webdav_client = easywebdav.connect(WEBDAV_URL, username=WEBDAV_USER, password=WEBDAV_PASSWORD)

def upload_file(file_path):
    """upload files to WebDAV server"""
    try:
        remote_path = '/uploads/' + file_path.split('/')[-1]  # Remote file path
        webdav_client.upload(file_path, remote_path)
        print(f" '{file_path}'  Upload successful!")
    except Exception as e:
        print(f"Sorry file upload failed!：{e}")

def download_file(remote_file_name):
    """download files from WebDAV server"""
    try:
        remote_path = '/downloads/' + remote_file_name  #  Remote file path
        local_path = './' + remote_file_name  #  Local file path
        webdav_client.download(remote_path, local_path)
        print(f" '{remote_file_name}' Download successful!")
    except Exception as e:
        print(f" Sorry file download failed!：{e}")
