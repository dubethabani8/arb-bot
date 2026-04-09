"""
sources.py — price data fetchers for all platforms.

Amazon:
  - Direct HTTP scraper using requests + BeautifulSoup (no Playwright needed)
  - Falls back to RainforestAPI if key is set

Walmart:
  - Direct HTTP scraper using requests + BeautifulSoup

eBay:
  - Finding API (free, developer.ebay.com) — use PRODUCTION key (PRD not SBX)

Liquidation:
  - Direct scrape (beautifulsoup4)
"""

import os
import re
import time
import random
import logging
import requests
from bs4 import BeautifulSoup
from config import EBAY_APP_ID, BLUECART_API_KEY

logger = logging.getLogger(__name__)

RAINFOREST_API_KEY = os.getenv("RAINFOREST_API_KEY", "")

# Rotate these headers to avoid blocks
HEADERS_LIST = [
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0",
    },
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    },
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    },
]


def _get_headers():
    """Return a random header set to rotate identity."""
    return random.choice(HEADERS_LIST)


def _make_session():
    """Create a requests session with realistic browser headers."""
    session = requests.Session()
    session.headers.update(_get_headers())
    return session


# =============================================================================
# AMAZON — direct HTTP scraper (no Playwright, no paid API)
# =============================================================================

SCRAPERAPI_KEY = os.getenv("SCRAPERAPI_KEY", "")

def get_amazon_price_scraper(asin: str) -> dict | None:
    """
    Scrape Amazon via ScraperAPI — handles CAPTCHAs automatically.
    Free tier: 1,000 requests/month. Sign up: https://scraperapi.com
    .env: SCRAPERAPI_KEY=your_key
    Falls back to direct scrape if no key set.
    """
    url = f"https://www.amazon.com/dp/{asin}"

    # Use ScraperAPI if key is configured
    if SCRAPERAPI_KEY:
        proxied_url = (
            f"http://api.scraperapi.com?"
            f"api_key={SCRAPERAPI_KEY}&url={requests.utils.quote(url)}"
            f"&country_code=us"
        )
        try:
            time.sleep(random.uniform(1.0, 2.0))
            resp = requests.get(proxied_url, timeout=60)
            if resp.status_code == 200:
                return _parse_amazon_html(resp.text, asin, url)
        except Exception as e:
            logger.error(f"ScraperAPI error for {asin}: {e}")
            return None

    # Direct scrape fallback (slower, may get CAPTCHAs)
    try:
        session = _make_session()
        time.sleep(random.uniform(8.0, 15.0))
        resp = session.get(url, timeout=15)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
        if soup.find("form", {"action": "/errors/validateCaptcha"}):
            logger.warning(f"Amazon CAPTCHA for {asin} — will retry next scan")
            return None
        return _parse_amazon_html(resp.text, asin, url)
    except Exception as e:
        logger.error(f"Amazon scraper error for {asin}: {e}")
        return None


def _parse_amazon_html(html: str, asin: str, url: str) -> dict | None:
    """Parse Amazon product page HTML and extract price and title."""
    soup  = BeautifulSoup(html, "html.parser")

    if soup.find("form", {"action": "/errors/validateCaptcha"}):
        logger.warning(f"Amazon CAPTCHA for {asin}")
        return None

    title_el = soup.find("span", {"id": "productTitle"})
    title    = title_el.get_text(strip=True) if title_el else "Unknown product"

    price = None
    # Method 1: priceToPay
    price_el = soup.find("span", {"class": "priceToPay"})
    if price_el:
        whole    = price_el.find("span", {"class": "a-price-whole"})
        fraction = price_el.find("span", {"class": "a-price-fraction"})
        if whole:
            try:
                w     = int(re.sub(r"[^\d]", "", whole.get_text()))
                f     = int(fraction.get_text().strip()) if fraction else 0
                price = w + f / 100
            except ValueError:
                pass

    # Method 2: offscreen price spans
    if not price:
        for span in soup.find_all("span", {"class": "a-offscreen"}):
            text = span.get_text(strip=True)
            if text.startswith("$"):
                try:
                    p = float(re.sub(r"[^\d.]", "", text))
                    if p > 0:
                        price = p
                        break
                except ValueError:
                    continue

    if not price or price <= 0:
        return None

    return {
        "platform":   "amazon",
        "title":      title,
        "price":      round(price, 2),
        "url":        url,
        "identifier": asin,
        "source":     "scraperapi" if SCRAPERAPI_KEY else "direct",
    }


