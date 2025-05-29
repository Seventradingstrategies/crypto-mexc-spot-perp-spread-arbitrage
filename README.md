# crypto-mexc-spot-perp-spread-arbitrage
Real-time MEXC SPOT vs PERP Arbitrage Dashboard powered by Panel + WebSocket + CCXT Pro. Includes premium %, funding rate, true arbitrage, and multi-token selection.

# MEXC Premium Dashboard (v1.23)

🚀 Real-time crypto arbitrage dashboard comparing SPOT vs PERP pairs on MEXC using WebSockets.

## Features

- ✅ Real-time Order Book Mid Prices (Spot & Perp)
- ✅ Live Premium % (Perp Mid - Spot Mid)
- ✅ Directional Arbitrage Detection (Long/Short Opps)
- ✅ Funding Rate Display
- ✅ True Premium Spread (based on executable quotes)
- ✅ Multi-token selection from 3000+ PERP/USDT
- ✅ Built with Python Panel + CCXT Pro

## Screenshot 
SS -- https://paste.pics/4ec1839b1e93d33b30d810de7638d20b

## CONS AND IMPROVEMENT
- Please select only up to 5 coins, more selection will results in lagness and unworkable condition. 

## Getting Started

Clone this repo and run:

pip install -r requirements.txt
python panelv1.23.py

Open `http://localhost:8080` in your browser.











