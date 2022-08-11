from dotenv import load_dotenv
import os
import mysql.connector

load_dotenv()

# Database
db = mysql.connector

# Environment Variables
DB_HOST = os.environ.get("DB_HOST")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_NAME = os.environ.get("DB_NAME")
SP_CLIENT_ID = os.environ.get("SP_CLIENT_ID")
SP_CLIENT_SECRET = os.environ.get("SP_CLIENT_SECRET")
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")

# Slash Command names
SET_COMMAND = "setchannel"
FOLLOW_COMMAND = "follow"
LIST_COMMAND = "listfollow"

# Emojis
FOLLOW_ROLE_EMOJI = '✅'
UNFOLLOW_ROLE_EMOJI = '❌'