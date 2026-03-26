"""
fees.py — accurate fee calculation for each platform.

All fee structures as of 2024. Update if platforms change their rates.
"""


def amazon_fba_fees(sale_price: float, weight_kg: float = 0.5, category: str = "general") -> dict:
    """
    Calculate total Amazon FBA fees for a given sale price.

    Returns a dict with a breakdown and the total fee.

    Referral fee rates by category (simplified):
      - Electronics: 8%
      - Books: 15%
      - Toys & Games: 15%
      - General (default): 15%

    FBA fulfilment fee by weight (small standard, US):
      - 0–0.25 kg:  $3.22
      - 0.25–0.5 kg: $3.40
      - 0.5–0.75 kg: $3.58
      - 0.75–1.0 kg: $3.77
      - 1.0–1.5 kg:  $4.37
      - 1.5–2.0 kg:  $4.90
      - 2.0+ kg:     $5.42
    """
    referral_rates = {
        "electronics": 0.08,
        "books": 0.15,
        "toys": 0.15,
        "clothing": 0.17,
        "general": 0.15,
    }
    referral_rate = referral_rates.get(category.lower(), 0.15)
    referral_fee = sale_price * referral_rate

    # FBA fulfilment fee (small standard item tiers)
    if weight_kg <= 0.25:
        fba_fee = 3.22
    elif weight_kg <= 0.50:
        fba_fee = 3.40
    elif weight_kg <= 0.75:
        fba_fee = 3.58
    elif weight_kg <= 1.00:
        fba_fee = 3.77
    elif weight_kg <= 1.50:
        fba_fee = 4.37
    elif weight_kg <= 2.00:
        fba_fee = 4.90
    else:
        fba_fee = 5.42

    # Closing fee (media items like books/DVDs only)
    closing_fee = 1.80 if category.lower() == "books" else 0.0

    total = referral_fee + fba_fee + closing_fee

    return {
        "referral_fee": round(referral_fee, 2),
        "fba_fulfilment_fee": round(fba_fee, 2),
        "closing_fee": round(closing_fee, 2),
        "total_fees": round(total, 2),
    }


def ebay_fees(sale_price: float) -> dict:
    """
    eBay seller fees (standard account, no store subscription).
      - Final value fee: 13.25% on total amount up to $7,500, then 2.35% above
      - Per-order fee: $0.30
    """
    if sale_price <= 7500:
        fvf = sale_price * 0.1325
    else:
        fvf = 7500 * 0.1325 + (sale_price - 7500) * 0.0235

    per_order = 0.30
    total = fvf + per_order

    return {
        "final_value_fee": round(fvf, 2),
        "per_order_fee": per_order,
        "total_fees": round(total, 2),
    }


def walmart_marketplace_fees(sale_price: float, category: str = "general") -> dict:
    """
    Walmart Marketplace referral fees (simplified).
      - Most categories: 15%
      - Electronics: 8%
      - Jewellery: 20%
    """
    rates = {"electronics": 0.08, "jewellery": 0.20, "general": 0.15}
    rate = rates.get(category.lower(), 0.15)
    referral = sale_price * rate
    return {
        "referral_fee": round(referral, 2),
        "total_fees": round(referral, 2),
    }


def calculate_net_profit(
    buy_price: float,
    sell_price: float,
    sell_platform: str,
    shipping_to_fba: float = 5.0,
    weight_kg: float = 0.5,
    category: str = "general",
) -> dict:
    """
    Master profit calculator.

    Args:
        buy_price:        what you pay to acquire the item
        sell_price:       the listing/sale price on the destination platform
        sell_platform:    'amazon', 'ebay', or 'walmart'
        shipping_to_fba:  cost to ship item to Amazon warehouse (if using FBA)
        weight_kg:        item weight for FBA fee tier
        category:         product category for referral fee rate

    Returns a dict with full breakdown, net profit, and ROI.
    """
    if sell_platform == "amazon":
        fee_breakdown = amazon_fba_fees(sell_price, weight_kg, category)
        platform_fees = fee_breakdown["total_fees"]
        inbound_shipping = shipping_to_fba
    elif sell_platform == "ebay":
        fee_breakdown = ebay_fees(sell_price)
        platform_fees = fee_breakdown["total_fees"]
        inbound_shipping = 0.0  # seller ships directly to buyer
    elif sell_platform == "walmart":
        fee_breakdown = walmart_marketplace_fees(sell_price, category)
        platform_fees = fee_breakdown["total_fees"]
        inbound_shipping = 0.0
    else:
        fee_breakdown = {}
        platform_fees = 0.0
        inbound_shipping = 0.0

    net_profit = sell_price - buy_price - platform_fees - inbound_shipping
    roi = (net_profit / buy_price) * 100 if buy_price > 0 else 0.0

    return {
        "buy_price": round(buy_price, 2),
        "sell_price": round(sell_price, 2),
        "platform_fees": round(platform_fees, 2),
        "shipping_cost": round(inbound_shipping, 2),
        "net_profit": round(net_profit, 2),
        "roi_percent": round(roi, 1),
        "fee_breakdown": fee_breakdown,
    }
