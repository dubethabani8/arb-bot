"""
alerts.py — send deal notifications via Telegram and email.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import requests

from config import (
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
    EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECIPIENT,
)

logger = logging.getLogger(__name__)


def format_deal_message(deal: dict) -> str:
    """
    Build a human-readable deal summary from a deal dict.
    Used by both Telegram and email alerts.
    """
    profit = deal["net_profit"]
    roi = deal["roi_percent"]
    stars = "🔥🔥🔥" if roi >= 50 else ("🔥🔥" if roi >= 35 else "🔥")

    lines = [
        f"{stars} DEAL FOUND {stars}",
        f"",
        f"📦 Product:   {deal['title']}",
        f"🛒 Buy from:  {deal['buy_platform'].upper()} at ${deal['buy_price']:.2f}",
        f"💰 Sell on:   {deal['sell_platform'].upper()} at ${deal['sell_price']:.2f}",
        f"",
        f"📊 Net profit:   ${profit:.2f}",
        f"📈 ROI:          {roi:.1f}%",
        f"💸 Platform fees: ${deal['platform_fees']:.2f}",
        f"🚚 Shipping:      ${deal['shipping_cost']:.2f}",
        f"",
        f"🔗 Buy here: {deal.get('buy_url', 'N/A')}",
        f"🔗 Sell here: {deal.get('sell_url', 'N/A')}",
        f"",
        f"🕐 Found at: {deal.get('found_at', 'N/A')}",
    ]
    return "\n".join(lines)


def send_telegram(deal: dict) -> bool:
    """
    Send a deal alert to your Telegram chat.
    Returns True on success, False on failure.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram credentials not configured — skipping Telegram alert.")
        return False

    message = format_deal_message(deal)
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        logger.info("Telegram alert sent successfully.")
        return True
    except Exception as e:
        logger.error(f"Telegram alert failed: {e}")
        return False


def send_email(deal: dict) -> bool:
    """
    Send a deal alert via Gmail (or any SMTP provider).
    Requires an App Password if 2FA is enabled on Gmail.
    Returns True on success, False on failure.
    """
    if not EMAIL_SENDER or not EMAIL_PASSWORD or not EMAIL_RECIPIENT:
        logger.warning("Email credentials not configured — skipping email alert.")
        return False

    profit = deal["net_profit"]
    roi = deal["roi_percent"]
    subject = f"[ARB BOT] Deal found — ${profit:.2f} profit ({roi:.1f}% ROI) on {deal['title'][:40]}"

    body_text = format_deal_message(deal)

    # HTML version for nicer email rendering
    body_html = f"""
    <html><body style="font-family: Arial, sans-serif; max-width: 600px; margin: auto;">
      <h2 style="color: #1a3a5c;">🔥 Arbitrage Deal Found</h2>
      <table style="width:100%; border-collapse: collapse;">
        <tr style="background:#f0f6ff;"><td style="padding:8px; font-weight:bold;">Product</td>
            <td style="padding:8px;">{deal['title']}</td></tr>
        <tr><td style="padding:8px; font-weight:bold;">Buy from</td>
            <td style="padding:8px;">{deal['buy_platform'].upper()} — <b>${deal['buy_price']:.2f}</b></td></tr>
        <tr style="background:#f0f6ff;"><td style="padding:8px; font-weight:bold;">Sell on</td>
            <td style="padding:8px;">{deal['sell_platform'].upper()} — <b>${deal['sell_price']:.2f}</b></td></tr>
        <tr><td style="padding:8px; font-weight:bold;">Net Profit</td>
            <td style="padding:8px; color: #1a7a2e;"><b>${profit:.2f}</b></td></tr>
        <tr style="background:#f0f6ff;"><td style="padding:8px; font-weight:bold;">ROI</td>
            <td style="padding:8px; color: #1a7a2e;"><b>{roi:.1f}%</b></td></tr>
        <tr><td style="padding:8px; font-weight:bold;">Platform Fees</td>
            <td style="padding:8px;">${deal['platform_fees']:.2f}</td></tr>
        <tr style="background:#f0f6ff;"><td style="padding:8px; font-weight:bold;">Shipping</td>
            <td style="padding:8px;">${deal['shipping_cost']:.2f}</td></tr>
      </table>
      <p><a href="{deal.get('buy_url','#')}">→ Buy link</a> &nbsp;|&nbsp;
         <a href="{deal.get('sell_url','#')}">→ Sell link</a></p>
      <p style="color:#999; font-size:12px;">Found at {deal.get('found_at','N/A')} by Arb Bot</p>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECIPIENT
    msg.attach(MIMEText(body_text, "plain"))
    msg.attach(MIMEText(body_html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT, msg.as_string())
        logger.info("Email alert sent successfully.")
        return True
    except Exception as e:
        logger.error(f"Email alert failed: {e}")
        return False


def send_alert(deal: dict) -> None:
    """
    Send both Telegram and email alerts for a deal.
    Failures in one channel do not block the other.
    """
    send_telegram(deal)
    send_email(deal)


def send_startup_message() -> None:
    """Send a simple message when the bot starts, so you know it's live."""
    msg = "✅ Arb Bot started and scanning for deals..."
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        try:
            requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg}, timeout=10)
        except Exception:
            pass


def send_daily_summary(summary: dict) -> None:
    """
    Send a daily performance summary.
    Call this from your scheduler at end of day.
    """
    lines = [
        "📅 Daily Summary",
        f"Scans completed:   {summary.get('scans', 0)}",
        f"Products checked:  {summary.get('products_checked', 0)}",
        f"Deals found:       {summary.get('deals_found', 0)}",
        f"Best ROI today:    {summary.get('best_roi', 0):.1f}%",
        f"Best profit today: ${summary.get('best_profit', 0):.2f}",
    ]
    msg = "\n".join(lines)
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        try:
            requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg}, timeout=10)
        except Exception:
            pass
