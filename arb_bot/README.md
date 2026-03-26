# Retail Arbitrage Bot

Scans Amazon, eBay, Walmart, and Liquidation.com for price discrepancies.
Alerts you via Telegram and email when a profitable deal is found.

---

## Project structure

```
arb_bot/
  main.py          ← entry point, scheduler
  scanner.py       ← core scan logic
  sources.py       ← price fetchers (Keepa, eBay, Walmart, Liquidation)
  fees.py          ← fee calculators for each platform
  alerts.py        ← Telegram + email alert sender
  watchlist.py     ← your list of products to monitor
  config.py        ← loads settings from .env
  requirements.txt ← Python dependencies
  .env.example     ← template for your credentials
  arb-bot.service  ← systemd service for VPS deployment
```

---

## Setup (local or VPS)

### 1. Clone / copy the project
```bash
mkdir arb_bot && cd arb_bot
# copy all files here
```

### 2. Create a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
playwright install chromium     # only needed for Liquidation.com scraping
```

### 4. Set up your credentials
```bash
cp .env.example .env
nano .env                       # fill in your API keys
```

Required keys:
- **KEEPA_API_KEY** → https://keepa.com/api (free trial available)
- **EBAY_APP_ID** → https://developer.ebay.com (free)
- **TELEGRAM_BOT_TOKEN** → message @BotFather on Telegram
- **TELEGRAM_CHAT_ID** → message @userinfobot on Telegram
- **EMAIL_SENDER + EMAIL_PASSWORD** → Gmail App Password (Google Account → Security → App Passwords)

Optional:
- **BLUECART_API_KEY** → https://www.bluecartapi.com (free tier: 100 req/month)

### 5. Add products to your watchlist
Edit `watchlist.py` and add ASINs you want to monitor.
Find an ASIN in any Amazon product URL: `amazon.com/dp/XXXXXXXXXX`

### 6. Test your setup
```bash
python main.py --test
```
This verifies your API keys are set and sends a test alert to Telegram and email.

---

## Running the bot

### Paper trading (recommended first — no real alerts, just logs)
```bash
python main.py --paper
```

### Single scan (run once and exit)
```bash
python main.py --once
```

### Live mode (alerts fire, runs on schedule)
```bash
python main.py
```

---

## VPS deployment (run 24/7)

### On your VPS (DigitalOcean / AWS / Hetzner):
```bash
# Upload your project
scp -r arb_bot ubuntu@YOUR_VPS_IP:/home/ubuntu/

# SSH into the VPS
ssh ubuntu@YOUR_VPS_IP

# Install Python and set up
cd /home/ubuntu/arb_bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set up systemd service
sudo cp arb-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable arb-bot
sudo systemctl start arb-bot
```

### Useful commands after deployment:
```bash
sudo systemctl status arb-bot      # check if it's running
sudo journalctl -u arb-bot -f      # live logs
sudo systemctl restart arb-bot     # restart after code changes
tail -f /home/ubuntu/arb_bot/arb_bot.log   # view bot logs
```

---

## Reading your results

All deals are logged to `deals.csv` with full details:
- Timestamp, product name, ASIN
- Buy platform + price, sell platform + price
- Platform fees, shipping cost, net profit, ROI %
- Buy and sell URLs

Open in Excel or Google Sheets to analyse your deal history.

---

## Tuning the bot

All thresholds are in `.env`:

| Setting | Default | What it does |
|---------|---------|--------------|
| MIN_ROI_PERCENT | 25 | Minimum ROI to trigger an alert |
| MIN_NET_PROFIT_USD | 10 | Minimum dollar profit to trigger an alert |
| SCAN_INTERVAL_MINUTES | 20 | How often to scan (in minutes) |
| TOTAL_CAPITAL_USD | 1000 | For future stake-sizing features |

Tighten thresholds to reduce noise. Loosen them to catch more marginal deals.

---

## Expanding the watchlist

Start with 10–20 products you already know sell well on Amazon.
Good sources for ASIN ideas:
- Keepa movers list (keepa.com → Top Movers)
- Amazon Best Sellers in categories you know
- eBay "Sold listings" filter — search popular items, sort by most sold
- Retail arbitrage Facebook groups and Discord servers

---

## Important notes

1. Liquidation.com prices are **lot prices** — always verify per-unit cost before buying.
2. eBay sold prices are the **median of last 10 sold** — not guaranteed future price.
3. Amazon prices change. Always verify the current live price before purchasing.
4. Start in paper trading mode for at least 1 week before buying anything.
5. Keep your `.env` file private — never commit it to GitHub.
