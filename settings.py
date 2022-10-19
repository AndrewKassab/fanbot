from dotenv import load_dotenv
import os
import mysql.connector
import logging

load_dotenv()


logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s;%(levelname)s;%(message)s")

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
LIST_COMMAND = "listroles"
HELP_COMMAND = "help"

# Emojis
FOLLOW_ROLE_EMOJI = '✅'
UNFOLLOW_ROLE_EMOJI = '❌'

HELP_MESSAGE = f"Hello, I am fanbot! Your ultimate music fanboy. I can allow your server to follow music artists on " \
               f"Spotify and create a role to ping whenever that artist releases new music!\n\n__**Commands**__\n\n" \
               f"/{SET_COMMAND}: Admin only, configures the channel that releases will be sent to.\n\n/" \
               f"{FOLLOW_COMMAND} artist_profile_link: Follows an artist for a server by providing their spotify " \
               f"share link. This then creates a role with the artists name followed by Fan and assigns it to the " \
               f"person who sent the command, while others can react to assign. (To limit this to a certain role" \
               f", manage the integration in your server settings)\n\n/{LIST_COMMAND}: This will produce an " \
               f"invisible select menu and pageable dropdown that allows members to assign themselves to " \
               f"existing artist fan roles.\n\nTo unfollow and artist and stop pinging their releases, just " \
               f"delete their respective role from the server."