def get_amazon_price_rainforest(asin: str) -> dict | None:
    """
    RainforestAPI — reliable paid option.
    Free tier: 200 req/month. Sign up: https://rainforestapi.com
    .env: RAINFOREST_API_KEY=your_key
    """
    if not RAINFOREST_API_KEY:
        return None

    params = {
        "api_key":       RAINFOREST_API_KEY,
        "type":          "product",
        "asin":          asin,
        "amazon_domain": "amazon.com",
    }
    try:
        resp = requests.get(
            "https://api.rainforestapi.com/request",
            params=params, timeout=15
        )
        if resp.status_code == 402:
            logger.warning("RainforestAPI: free quota exhausted — using scraper instead.")
            return None
        resp.raise_for_status()
        data    = resp.json()
        product = data.get("product", {})
        if not product:
            return None

        buybox     = product.get("buybox_winner", {})
        price_data = buybox.get("price") or product.get("price")
        if not price_data:
            return None

        price = price_data.get("value")
        if not price or float(price) <= 0:
            return None

        return {
            "platform":      "amazon",
            "title":         product.get("title", "Unknown product"),
            "price":         round(float(price), 2),
            "url":           f"https://www.amazon.com/dp/{asin}",
            "identifier":    asin,
            "source":        "rainforest",
        }

    except Exception as e:
        logger.error(f"RainforestAPI error for {asin}: {e}")
        return None


def get_amazon_price(asin: str) -> dict | None:
    """
    Master Amazon fetcher.
    Tries RainforestAPI first (if key set), then direct scraper.
    """
    # Try RainforestAPI first if key is configured and not exhausted
    if RAINFOREST_API_KEY:
        result = get_amazon_price_rainforest(asin)
        if result:
            return result

    # Fall back to direct scraper (no API key, no browser needed)
    return get_amazon_price_scraper(asin)


# =============================================================================
# WALMART — direct HTTP scraper
# =============================================================================

def get_walmart_price(query: str) -> dict | None:
    """
    Scrape Walmart search results directly using requests + BeautifulSoup.
    No API key, no browser needed.
    Parses Walmart's embedded JSON data from the page source.
    """
    import json

    search_url = f"https://www.walmart.com/search?q={requests.utils.quote(query)}"

    try:
        session = _make_session()
        time.sleep(random.uniform(1.5, 3.0))

        resp = session.get(search_url, timeout=15)

        if resp.status_code in (429, 503):
            logger.warning(f"Walmart blocked request for '{query}' — will retry next scan")
            return None

        if resp.status_code != 200:
            logger.debug(f"Walmart returned {resp.status_code} for '{query}'")
            return None

        # Strategy 1: parse __NEXT_DATA__ JSON embedded in page
        soup = BeautifulSoup(resp.text, "html.parser")
        next_data_el = soup.find("script", {"id": "__NEXT_DATA__"})

        if next_data_el:
            try:
                data = json.loads(next_data_el.string)

                # Navigate Walmart's JSON structure
                items = (
                    data.get("props", {})
                        .get("pageProps", {})
                        .get("initialData", {})
                        .get("searchResult", {})
                        .get("itemStacks", [{}])[0]
                        .get("items", [])
                )

                if not items:
                    # Try alternate path
                    items = (
                        data.get("props", {})
                            .get("pageProps", {})
                            .get("initialData", {})
                            .get("contentLayout", {})
                            .get("modules", [{}])[0]
                            .get("configs", {})
                            .get("products", [])
                    )

                for item in items:
                    try:
                        price_info    = item.get("priceInfo", {})
                        current_price = price_info.get("currentPrice", {})
                        price         = current_price.get("price") or current_price.get("priceString")

                        if not price:
                            continue

                        if isinstance(price, str):
                            price = float(re.sub(r"[^\d.]", "", price))
                        else:
                            price = float(price)

                        if price <= 0:
                            continue

                        # Skip out of stock
                        avail = item.get("availabilityStatus", "").lower()
                        if "out_of_stock" in avail or "unavailable" in avail:
                            continue

                        title   = item.get("name", "Unknown product")
                        item_id = item.get("usItemId", item.get("itemId", ""))
                        url     = f"https://www.walmart.com/ip/{item_id}" if item_id else search_url

                        return {
                            "platform":   "walmart",
                            "title":      title,
                            "price":      round(price, 2),
                            "url":        url,
                            "identifier": item_id,
                            "source":     "walmart_json",
                        }

                    except (KeyError, ValueError, TypeError):
                        continue

            except (json.JSONDecodeError, Exception) as e:
                logger.debug(f"Walmart JSON parse failed for '{query}': {e}")

        # Strategy 2: parse DOM price elements directly
        price_els = soup.find_all("span", {"itemprop": "price"})
        for el in price_els:
            try:
                price = float(el.get("content", 0))
                if price > 0:
                    title_el = soup.find("span", {"class": re.compile(r"product.*title|item.*name", re.I)})
                    title    = title_el.get_text(strip=True) if title_el else query
                    return {
                        "platform":   "walmart",
                        "title":      title,
                        "price":      round(price, 2),
                        "url":        search_url,
                        "identifier": search_url,
                        "source":     "walmart_dom",
                    }
            except (ValueError, TypeError):
                continue

        logger.debug(f"Walmart: no price found for '{query}'")
        return None

    except requests.exceptions.Timeout:
        logger.warning(f"Walmart request timed out for '{query}'")
        return None
    except Exception as e:
        logger.error(f"Walmart scraper error for '{query}': {e}")
        return None


