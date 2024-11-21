import telebot
from telebot import types
import os
import sqlite3
from datetime import datetime

API_TOKEN = '7220128060:AAG85w8zxA1t2sagr15iiElAUHSiiJVst7s'
bot = telebot.TeleBot(API_TOKEN)



# Paths for database and file storage
DB_PATH = "/teleg1/users.db"  # Replace with your desired server path
FILES_DIR = "/teleg1/uploads"  # Replace with your desired server path

# Ensure file storage directory exists
os.makedirs(FILES_DIR, exist_ok=True)

# Initialize database
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Create tables for users and uploads
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        email TEXT,
        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS uploads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        competition_title TEXT,
        file_name TEXT,
        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )''')
    conn.commit()
    conn.close()

init_db()

# Bot command and message handlers

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(row_width=2)
    register_btn = types.KeyboardButton('Register')
    profile_btn = types.KeyboardButton('Profile')
    upload_btn = types.KeyboardButton('Upload Files')
    status_btn = types.KeyboardButton('Check Status')
    markup.add(register_btn, profile_btn, upload_btn, status_btn)
    bot.send_message(chat_id, "Welcome! Please choose an option:", reply_markup=markup)

# Registration, upload, and profile features remain unchanged...



@bot.message_handler(func=lambda message: message.text == 'Register')
def register(message):
    chat_id = message.chat.id
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (chat_id,))
    user = cursor.fetchone()
    if user:
        bot.send_message(chat_id, "You are already registered.")
    else:
        bot.send_message(chat_id, "Please provide your username.")
        bot.register_next_step_handler(message, register_username)
    conn.close()

def register_username(message):
    chat_id = message.chat.id
    username = message.text
    bot.send_message(chat_id, "Please provide your email.")
    bot.register_next_step_handler(message, register_email, username)

def register_email(message, username):
    chat_id = message.chat.id
    email = message.text
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (user_id, username, email) VALUES (?, ?, ?)",
                   (chat_id, username, email))
    conn.commit()
    conn.close()
    bot.send_message(chat_id, "You are now registered!")

@bot.message_handler(func=lambda message: message.text == 'Profile')
def profile(message):
    chat_id = message.chat.id
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT username, email FROM users WHERE user_id = ?", (chat_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        bot.send_message(chat_id, f"Username: {user[0]}\nEmail: {user[1]}")
    else:
        bot.send_message(chat_id, "You are not registered. Please use the 'Register' button to sign up.")

@bot.message_handler(func=lambda message: message.text == 'Upload Files')
def upload_files(message):
    chat_id = message.chat.id
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (chat_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        bot.send_message(chat_id, "Please enter the competition title:")
        bot.register_next_step_handler(message, receive_competition_title)
    else:
        bot.send_message(chat_id, "You need to register first. Please use the 'Register' button.")

def receive_competition_title(message):
    chat_id = message.chat.id
    competition_title = message.text
    bot.send_message(chat_id, "Now, please upload your ZIP file max 50MB.")
    bot.register_next_step_handler(message, handle_docs, competition_title)

@bot.message_handler(content_types=['document'])
def handle_docs(message, competition_title):
    chat_id = message.chat.id
    if message.document.mime_type == 'application/zip':
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        user_dir = os.path.join(FILES_DIR, str(chat_id))
        os.makedirs(user_dir, exist_ok=True)

        file_name = f"{competition_title}_{message.document.file_name}"
        file_path = os.path.join(user_dir, file_name)
        with open(file_path, "wb") as f:
            f.write(downloaded_file)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO uploads (user_id, competition_title, file_name) VALUES (?, ?, ?)",
                       (chat_id, competition_title, file_name))
        conn.commit()
        conn.close()

        bot.reply_to(message, "File uploaded successfully!")
    else:
        bot.reply_to(message, "Only ZIP files are allowed.")

@bot.message_handler(func=lambda message: message.text == 'Check Status')
def check_status(message):
    chat_id = message.chat.id
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT competition_title, file_name, upload_date FROM uploads WHERE user_id = ?", (chat_id,))
    uploads = cursor.fetchall()
    conn.close()
    if uploads:
        response = "Your uploads:\n" + "\n".join([f"{u[0]}: {u[1]} (Uploaded on {u[2]})" for u in uploads])
    else:
        response = "No submissions found."
    bot.send_message(chat_id, response)




# Admin chat ID
ADMIN_CHAT_ID = '6286579149'  # Replace with your admin Telegram ID
# --- Admin Panel Features ---

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    chat_id = message.chat.id
    print(f"Admin Panel accessed by: {chat_id}")
    if str(chat_id) == ADMIN_CHAT_ID:
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        view_users_btn = types.KeyboardButton('View Users')
        view_uploads_btn = types.KeyboardButton('View Uploads')
        download_btn = types.KeyboardButton('Download File')
        announce_btn = types.KeyboardButton('Announce')
        markup.add(view_users_btn, view_uploads_btn, download_btn, announce_btn)

        print("Admin markup Created")
        bot.send_message(chat_id, "Admin Panel", reply_markup=markup)
    else:
        bot.send_message(chat_id, "You are not authorized to access the admin panel")

@bot.message_handler(func=lambda message: message.text == 'View Users' and str(message.chat.id) == ADMIN_CHAT_ID)
def view_users(message):
    chat_id = message.chat.id
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, email, registration_date FROM users")
    users = cursor.fetchall()
    conn.close()
    if users:
        user_list = "Registered Users:\n"
        for user in users:
            user_list += f"ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Registered on: {user[3]}\n"
    else:
        user_list = "No registered users."
    bot.send_message(chat_id, user_list)

@bot.message_handler(func=lambda message: message.text == 'View Uploads' and str(message.chat.id) == ADMIN_CHAT_ID)
def view_uploads(message):
    chat_id = message.chat.id
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT u.id, u.user_id, u.competition_title, u.file_name, u.upload_date, us.username "
                   "FROM uploads u INNER JOIN users us ON u.user_id = us.user_id")
    uploads = cursor.fetchall()
    conn.close()
    if uploads:
        upload_list = "User Uploads:\n"
        for upload in uploads:
            upload_list += (f"Upload ID: {upload[0]}, User ID: {upload[1]}, Username: {upload[5]}, "
                            f"Title: {upload[2]}, File: {upload[3]}, Uploaded on: {upload[4]}\n")
    else:
        upload_list = "No uploads found."
    bot.send_message(chat_id, upload_list)

@bot.message_handler(func=lambda message: message.text == 'Download File' and str(message.chat.id) == ADMIN_CHAT_ID)
def request_file_id(message):
    bot.send_message(message.chat.id, "Please enter the Upload ID of the file you want to download.")
    bot.register_next_step_handler(message, download_file)

def download_file(message):
    upload_id = message.text.strip()
    print(f"Requestd Upload ID: {upload_id}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT file_name FROM uploads WHERE id = ?", (upload_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        file_name = result[0]
        file_path = os.path.join(FILES_DIR, file_name)
        print(f"File path resolved: {file_path}")  # Debug log

        if os.path.exists(file_path):
            with open(file_path, 'rb') as file:
                bot.send_document(message.chat.id, file)
                print(f"File {file_name} sent to admin.")  # Debug log
        else:
            print(f"File not found on server: {file_path}")  # Debug log
            bot.send_message(message.chat.id, "File not found on the server.")
    else:
        print("No record found for the given Upload ID.")  # Debug log
        bot.send_message(message.chat.id, "Invalid Upload ID.")

@bot.message_handler(func=lambda message: message.text == 'Announce' and str(message.chat.id) == ADMIN_CHAT_ID)
def announce(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Please enter the announcement message.")
    bot.register_next_step_handler(message, send_announcement)

def send_announcement(message):
    announcement = message.text
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    user_ids = cursor.fetchall()
    conn.close()
    for user_id in user_ids:
        bot.send_message(user_id[0], f"Announcement: {announcement}")
    bot.send_message(ADMIN_CHAT_ID, "Announcement sent to all users.")

# Bot polling
bot.polling()
