"""
Configuration for Brawl Stars Telegram Bot
"""
import os

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = "8670029286:AAGf5IxiQINSwhNuSESJvbjsoTJdJ07Fihw"

# Brawl Stars Server Configuration
BRAWL_STARS_HOST = "game.brawlstarsgame.com"
BRAWL_STARS_PORT = 9339

# Server Public Key (from BrawlStars-Client by PeterHackz)
SERVER_PUBLIC_KEY = bytes.fromhex("5C344B84451436796B735CB62EE38DF813A31798D21294F8C05E0F2B4CA4C047")

# Message Types
MSG_CLIENT_HELLO = 10100
MSG_LOGIN = 10101
MSG_FRIEND = 10502
MSG_SPECTATE = 14104

# Limits
MAX_SPECTATORS = 200
FRIEND_REQUEST_COUNT = 30
