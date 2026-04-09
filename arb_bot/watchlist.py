# watchlist.py — optimised for Electronics, Kitchen, Beauty, Sports
# Budget: $300–700 | Fulfilment: Amazon FBA
#
# Selection criteria:
#   - Sell price $25–$120 (FBA fees proportionally small)
#   - High turnover — strong BSR in category
#   - Brand name products (easier to resell)
#   - Not sold directly by Amazon
#   - Lightweight under 1kg where possible (lower FBA fees)
#
# HOW TO ADD YOUR OWN:
#   1. Find ASIN in Amazon URL: amazon.com/dp/XXXXXXXXXX
#   2. Copy the template at the bottom, fill it in
#   3. Save and restart the bot
#
# CATEGORIES: electronics | kitchen | beauty | sports | general

WATCHLIST = [

    # ══════════════════════════════════════════════════════════════════════
    # ELECTRONICS & GADGETS
    # Best arb: Best Buy / Walmart clearance → Amazon resale
    # ══════════════════════════════════════════════════════════════════════

    {
        "asin": "B09WB6YVRD",
        "name": "Anker 735 Charger GaNPrime 65W",
        "category": "electronics",
        "weight_kg": 0.18,
        "min_buy_price": 15.0,
        "max_buy_price": 35.0,
        # Sells $45-55 on Amazon. Frequently on sale at Best Buy and Walmart.
    },
    {
        "asin": "B08C4KWM9T",
        "name": "Anker PowerCore Slim 10000 Portable Charger",
        "category": "electronics",
        "weight_kg": 0.22,
        "min_buy_price": 12.0,
        "max_buy_price": 22.0,
        # Sells $30-38 on Amazon. Constant demand from travellers.
    },
    {
        "asin": "B07PXGQC1Q",
        "name": "Tile Mate Bluetooth Tracker 4-Pack",
        "category": "electronics",
        "weight_kg": 0.12,
        "min_buy_price": 15.0,
        "max_buy_price": 30.0,
        # Sells $35-50 on Amazon. Frequently discounted at Target and Costco.
    },
    {
        "asin": "B09G9FPHY6",
        "name": "Govee LED Strip Lights 100ft",
        "category": "electronics",
        "weight_kg": 0.35,
        "min_buy_price": 12.0,
        "max_buy_price": 22.0,
        # Sells $28-40 on Amazon. Massive demand from gamers and home decor buyers.
    },
    {
        "asin": "B08BHXG144",
        "name": "Logitech MX Master 3 Advanced Wireless Mouse",
        "category": "electronics",
        "weight_kg": 0.14,
        "min_buy_price": 50.0,
        "max_buy_price": 75.0,
        # Sells $90-100 on Amazon. Premium product, loyal buyers.
    },
    {
        "asin": "B07VGRJDFY",
        "name": "POWRUI Surge Protector 8 Outlets",
        "category": "electronics",
        "weight_kg": 0.40,
        "min_buy_price": 10.0,
        "max_buy_price": 20.0,
        # Sells $25-32 on Amazon. Consistent BSR under 2,000 in electronics.
    },
    {
        "asin": "B08KTZ8249",
        "name": "Soundcore by Anker Life P2 Mini Earbuds",
        "category": "electronics",
        "weight_kg": 0.10,
        "min_buy_price": 15.0,
        "max_buy_price": 28.0,
        # Sells $35-45 on Amazon. Budget earbuds with massive sales volume.
    },

    # ══════════════════════════════════════════════════════════════════════
    # KITCHEN & APPLIANCES
    # Best arb: TJ Maxx / HomeGoods / Walmart clearance → Amazon
    # ══════════════════════════════════════════════════════════════════════

    {
        "asin": "B08YDR2H6V",
        "name": "Stanley Quencher H2.0 FlowState Tumbler 40oz",
        "category": "kitchen",
        "weight_kg": 0.48,
        "min_buy_price": 20.0,
        "max_buy_price": 38.0,
        # Sells $40-55 on Amazon. Viral product with consistently high demand.
    },
    {
        "asin": "B00004SPZV",
        "name": "Lodge 10.25 Inch Cast Iron Skillet",
        "category": "kitchen",
        "weight_kg": 2.10,
        "min_buy_price": 15.0,
        "max_buy_price": 25.0,
        # Sells $30-38 on Amazon. Perennial bestseller, never goes out of demand.
    },
    {
        "asin": "B089WXGTC5",
        "name": "Ninja CF091 Coffee Maker with Thermal Carafe",
        "category": "kitchen",
        "weight_kg": 1.80,
        "min_buy_price": 45.0,
        "max_buy_price": 75.0,
        # Sells $95-115 on Amazon. High ticket = higher dollar profit per unit.
    },
    {
        "asin": "B07GJBBGHG",
        "name": "Instant Pot Duo 7-in-1 Pressure Cooker 6qt",
        "category": "kitchen",
        "weight_kg": 2.50,
        "min_buy_price": 50.0,
        "max_buy_price": 75.0,
        # Sells $90-100 on Amazon. Icon product, steady demand year-round.
    },
    {
        "asin": "B08CYKPB7W",
        "name": "Ninja Air Fryer Pro 4qt AF141",
        "category": "kitchen",
        "weight_kg": 2.20,
        "min_buy_price": 55.0,
        "max_buy_price": 80.0,
        # Sells $100-120 on Amazon. Air fryers are top sellers globally in 2026.
    },
    {
        "asin": "B07WQ25PXR",
        "name": "OXO Good Grips 3-Piece Mixing Bowl Set",
        "category": "kitchen",
        "weight_kg": 0.90,
        "min_buy_price": 20.0,
        "max_buy_price": 32.0,
        # Sells $38-48 on Amazon. Trusted brand with consistent demand.
    },

    # ══════════════════════════════════════════════════════════════════════
    # BEAUTY & HEALTH
    # Best arb: Costco / Ulta / Walmart sale → Amazon resale
    # Note: verify you are ungated for beauty brands before buying stock
    # ══════════════════════════════════════════════════════════════════════

    {
        "asin": "B00TTD9BRC",
        "name": "CeraVe Moisturising Cream 19oz",
        "category": "beauty",
        "weight_kg": 0.60,
        "min_buy_price": 10.0,
        "max_buy_price": 18.0,
        # Sells $20-26 on Amazon. #1 dermatologist recommended brand.
    },
    {
        "asin": "B07FLGR2TH",
        "name": "Neutrogena Hydro Boost Water Gel 1.7oz",
        "category": "beauty",
        "weight_kg": 0.12,
        "min_buy_price": 10.0,
        "max_buy_price": 18.0,
        # Sells $22-28 on Amazon. Lightweight, low FBA fees, high repeat purchase.
    },
    {
        "asin": "B09NWYPTLP",
        "name": "The Ordinary Niacinamide 10 Percent Zinc 60ml",
        "category": "beauty",
        "weight_kg": 0.10,
        "min_buy_price": 7.0,
        "max_buy_price": 13.0,
        # Sells $14-18 on Amazon. Viral skincare, extremely high BSR velocity.
    },
    {
        "asin": "B005F0QKHE",
        "name": "Revlon One-Step Volumiser Hair Dryer Brush",
        "category": "beauty",
        "weight_kg": 0.68,
        "min_buy_price": 25.0,
        "max_buy_price": 42.0,
        # Sells $50-65 on Amazon. Cult product, viral on TikTok, stays in demand.
    },
    {
        "asin": "B08K2H2B7G",
        "name": "Maybelline Sky High Mascara",
        "category": "beauty",
        "weight_kg": 0.05,
        "min_buy_price": 5.0,
        "max_buy_price": 10.0,
        # Sells $12-16 on Amazon. Tiny FBA fees. Frequently out of stock on Amazon.
    },
    {
        "asin": "B07K5299KZ",
        "name": "Dove Body Wash Deep Moisture 22oz 4-Pack",
        "category": "beauty",
        "weight_kg": 2.40,
        "min_buy_price": 12.0,
        "max_buy_price": 20.0,
        # Sells $25-32 on Amazon. Costco multipacks frequently beat Amazon price.
    },

    # ══════════════════════════════════════════════════════════════════════
    # SPORTS & FITNESS
    # Best arb: Dick's Sporting Goods / Walmart clearance → Amazon
    # ══════════════════════════════════════════════════════════════════════

    {
        "asin": "B078H9KDX3",
        "name": "Gaiam Essentials Thick Yoga Mat 2/5 Inch",
        "category": "sports",
        "weight_kg": 0.90,
        "min_buy_price": 15.0,
        "max_buy_price": 26.0,
        # Sells $30-38 on Amazon. Consistent demand from home fitness buyers.
    },
    {
        "asin": "B07C5F9KHK",
        "name": "Fit Simplify Resistance Bands Set of 5",
        "category": "sports",
        "weight_kg": 0.28,
        "min_buy_price": 8.0,
        "max_buy_price": 16.0,
        # Sells $20-28 on Amazon. Lightweight, very low FBA fees, high volume.
    },
    {
        "asin": "B07G5F5CHX",
        "name": "Hydro Flask Standard Mouth 21oz Water Bottle",
        "category": "sports",
        "weight_kg": 0.30,
        "min_buy_price": 22.0,
        "max_buy_price": 35.0,
        # Sells $38-48 on Amazon. Premium brand, loyal following.
    },
    {
        "asin": "B07MJG2MBZ",
        "name": "Hidrate Spark 3 Smart Water Bottle 21oz",
        "category": "sports",
        "weight_kg": 0.25,
        "min_buy_price": 30.0,
        "max_buy_price": 48.0,
        # Sells $55-70 on Amazon. Premium hydration tracker, strong margins.
    },
    {
        "asin": "B08DK3GG59",
        "name": "Sunny Health Fitness Rowing Machine SF-RW5515",
        "category": "sports",
        "weight_kg": 7.50,
        "min_buy_price": 90.0,
        "max_buy_price": 140.0,
        # Sells $160-200 on Amazon. High ticket, less competition due to bulk size.
    },

    # ══════════════════════════════════════════════════════════════════════
    # ADD YOUR OWN PRODUCTS BELOW
    # ══════════════════════════════════════════════════════════════════════

    # {
    #     "asin": "XXXXXXXXXX",
    #     "name": "Product name here",
    #     "category": "general",
    #     "weight_kg": 0.5,
    #     "min_buy_price": 10.0,
    #     "max_buy_price": 60.0,
    # },
]
