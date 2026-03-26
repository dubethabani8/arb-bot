# watchlist.py — your list of products to scan
#
# How to add a product:
#   1. Find the ASIN on Amazon (it's in the URL: amazon.com/dp/XXXXXXXXXX)
#   2. Add an entry below with the ASIN, a short name, category, and estimated weight in kg
#   3. The bot will check this product every scan cycle
#
# Categories: general | electronics | books | toys | clothing | jewellery
#
# Weight guide (kg):
#   Small item (phone case, cable):    0.1 – 0.3
#   Medium item (toy, small gadget):   0.3 – 0.75
#   Large item (kitchen appliance):    1.0 – 2.5

WATCHLIST = [
    # ── Electronics ──────────────────────────────────────────────────────────
    {
        "asin": "B08N5WRWNW",          # Echo Dot 4th Gen
        "name": "Amazon Echo Dot 4th Gen",
        "category": "electronics",
        "weight_kg": 0.34,
        "min_buy_price": 10.0,         # ignore results below this (likely errors)
        "max_buy_price": 40.0,         # ignore results above this (not a deal)
    },
    {
        "asin": "B07FZ8S74R",          # Fire TV Stick
        "name": "Amazon Fire TV Stick",
        "category": "electronics",
        "weight_kg": 0.10,
        "min_buy_price": 5.0,
        "max_buy_price": 25.0,
    },

    # ── Toys ─────────────────────────────────────────────────────────────────
    {
        "asin": "B07WMNPGSK",          # LEGO Classic set
        "name": "LEGO Classic Creative Bricks",
        "category": "toys",
        "weight_kg": 0.45,
        "min_buy_price": 8.0,
        "max_buy_price": 30.0,
    },

    # ── Books ────────────────────────────────────────────────────────────────
    {
        "asin": "0735224293",          # Atomic Habits
        "name": "Atomic Habits - James Clear",
        "category": "books",
        "weight_kg": 0.30,
        "min_buy_price": 2.0,
        "max_buy_price": 15.0,
    },

    # ── Add your own products below ──────────────────────────────────────────
    # {
    #     "asin": "YOUR_ASIN_HERE",
    #     "name": "Product name",
    #     "category": "general",
    #     "weight_kg": 0.5,
    #     "min_buy_price": 5.0,
    #     "max_buy_price": 100.0,
    # },
]
