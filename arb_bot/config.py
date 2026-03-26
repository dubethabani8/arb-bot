"""
config.py — loads all settings from .env
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API keys
KEEPA_API_KEY       = os.getenv("KEEPA_API_KEY", "")
EBAY_APP_ID         = os.getenv("EBAY_APP_ID", "")
BLUECART_API_KEY    = os.getenv("BLUECART_API_KEY", "")

# Alerts
TELEGRAM_BOT_TOKEN  = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID    = os.getenv("TELEGRAM_CHAT_ID", "")
EMAIL_SENDER        = os.getenv("EMAIL_SENDER", "")
EMAIL_PASSWORD      = os.getenv("EMAIL_PASSWORD", "")
EMAIL_RECIPIENT     = os.getenv("EMAIL_RECIPIENT", "")

# Bot behaviour
MIN_ROI_PERCENT         = float(os.getenv("MIN_ROI_PERCENT", 25))
MIN_NET_PROFIT_USD      = float(os.getenv("MIN_NET_PROFIT_USD", 10))
SCAN_INTERVAL_MINUTES   = int(os.getenv("SCAN_INTERVAL_MINUTES", 20))
TOTAL_CAPITAL_USD       = float(os.getenv("TOTAL_CAPITAL_USD", 1000))

RAINFOREST_API_KEY     = os.getenv("RAINFOREST_API_KEY", "DB34419854AA4BA0BCD3DD9901A6736D")
USE_PLAYWRIGHT_SCRAPER = os.getenv("USE_PLAYWRIGHT_SCRAPER", "false")
