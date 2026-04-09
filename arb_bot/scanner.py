"""
scanner.py — core arbitrage scanning logic.

For each product in the watchlist:
  1. Fetch Amazon sale price (what you SELL for via FBA)
  2. Fetch eBay sold price, Walmart price, liquidation listings (where you BUY)
  3. Calculate net profit for every buy->sell combination
  4. Alert if ROI and profit thresholds are met
  5. Log everything to deals.csv
"""

import csv
import logging
import os
from datetime import datetime

from config import MIN_ROI_PERCENT, MIN_NET_PROFIT_USD
from fees import calculate_net_profit
from sources import (
    get_amazon_price,
    get_ebay_sold_price,
    get_walmart_price,
    get_liquidation_listings,
)
from alerts import send_alert
from watchlist import WATCHLIST

logger = logging.getLogger(__name__)

DEALS_LOG = "deals.csv"
STATS = {
    "scans": 0,
    "products_checked": 0,
    "deals_found": 0,
    "best_roi": 0.0,
    "best_profit": 0.0,
}


def ensure_log_file():
    """Create the CSV log file with headers if it doesn't exist."""
    if not os.path.exists(DEALS_LOG):
        with open(DEALS_LOG, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "found_at", "title", "asin",
                "buy_platform", "buy_price",
                "sell_platform", "sell_price",
                "platform_fees", "shipping_cost",
                "net_profit", "roi_percent",
                "buy_url", "sell_url",
            ])
            writer.writeheader()


def log_deal(deal: dict):
    """Append a confirmed deal to the CSV log."""
    with open(DEALS_LOG, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "found_at", "title", "asin",
            "buy_platform", "buy_price",
            "sell_platform", "sell_price",
            "platform_fees", "shipping_cost",
            "net_profit", "roi_percent",
            "buy_url", "sell_url",
        ])
        writer.writerow({
            "found_at":      deal.get("found_at"),
            "title":         deal.get("title"),
            "asin":          deal.get("asin"),
            "buy_platform":  deal.get("buy_platform"),
            "buy_price":     deal.get("buy_price"),
            "sell_platform": deal.get("sell_platform"),
            "sell_price":    deal.get("sell_price"),
            "platform_fees": deal.get("platform_fees"),
            "shipping_cost": deal.get("shipping_cost"),
            "net_profit":    deal.get("net_profit"),
            "roi_percent":   deal.get("roi_percent"),
            "buy_url":       deal.get("buy_url"),
            "sell_url":      deal.get("sell_url"),
        })


def check_opportunity(
    product: dict,
    buy_data: dict,
    sell_data: dict,
    sell_platform: str,
) -> dict | None:
    """
    Calculate profit for a buy/sell pair.
    Returns a deal dict if thresholds are met, None otherwise.
    """
    buy_price  = buy_data["price"]
    sell_price = sell_data["price"]

    if buy_price >= sell_price:
        return None

    result = calculate_net_profit(
        buy_price       = buy_price,
        sell_price      = sell_price,
        sell_platform   = sell_platform,
        shipping_to_fba = 5.0,
        weight_kg       = product.get("weight_kg", 0.5),
        category        = product.get("category", "general"),
    )

    net_profit = result["net_profit"]
    roi        = result["roi_percent"]

    if net_profit >= MIN_NET_PROFIT_USD and roi >= MIN_ROI_PERCENT:
        return {
            "found_at":      datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "title":         product["name"],
            "asin":          product["asin"],
            "buy_platform":  buy_data["platform"],
            "buy_price":     buy_price,
            "buy_url":       buy_data.get("url", ""),
            "sell_platform": sell_platform,
            "sell_price":    sell_price,
            "sell_url":      sell_data.get("url", ""),
            "platform_fees": result["platform_fees"],
            "shipping_cost": result["shipping_cost"],
            "net_profit":    net_profit,
            "roi_percent":   roi,
        }

    return None


