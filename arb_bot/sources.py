"""
sources.py — price data fetchers for each platform.

Amazon data sources (in priority order):
  1. RainforestAPI  — 200 free requests/month, no card needed (rainforestapi.com)
  2. Playwright     — direct scrape fallback, free but needs proxies at scale

Each function returns a normalised dict:
  { "platform", "title", "price", "url", "identifier" }
Returns None if the product is not found or an error occurs.
"""

import os
import time
import random
import logging
import requests
from config import EBAY_APP_ID, BLUECART_API_KEY

logger = logging.getLogger(__name__)

RAINFOREST_API_KEY = os.getenv("RAINFOREST_API_KEY", "")
USE_PLAYWRIGHT     = os.getenv("USE_PLAYWRIGHT_SCRAPER", "false").lower() == "true"


def get_amazon_price_rainforest(asin: str) -> dict | None:
    """
    RainforestAPI — free tier: 200 req/month, no credit card.
    Sign up: https://rainforestapi.com
    .env key: RAINFOREST_API_KEY
    """
    if not RAINFOREST_API_KEY:
        logger.debug("No RainforestAPI key set — skipping.")
        return None

    params = {
        "api_key": RAINFOREST_API_KEY,
        "type": "product",
        "asin": asin,
        "amazon_domain": "amazon.com",
    }
    try:
        resp = requests.get("https://api.rainforestapi.com/request", params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        product = data.get("product", {})
        if not product:
            return None

        buybox     = product.get("buybox_winner", {})
        price_data = buybox.get("price") or product.get("price")
        if not price_data:
            return None

        price = price_data.get("value")
        if not price or price <= 0:
            return None

        return {
            "platform":      "amazon",
            "title":         product.get("title", "Unknown product"),
            "price":         round(float(price), 2),
            "url":           f"https://www.amazon.com/dp/{asin}",
            "identifier":    asin,
            "rating":        product.get("rating"),
            "ratings_total": product.get("ratings_total"),
            "source":        "rainforest",
        }

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            logger.warning("RainforestAPI rate limit reached — free quota may be used up.")
        else:
            logger.error(f"RainforestAPI HTTP error for {asin}: {e}")
        return None
    except Exception as e:
        logger.error(f"RainforestAPI error for {asin}: {e}")
        return None


def get_amazon_price_playwright(asin: str) -> dict | None:
    """
    Playwright scraper — free fallback. Amazon may block at scale.
    Enable in .env: USE_PLAYWRIGHT_SCRAPER=true
    Install: pip install playwright && playwright install chromium
    """
    if not USE_PLAYWRIGHT:
        return None

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.error("Playwright not installed. Run: pip install playwright && playwright install chromium")
        return None

    url = f"https://www.amazon.com/dp/{asin}"
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/118.0.0.0 Safari/537.36",
    ]

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=random.choice(user_agents),
                viewport={"width": 1280, "height": 800},
            )
            page = context.new_page()
            time.sleep(random.uniform(1.5, 3.0))
            page.goto(url, wait_until="domcontentloaded", timeout=20000)

            if "captcha" in page.url.lower() or page.query_selector("#captchacharacters"):
                logger.warning(f"Amazon CAPTCHA for {asin} — consider using a proxy.")
                browser.close()
                return None

            title_el = page.query_selector("#productTitle")
            title    = title_el.inner_text().strip() if title_el else "Unknown product"

            price         = None
            price_selectors = [
                (".priceToPay .a-price-whole",          ".priceToPay .a-price-fraction"),
                ("#priceblock_ourprice",                 None),
                ("#priceblock_dealprice",                None),
                ("#corePrice_feature_div .a-price-whole","#corePrice_feature_div .a-price-fraction"),
            ]

            for whole_sel, frac_sel in price_selectors:
                el = page.query_selector(whole_sel)
                if el:
                    try:
                        whole    = int(el.inner_text().strip().replace(",", "").replace("$", ""))
                        fraction = 0
                        if frac_sel:
                            fel = page.query_selector(frac_sel)
                            if fel:
                                fraction = int(fel.inner_text().strip())
                        price = whole + fraction / 100
                        break
                    except ValueError:
                        continue

            browser.close()

            if not price or price <= 0:
                return None

            return {
                "platform":   "amazon",
                "title":      title,
                "price":      round(price, 2),
                "url":        url,
                "identifier": asin,
                "source":     "playwright",
            }

    except Exception as e:
        logger.error(f"Playwright error for {asin}: {e}")
        return None


def get_amazon_price(asin: str) -> dict | None:
    """
    Master Amazon fetcher. Tries RainforestAPI first, then Playwright.
    """
    result = get_amazon_price_rainforest(asin)
    if result:
        return result

    result = get_amazon_price_playwright(asin)
    if result:
        return result

    logger.warning(
        f"No Amazon price for {asin}. "
        "Set RAINFOREST_API_KEY or USE_PLAYWRIGHT_SCRAPER=true in .env"
    )
    return None