# =============================================================================
# EBAY — Finding API (free, production key required)
# =============================================================================

def get_ebay_sold_price(keywords: str, min_price: float = 1.0) -> dict | None:
    """
    eBay Finding API — free.
    IMPORTANT: use PRODUCTION key (contains PRD), NOT Sandbox (contains SBX).
    Sign up: https://developer.ebay.com
    .env: EBAY_APP_ID=YourName-AppName-PRD-xxxxxxxx-xxxxxxxx
    Returns median sale price of last 10 sold listings.
    """
    if not EBAY_APP_ID:
        logger.warning("No eBay App ID set — skipping eBay lookup.")
        return None

    if "SBX" in str(EBAY_APP_ID).upper():
        logger.error(
            "eBay App ID is a SANDBOX key (contains SBX). "
            "Copy the PRODUCTION key (contains PRD) from developer.ebay.com"
        )
        return None

    params = {
        "OPERATION-NAME":                 "findCompletedItems",
        "SERVICE-VERSION":                "1.0.0",
        "SECURITY-APPNAME":               EBAY_APP_ID,
        "RESPONSE-DATA-FORMAT":           "JSON",
        "keywords":                       keywords,
        "itemFilter(0).name":             "SoldItemsOnly",
        "itemFilter(0).value":            "true",
        "itemFilter(1).name":             "MinPrice",
        "itemFilter(1).value":            str(min_price),
        "sortOrder":                      "EndTimeSoonest",
        "paginationInput.entriesPerPage": "10",
    }

    try:
        resp = requests.get(
            "https://svcs.ebay.com/services/search/FindingService/v1",
            params=params, timeout=10
        )

        if resp.status_code == 500:
            logger.error(
                f"eBay 500 error for '{keywords}' — likely using Sandbox key. "
                "Use the Production (PRD) key from developer.ebay.com"
            )
            return None

        resp.raise_for_status()
        data = resp.json()

        items = (
            data.get("findCompletedItemsResponse", [{}])[0]
                .get("searchResult",               [{}])[0]
                .get("item", [])
        )
        if not items:
            logger.debug(f"eBay: no sold listings for '{keywords}'")
            return None

        prices = []
        for item in items:
            try:
                price = float(
                    item["sellingStatus"][0]["currentPrice"][0]["__value__"]
                )
                prices.append(price)
            except (KeyError, IndexError, ValueError):
                continue

        if not prices:
            return None

        prices.sort()
        median = prices[len(prices) // 2]
        first  = items[0]

        return {
            "platform":    "ebay",
            "title":       first.get("title",       ["Unknown"])[0],
            "price":       round(median, 2),
            "url":         first.get("viewItemURL", [""])[0],
            "identifier":  first.get("itemId",      [""])[0],
            "sample_size": len(prices),
        }

    except Exception as e:
        logger.error(f"eBay error for '{keywords}': {e}")
        return None


# =============================================================================
# LIQUIDATION.COM scraper
# =============================================================================

def get_liquidation_listings(search_term: str, max_results: int = 5) -> list[dict]:
    """
    Scrape Liquidation.com for auction lots.
    NOTE: prices are per-lot. Divide by quantity for per-unit cost.
    Returns 403 intermittently — failures are normal and logged quietly.
    """
    results = []
    try:
        session = _make_session()
        resp = session.get(
            "https://www.liquidation.com/items/search",
            params={"q": search_term, "sort": "ending_soon"},
            timeout=15
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

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            logger.debug("Liquidation.com 403 — site blocks scrapers intermittently, skipping.")
        else:
            logger.error(f"Liquidation.com error for '{search_term}': {e}")
    except Exception as e:
        logger.error(f"Liquidation.com error for '{search_term}': {e}")

    return results