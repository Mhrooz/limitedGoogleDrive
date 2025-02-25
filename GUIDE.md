# GUIDE: Setting Up the Server and Client

This guide provides step-by-step instructions on how to set up the server and client for the Limited Google Drive project. It also lists the dependencies that need to be installed.

## Prerequisites

Ensure you have the following installed on your system:
- Python 3.x
- Git

## Step 1: Clone the Repository

Clone the project repository to your local machine:

```bash
git clone https://github.com/Mhrooz/limitedGoogleDrive.git 
cd limitedGoogleDrive
```

## Step 2: Install Dependencies

### Server Dependencies

Install the required dependencies for the server:

```bash
pip install Flask Flask-RESTful WsgiDAV cheroot PyJWT requests
```

### Client Dependencies

Install the required dependencies for the client:

```bash
pip install click requests webdavclient3 rich PyJWT
```

### Network Control Dependencies

Install additional dependencies for P4 and Mininet:

```bash
pip install scapy protobuf ipaddr p4utils
sudo apt-get install mininet
```

## Step 3: Set up the Network Control

Follow the How_to_use_network_control.md guide

## Step 4: Set Up the Server

Navigate to the project directory and start the Webdav server:

```bash
cd ~/limitedGoogleDrive
python3 webdav_server.py
```

In a separate terminal, start the Network Control server:

```bash
python3 main.py
```

## Step 5: Set Up the Client

Navigate to the project directory and use the client script to interact with the server:

```bash
cd ~/limitedGoogleDrive
./client.sh connect
```

## Step 6: Using the Client

### Connect to the Server

```bash
./client.sh connect
```

### List Files

```bash
./client.sh ls /path/to/directory
```

Default path is 
```bash
./client.sh ls
```

### Upload a File

```bash
./client.sh upload /path/to/local/file /path/to/remote/directory
```

### Download a File

```bash
./client.sh download /path/to/remote/file /path/to/local/directory
```

### Delete a File

```bash
./client.sh delete /path/to/remote/file
```

### Rename a File

```bash
./client.sh rename /path/to/old/remote/file /path/to/new/remote/file
```

### Create a New User (Admin Only)

```bash
./client.sh create_user new_username new_password new_role
```

### Create a New Directory

```bash
./client.sh create_directory /path/to/new/directory
```

### Show User Information

```bash
./client.sh show_user_info
```

## Summary

By following these steps, you can set up the server and client for the Limited Google Drive project and interact with the system using the provided CLI commands.