def get_ebay_sold_price(keywords: str, min_price: float = 1.0) -> dict | None:
    """
    eBay Finding API — free. Sign up: https://developer.ebay.com
    .env key: EBAY_APP_ID
    Returns median price of last 10 sold listings.
    """
    if not EBAY_APP_ID:
        logger.warning("No eBay App ID set — skipping eBay lookup.")
        return None

    params = {
        "OPERATION-NAME":             "findCompletedItems",
        "SERVICE-VERSION":            "1.0.0",
        "SECURITY-APPNAME":           EBAY_APP_ID,
        "RESPONSE-DATA-FORMAT":       "JSON",
        "keywords":                   keywords,
        "itemFilter(0).name":         "SoldItemsOnly",
        "itemFilter(0).value":        "true",
        "itemFilter(1).name":         "MinPrice",
        "itemFilter(1).value":        str(min_price),
        "sortOrder":                  "EndTimeSoonest",
        "paginationInput.entriesPerPage": "10",
    }

    try:
        resp = requests.get(
            "https://svcs.ebay.com/services/search/FindingService/v1",
            params=params, timeout=10
        )
        resp.raise_for_status()
        data = resp.json()

        items = (
            data.get("findCompletedItemsResponse", [{}])[0]
                .get("searchResult", [{}])[0]
                .get("item", [])
        )
        if not items:
            return None

        prices = []
        for item in items:
            try:
                prices.append(float(item["sellingStatus"][0]["currentPrice"][0]["__value__"]))
            except (KeyError, IndexError, ValueError):
                continue

        if not prices:
            return None

        prices.sort()
        median = prices[len(prices) // 2]
        first  = items[0]

        return {
            "platform":    "ebay",
            "title":       first.get("title", ["Unknown"])[0],
            "price":       round(median, 2),
            "url":         first.get("viewItemURL", [""])[0],
            "identifier":  first.get("itemId", [""])[0],
            "sample_size": len(prices),
        }

    except Exception as e:
        logger.error(f"eBay error for '{keywords}': {e}")
        return None


def get_walmart_price(query: str) -> dict | None:
    """
    Bluecart API (Walmart) — free tier: 100 req/month, no card.
    Sign up: https://www.bluecartapi.com
    .env key: BLUECART_API_KEY
    """
    if not BLUECART_API_KEY:
        logger.warning("No Bluecart API key — skipping Walmart lookup.")
        return None

    params = {
        "api_key":     BLUECART_API_KEY,
        "type":        "search",
        "search_term": query,
    }

    try:
        resp = requests.get("https://api.bluecartapi.com/request", params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        items = (
            data.get("search_results", {})
                .get("item_results", {})
                .get("results", [])
        )
        if not items:
            return None

        for item in items:
            price = item.get("offers", {}).get("primary", {}).get("price")
            if price:
                return {
                    "platform":   "walmart",
                    "title":      item.get("product", {}).get("title", "Unknown"),
                    "price":      round(float(price), 2),
                    "url":        item.get("product", {}).get("link", ""),
                    "identifier": item.get("product", {}).get("item_id", ""),
                }
        return None

    except Exception as e:
        logger.error(f"Walmart/Bluecart error for '{query}': {e}")
        return None


def get_liquidation_listings(search_term: str, max_results: int = 5) -> list[dict]:
    """
    Scrape Liquidation.com for auction lots.
    NOTE: prices are per-lot — divide by quantity for per-unit cost.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        )
    }
    results = []

    try:
        from bs4 import BeautifulSoup
        resp = requests.get(
            "https://www.liquidation.com/items/search",
            params={"q": search_term, "sort": "ending_soon"},
            headers=headers, timeout=15
        )
        resp.raise_for_status()
        soup  = BeautifulSoup(resp.text, "html.parser")
        cards = soup.select(".lot-card, .item-card, article.lot")[:max_results]

        for card in cards:
            try:
                title_el = card.select_one(".lot-title, h3, .item-title")
                price_el = card.select_one(".current-bid, .price, .lot-price")
                link_el  = card.select_one("a[href]")
                if not (title_el and price_el):
                    continue
                price = float(price_el.get_text(strip=True).replace("$", "").replace(",", ""))
                link  = link_el["href"] if link_el else ""
                if link and not link.startswith("http"):
                    link = "https://www.liquidation.com" + link
                results.append({
                    "platform":   "liquidation",
                    "title":      title_el.get_text(strip=True),
                    "price":      round(price, 2),
                    "url":        link,
                    "identifier": link,
                    "note":       "Lot price — divide by quantity for per-unit cost",
                })
            except Exception:
                continue

    except Exception as e:
        logger.error(f"Liquidation.com error for '{search_term}': {e}")

    return results

