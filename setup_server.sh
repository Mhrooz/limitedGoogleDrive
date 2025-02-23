#!/bin/bash

# Install system dependencies
apt-get update
apt-get install -y python3-pip protobuf-compiler git

# Upgrade pip
pip3 install --upgrade pip

# Install Python packages
pip3 install -r requirements_server.txt

# Generate P4 protobuf files
python3 generate_protos.py

echo "Setup complete! You can now run main.py"
