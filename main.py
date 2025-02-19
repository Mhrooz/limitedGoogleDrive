import os
import global_value
from db_operations import register, login, logout
from file_operations import upload_file, download_file

def user_menu():
    """file operations for log in users"""
    while global_value.current_user:
        print("1. Upload Files")
        print("2. Download Files")
        print("3. Log out")
        print("4. Exit")

        choice = input("Please select an option:")

        if choice == "1":
            file_path = input("Enter the file path to upload: ")
            upload_file(file_path)

        elif choice == "2":
            remote_file_name = input("Enter the file name to download: ")
            download_file(remote_file_name)

        elif choice == "3":
            logout()
            return  # return to log in

        elif choice == "4":
            print(" See You ")
            exit()

        else:
            print("Invalid choice, please try again")

def main():
    while True:
        if global_value.current_user:
            user_menu()
        else:
            print("\n1. Sign up  2. Log in 3.Exit")
            choice = input("Please select an option:")
            if choice == "1":
               username = input("Enter your username: ")
               password = input("Enter your password: ")
               register(username, password)
            elif choice == "2":
                 username = input("Enter your username: ")
                 password = input("Enter your password: ")
                 login(username, password)

            elif choice == "3":
                 print(" See You ")
                 exit()
            else:
                 print("Invalid choice, please try again")



if __name__ == "__main__":
    main()

