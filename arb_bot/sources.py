"""
sources.py — price data fetchers for each platform.

Each function returns a normalised dict:
  {
    "platform": str,
    "title": str,
    "price": float,        # current lowest price
    "url": str,
    "identifier": str,     # ASIN / UPC / item ID
  }
Returns None if the product is not found or an error occurs.
"""

import requests
import logging
from config import KEEPA_API_KEY, EBAY_APP_ID, BLUECART_API_KEY

logger = logging.getLogger(__name__)


# ── Amazon via Keepa API ──────────────────────────────────────────────────────

def get_amazon_price(asin: str) -> dict | None:
    """
    Fetch current Amazon price for an ASIN using the Keepa API.
    Keepa returns prices in cents × 10 (so 1999 = $1.99).
    """
    if not KEEPA_API_KEY:
        logger.warning("No Keepa API key set — skipping Amazon lookup.")
        return None

    url = "https://api.keepa.com/product"
    params = {
        "key": KEEPA_API_KEY,
        "domain": 1,      # 1 = amazon.com
        "asin": asin,
        "stats": 1,
        "offers": 20,
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        products = data.get("products", [])
        if not products:
            return None

        product = products[0]
        stats = product.get("stats", {})

        # 'current' array: index 0 = Amazon price, index 1 = Marketplace new
        current = stats.get("current", [])
        # Keepa uses -1 for "not available"
        amazon_price_raw = current[0] if len(current) > 0 else -1
        marketplace_price_raw = current[1] if len(current) > 1 else -1

        # Use whichever is available and positive
        raw_price = -1
        if amazon_price_raw > 0:
            raw_price = amazon_price_raw
        elif marketplace_price_raw > 0:
            raw_price = marketplace_price_raw

        if raw_price <= 0:
            return None

        price = raw_price / 100.0  # Keepa stores as cents (not cents×10 for current)

        title = product.get("title", "Unknown product")
        url_str = f"https://www.amazon.com/dp/{asin}"

        return {
            "platform": "amazon",
            "title": title,
            "price": round(price, 2),
            "url": url_str,
            "identifier": asin,
            "sales_rank": product.get("salesRanks", {}).get("current", [None])[0],
        }

    except Exception as e:
        logger.error(f"Keepa error for ASIN {asin}: {e}")
        return None


# ── eBay sold listings via Finding API ───────────────────────────────────────

def get_ebay_sold_price(keywords: str, min_price: float = 1.0) -> dict | None:
    """
    Search eBay completed/sold listings for a product by keyword.
    Returns the median sale price of the last 10 sold listings.

    Uses the eBay Finding API (free, no approval needed beyond app creation).
    """
    if not EBAY_APP_ID:
        logger.warning("No eBay App ID set — skipping eBay lookup.")
        return None

    url = "https://svcs.ebay.com/services/search/FindingService/v1"
    params = {
        "OPERATION-NAME": "findCompletedItems",
        "SERVICE-VERSION": "1.0.0",
        "SECURITY-APPNAME": EBAY_APP_ID,
        "RESPONSE-DATA-FORMAT": "JSON",
        "keywords": keywords,
        "itemFilter(0).name": "SoldItemsOnly",
        "itemFilter(0).value": "true",
        "itemFilter(1).name": "MinPrice",
        "itemFilter(1).value": str(min_price),
        "sortOrder": "EndTimeSoonest",
        "paginationInput.entriesPerPage": "10",
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        search_result = (
            data.get("findCompletedItemsResponse", [{}])[0]
            .get("searchResult", [{}])[0]
        )
        items = search_result.get("item", [])

        if not items:
            return None

        prices = []
        for item in items:
            try:
                price = float(item["sellingStatus"][0]["currentPrice"][0]["__value__"])
                prices.append(price)
            except (KeyError, IndexError, ValueError):
                continue

        if not prices:
            return None

        # Use median to avoid outlier distortion
        prices.sort()
        median_price = prices[len(prices) // 2]

        first_item = items[0]
        title = first_item.get("title", ["Unknown"])[0]
        item_url = first_item.get("viewItemURL", [""])[0]
        item_id = first_item.get("itemId", [""])[0]

        return {
            "platform": "ebay",
            "title": title,
            "price": round(median_price, 2),
            "url": item_url,
            "identifier": item_id,
            "sample_size": len(prices),
        }

    except Exception as e:
        logger.error(f"eBay error for '{keywords}': {e}")
        return None


# ── Walmart via Bluecart API ──────────────────────────────────────────────────

def get_walmart_price(query: str) -> dict | None:
    """
    Fetch Walmart product pricing via the Bluecart API.
    Free tier: 100 requests/month. Paid plans available.
    Sign up at: https://www.bluecartapi.com/

    Alternative: use walmart-api library or scrape with Playwright.
    """
    if not BLUECART_API_KEY:
        logger.warning("No Bluecart API key — skipping Walmart lookup.")
        return None

    url = "https://api.bluecartapi.com/request"
    params = {
        "api_key": BLUECART_API_KEY,
        "type": "search",
        "search_term": query,
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        items = data.get("search_results", {}).get("item_results", {}).get("results", [])
        if not items:
            return None

        # Take the first in-stock result
        for item in items:
            price = item.get("offers", {}).get("primary", {}).get("price")
            if price:
                return {
                    "platform": "walmart",
                    "title": item.get("product", {}).get("title", "Unknown"),
                    "price": round(float(price), 2),
                    "url": item.get("product", {}).get("link", ""),
                    "identifier": item.get("product", {}).get("item_id", ""),
                }

        return None

    except Exception as e:
        logger.error(f"Walmart/Bluecart error for '{query}': {e}")
        return None


# ── Liquidation.com basic scraper ─────────────────────────────────────────────

def get_liquidation_listings(search_term: str, max_results: int = 5) -> list[dict]:
    """
    Scrape Liquidation.com for auction lots matching a search term.
    Returns a list of listings with estimated per-unit cost.

    Note: Liquidation prices are per-lot (bulk), so divide by quantity
    to get per-unit cost. Quantity is often listed in the title.
    """
    url = "https://www.liquidation.com/items/search"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    params = {"q": search_term, "sort": "ending_soon"}

    results = []
    try:
        from bs4 import BeautifulSoup
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Liquidation.com listing cards — selectors may need updating if site changes
        cards = soup.select(".lot-card, .item-card, article.lot")[:max_results]

        for card in cards:
            try:
                title_el = card.select_one(".lot-title, h3, .item-title")
                price_el = card.select_one(".current-bid, .price, .lot-price")
                link_el = card.select_one("a[href]")

                if not (title_el and price_el):
                    continue

                title = title_el.get_text(strip=True)
                price_text = price_el.get_text(strip=True).replace("$", "").replace(",", "")
                try:
                    price = float(price_text)
                except ValueError:
                    continue

                link = link_el["href"] if link_el else ""
                if link and not link.startswith("http"):
                    link = "https://www.liquidation.com" + link

                results.append({
                    "platform": "liquidation",
                    "title": title,
                    "price": round(price, 2),  # this is the lot price, not per-unit
                    "url": link,
                    "identifier": link,
                    "note": "Lot price — divide by quantity for per-unit cost",
                })
            except Exception:
                continue

    except Exception as e:
        logger.error(f"Liquidation.com error for '{search_term}': {e}")

    return results
