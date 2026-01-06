# Telegram Bot Configuration
# Instructions:
# 1. Open Telegram and search for "BotFather".
# 2. Send /newbot and follow instructions to get your TOKEN.
# 3. Search for "userinfobot" to get your CHAT_ID.

TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID_HERE"

# Pushover Configuration (Optional - Leave empty if unused)
# Get keys at: https://pushover.net/
PUSHOVER_USER_KEY = "YOUR_PUSHOVER_USER_KEY_HERE"
PUSHOVER_API_TOKEN = "YOUR_PUSHOVER_API_TOKEN_HERE"

# List of words that trigger a CRITICAL alert if seen on screen
DANGER_WORDS = [
    "verify",
    "verification",
    "captcha",
    "robot",
    "solve",
    "human",
    "challenge",
    "suspicious",
    "detected",
    "banned",
    "admin"
]

# Words that should NEVER be considered as a verification code
OCR_BLACKLIST = [
    "verify", "result", "please", "unable", "issue", "server", "times", "regen", 
    "captcha", "images", "setting", "discord", "continue", "solve", "posted", 
    "above", "command", "unreadable", "code", "there", "click",
    "fished", "caught", "seconds", "minute", "minutes", "waiting", "treasure",
    "online", "member", "active", "status", "events", "general", "boost", "settings"
]
