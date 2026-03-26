"""
main.py — entry point for the Retail Arbitrage Bot.

Usage:
  python main.py              # run live (alerts fire, deals logged)
  python main.py --paper      # paper trading: scan and log but no alerts
  python main.py --once       # run one scan immediately and exit
  python main.py --test       # test your API keys and alert channels
"""

import argparse
import logging
import sys
import schedule
import time
from datetime import datetime

from config import SCAN_INTERVAL_MINUTES
from alerts import send_startup_message, send_daily_summary
from scanner import run_scan, STATS

# ── Logging setup ─────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("arb_bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


# ── CLI args ──────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(description="Retail Arbitrage Bot")
    parser.add_argument("--paper", action="store_true",
                        help="Paper trading mode: scan without sending alerts")
    parser.add_argument("--once", action="store_true",
                        help="Run a single scan and exit")
    parser.add_argument("--test", action="store_true",
                        help="Test API keys and alert channels")
    return parser.parse_args()


# ── Test mode ─────────────────────────────────────────────────────────────────

def run_tests():
    """Quick sanity check for all configured integrations."""
    from config import KEEPA_API_KEY, EBAY_APP_ID, TELEGRAM_BOT_TOKEN, EMAIL_SENDER
    from alerts import send_telegram, send_email

    logger.info("Running integration tests...")
    print()

    # Check config
    checks = {
        "Keepa API key":       bool(KEEPA_API_KEY),
        "eBay App ID":         bool(EBAY_APP_ID),
        "Telegram token":      bool(TELEGRAM_BOT_TOKEN),
        "Email sender":        bool(EMAIL_SENDER),
    }
    for label, ok in checks.items():
        status = "✅" if ok else "❌ NOT SET"
        print(f"  {status}  {label}")

    print()

    # Send a test alert
    test_deal = {
        "found_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "title": "TEST PRODUCT — Arb Bot Test Alert",
        "asin": "TEST123",
        "buy_platform": "ebay",
        "buy_price": 15.00,
        "buy_url": "https://ebay.com",
        "sell_platform": "amazon",
        "sell_price": 45.00,
        "sell_url": "https://amazon.com",
        "platform_fees": 8.50,
        "shipping_cost": 5.00,
        "net_profit": 16.50,
        "roi_percent": 110.0,
    }

    print("  Sending Telegram test alert...")
    tg_ok = send_telegram(test_deal)
    print(f"  {'✅ Sent' if tg_ok else '❌ Failed'}")

    print("  Sending email test alert...")
    em_ok = send_email(test_deal)
    print(f"  {'✅ Sent' if em_ok else '❌ Failed (check EMAIL credentials in .env)'}")

    print()
    print("Test complete. Check your Telegram and email inbox.")
    sys.exit(0)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    if args.test:
        run_tests()

    logger.info("=" * 60)
    logger.info("  Retail Arbitrage Bot starting up")
    logger.info(f"  Mode: {'PAPER TRADING (no alerts)' if args.paper else 'LIVE'}")
    logger.info(f"  Scan interval: every {SCAN_INTERVAL_MINUTES} minutes")
    logger.info("=" * 60)

    if args.paper:
        # Monkey-patch send_alert to a no-op in paper trading mode
        import alerts
        alerts.send_alert = lambda deal: logger.info(
            f"[PAPER] Deal suppressed: {deal['title']} — ${deal['net_profit']:.2f} profit"
        )

    if args.once:
        run_scan()
        sys.exit(0)

    # Send startup notification
    if not args.paper:
        send_startup_message()

    # Schedule recurring scans
    schedule.every(SCAN_INTERVAL_MINUTES).minutes.do(run_scan)

    # Schedule daily summary at 9pm
    schedule.every().day.at("21:00").do(lambda: send_daily_summary(STATS))

    # Run the first scan immediately on startup
    logger.info("Running initial scan...")
    run_scan()

    logger.info(f"Scheduler active — next scan in {SCAN_INTERVAL_MINUTES} minutes. Press Ctrl+C to stop.")

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nBot stopped by user.")
        sys.exit(0)
