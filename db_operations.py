import sqlite3
import global_value

# Connect to the database (create if it doesn't exist)
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# create database for user_table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")
conn.commit()

def register(username, password):
    """sign up"""
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        print(" Registration successful!")
    except sqlite3.IntegrityError:
        print("Username already exists, please choose another username.")

def login(username, password):
    """user log in"""
    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    record = cursor.fetchone()
    if record and record[0] == password:
        global_value.current_user = username
        print(" Welcome to the NAS file management system!")
        return True
    else:
        print(" Incorrect username or password!")
        return False

def logout():
    """user log out"""
    if global_value.current_user:
        print(f" {global_value.current_user} has successfully logged out!")
        global_value.current_user = None  #  Clear the current session
    else:
        print("No user is logged in now")



