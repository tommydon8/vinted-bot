import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
VINTED_SESSION_COOKIE = os.getenv("VINTED_SESSION_COOKIE", "")
VINTED_COUNTRY = os.getenv("VINTED_COUNTRY", "it")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "60"))

PRICE_MIN = 1.0
PRICE_MAX = 10.0

BASE_URL = f"https://www.vinted.{VINTED_COUNTRY}"
API_URL = f"{BASE_URL}/api/v2"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8",
    "Referer": BASE_URL,
    "Origin": BASE_URL,
}