def scan_product(product: dict) -> list[dict]:
    """
    Run a full arbitrage scan for a single product.
    Returns a list of deals found (often empty).
    """
    asin    = product["asin"]
    name    = product["name"]
    min_buy = product.get("min_buy_price", 1.0)
    max_buy = product.get("max_buy_price", 9999.0)

    logger.info(f"  Checking: {name} ({asin})")
    STATS["products_checked"] += 1
    deals_found = []

    # ── Step 1: Get Amazon sale price (what we SELL for) ─────────────────────
    amazon_data = get_amazon_price(asin)
    if not amazon_data:
        logger.debug(f"    No Amazon price found for {asin}")
        return []

    amazon_price = amazon_data["price"]

    # Sanity check — if price is way above expected range, the API likely
    # returned a bundle or wrong listing. Skip to avoid false deal signals.
    max_expected = max_buy * 3
    if amazon_price > max_expected:
        logger.warning(
            f"    Amazon price ${amazon_price:.2f} looks incorrect for {name} "
            f"(expected under ${max_expected:.0f}) — skipping"
        )
        return []

    logger.info(f"    Amazon price: ${amazon_price:.2f}")

    # ── Step 2: Check eBay as buy source ─────────────────────────────────────
    ebay_data = get_ebay_sold_price(name)
    if ebay_data:
        ebay_price = ebay_data["price"]
        logger.info(f"    eBay sold price: ${ebay_price:.2f} (median of {ebay_data.get('sample_size', '?')} sales)")
        if min_buy <= ebay_price <= max_buy:
            deal = check_opportunity(product, ebay_data, amazon_data, "amazon")
            if deal:
                logger.info(
                    f"    DEAL: Buy eBay ${ebay_price:.2f} -> "
                    f"Sell Amazon ${amazon_price:.2f} = "
                    f"${deal['net_profit']:.2f} ({deal['roi_percent']:.1f}% ROI)"
                )
                deals_found.append(deal)

    # ── Step 3: Check Walmart as buy source ──────────────────────────────────
    walmart_data = get_walmart_price(name)
    if walmart_data:
        walmart_price = walmart_data["price"]
        logger.info(f"    Walmart price: ${walmart_price:.2f}")
        if min_buy <= walmart_price <= max_buy:
            deal = check_opportunity(product, walmart_data, amazon_data, "amazon")
            if deal:
                logger.info(
                    f"    DEAL: Buy Walmart ${walmart_price:.2f} -> "
                    f"Sell Amazon ${amazon_price:.2f} = "
                    f"${deal['net_profit']:.2f} ({deal['roi_percent']:.1f}% ROI)"
                )
                deals_found.append(deal)

    # ── Step 4: Check liquidation lots as buy source ──────────────────────────
    liq_listings = get_liquidation_listings(name, max_results=3)
    for liq in liq_listings:
        liq_price = liq["price"]
        if min_buy <= liq_price <= max_buy:
            deal = check_opportunity(product, liq, amazon_data, "amazon")
            if deal:
                deal["title"] += " [LOT — verify per-unit cost before buying]"
                logger.info(
                    f"    DEAL (lot): ${liq_price:.2f} lot -> "
                    f"Sell Amazon ${amazon_price:.2f}"
                )
                deals_found.append(deal)

    return deals_found


def run_scan():
    """
    Main scan loop. Called by the scheduler every N minutes.
    Scans every product in the watchlist and processes all deals found.
    """
    ensure_log_file()
    STATS["scans"] += 1
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    logger.info(f"\n{'='*60}")
    logger.info(f"Scan #{STATS['scans']} started at {timestamp}")
    logger.info(f"Checking {len(WATCHLIST)} products...")
    logger.info(f"{'='*60}")

    all_deals = []

    for product in WATCHLIST:
        try:
            deals = scan_product(product)
            all_deals.extend(deals)
        except Exception as e:
            logger.error(f"Error scanning {product['name']}: {e}")

    for deal in all_deals:
        STATS["deals_found"]  += 1
        STATS["best_roi"]      = max(STATS["best_roi"],    deal["roi_percent"])
        STATS["best_profit"]   = max(STATS["best_profit"], deal["net_profit"])
        log_deal(deal)
        send_alert(deal)

    logger.info(
        f"\nScan complete. {len(all_deals)} deal(s) found this cycle.\n"
        f"Lifetime totals — Scans: {STATS['scans']} | "
        f"Deals: {STATS['deals_found']} | "
        f"Best ROI: {STATS['best_roi']:.1f}%\n"
    )

    return all_deals
