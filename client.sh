#!/bin/bash

# Function to connect to the server
nas_connect() {
    python client.py connect
}

# Function to list files
nas_ls() {
    local path="$1"
    python client.py ls "$path"
}

# Function to upload a file
nas_upload() {
    local local_path="$1"
    local remote_path="$2"
    python client.py upload "$local_path" "$remote_path"
}

# Function to download a file
nas_download() {
    local remote_path="$1"
    local local_path="$2"
    python client.py download "$remote_path" "$local_path"
}

# Function to delete a file
nas_delete() {
    local remote_path="$1"
    python client.py delete "$remote_path"
}

# Function to rename a file
nas_rename() {
    local old_remote_path="$1"
    local new_remote_path="$2"
    python client.py rename "$old_remote_path" "$new_remote_path"
}

# Function to create a new user (admin only)
nas_create_user() {
    local new_username="$1"
    local new_password="$2"
    local new_role="$3"
    python client.py create_user "$new_username" "$new_password" "$new_role"
}

# Function to create a new directory
nas_create_directory() {
    local remote_path="$1"
    python client.py create_directory "$remote_path"
}

# Function to show user information
nas_show_user_info() {
    python client.py show_user_info
}

# Main script to handle commands
case "$1" in
    connect)
        nas_connect
        ;;
    ls)
        nas_ls "$2"
        ;;
    upload)
        nas_upload "$2" "$3"
        ;;
    download)
        nas_download "$2" "$3"
        ;;
    delete)
        nas_delete "$2"
        ;;
    rename)
        nas_rename "$2" "$3"
        ;;
    create_user)
        nas_create_user "$2" "$3" "$4"
        ;;
    create_directory)
        nas_create_directory "$2"
        ;;
    show_user_info)
        nas_show_user_info
        ;;
    *)
        echo "Usage: $0 {connect|ls|upload|download|delete|rename|create_user|create_directory|show_user_info}"
        ;;
esac
