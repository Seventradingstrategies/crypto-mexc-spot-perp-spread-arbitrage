# Version 1.023 — True Premium & % Added

import panel as pn
pn.extension('tabulator')

import ccxt.pro as ccxtpro
import ccxt
import asyncio
import threading
import pandas as pd
import time
import sys

# Arbitrage logic
def determine_true_arbitrage(spot_bid, spot_ask, perp_bid, perp_ask):
    try:
        if perp_bid and spot_ask and perp_bid > spot_ask:
            return '🟢 SHORT PERP (BID) / LONG SPOT (ASK)'
        elif spot_bid and perp_ask and spot_bid > perp_ask:
            return '🔴 SHORT SPOT (ASK) / LONG PERP (BID)'
        else:
            return '🟰 NEUTRAL'
    except:
        return '🟰 NEUTRAL'

# Token fetcher
async def fetch_token(symbol, spot_ws, perp_ws, rest, funding_cache, funding_ts):
    row = {'Token': symbol.replace('/USDT', '')}
    spot_symbol = symbol
    perp_symbol = f"{symbol}:USDT"
    symbol_key = symbol.replace('/USDT', '_USDT')

    try:
        ob_spot = await spot_ws.watch_order_book(spot_symbol)
        sbid, sbid_qty = ob_spot['bids'][0][:2] if ob_spot['bids'] else (None, None)
        sask, sask_qty = ob_spot['asks'][0][:2] if ob_spot['asks'] else (None, None)
        spot_mid = (sbid + sask) / 2 if sbid and sask else None

        ob_perp = await perp_ws.watch_order_book(perp_symbol)
        pbid, pbid_qty = ob_perp['bids'][0][:2] if ob_perp['bids'] else (None, None)
        pask, pask_qty = ob_perp['asks'][0][:2] if ob_perp['asks'] else (None, None)
        perp_mid = (pbid + pask) / 2 if pbid and pask else None

        premium = perp_mid - spot_mid if spot_mid and perp_mid else None
        premium_pct = (premium / spot_mid * 100) if spot_mid and premium else None
        arbitrage = determine_true_arbitrage(sbid, sask, pbid, pask)

        # True Premium + %
        true_premium = None
        true_premium_pct = None
        try:
            if arbitrage == '🟢 SHORT PERP (BID) / LONG SPOT (ASK)' and pbid and sask:
                true_premium = pbid - sask
                true_premium_pct = (true_premium / sask * 100) if sask else None
            elif arbitrage == '🔴 SHORT SPOT (ASK) / LONG PERP (BID)' and sbid and pask:
                true_premium = sbid - pask
                true_premium_pct = (true_premium / pask * 100) if pask else None
            else:
                true_premium = 0
                true_premium_pct = 0
        except:
            true_premium = "-"
            true_premium_pct = "-"

        now_time = time.time()
        if now_time - funding_ts[0] > 30:
            try:
                funding = rest.fetch_funding_rate(symbol_key)
                funding_rate = funding['fundingRate'] * 100
                funding_cache[symbol_key] = f"{funding_rate:.4f}%"
            except:
                funding_cache[symbol_key] = "-"
            funding_ts[0] = now_time

        row.update({
            'Spot Bid': f"{sbid:.5f} ({sbid_qty:.5f})" if sbid else "-",
            'Spot Ask': f"{sask:.5f} ({sask_qty:.5f})" if sask else "-",
            'Spot Mid': f"{spot_mid:.5f}" if spot_mid else "-",
            'Perp Bid': f"{pbid:.5f} ({pbid_qty:.5f})" if pbid else "-",
            'Perp Ask': f"{pask:.5f} ({pask_qty:.5f})" if pask else "-",
            'Perp Mid': f"{perp_mid:.5f}" if perp_mid else "-",
            'Premium': f"{premium:.5f}" if premium else "-",
            'Premium %': f"{premium_pct:.5f}%" if premium_pct else "-",
            'True Premium': f"{true_premium:.5f}" if isinstance(true_premium, float) else "-",
            'True Premium %': f"{true_premium_pct:.5f}%" if isinstance(true_premium_pct, float) else "-",
            'Arbitrage': arbitrage,
            'Funding': funding_cache.get(symbol_key, "-"),
            'Updated': time.strftime("%H:%M:%S")
        })

    except Exception as e:
        print(f"❌ {symbol}: {e}")

    return row

# Async loop
async def main_loop(table, token_selector, funding_cache, funding_ts):
    spot_ws = ccxtpro.mexc({'options': {'defaultType': 'spot'}})
    perp_ws = ccxtpro.mexc({'options': {'defaultType': 'swap'}})
    rest = ccxt.mexc()

    await spot_ws.load_markets()
    await perp_ws.load_markets()

    while True:
        tokens = token_selector.value
        if not tokens:
            await asyncio.sleep(2)
            continue
        tasks = [fetch_token(sym, spot_ws, perp_ws, rest, funding_cache, funding_ts) for sym in tokens]
        data = await asyncio.gather(*tasks)
        table.value = pd.DataFrame(data)
        await asyncio.sleep(3)

# Start backend thread
def start_backend(table_widget, token_selector, funding_cache, funding_ts):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main_loop(table_widget, token_selector, funding_cache, funding_ts))

# Launch UI with dropdown of all PERP/USDT pairs, default 3 selected
def launch_dashboard():
    funding_cache = {}
    funding_ts = [0]

    async def get_perp_symbols():
        exchange = ccxtpro.mexc({'options': {'defaultType': 'swap'}})
        await exchange.load_markets()
        symbols = [s.split(':')[0] for s in exchange.symbols if '/USDT' in s and ':USDT' in s]
        await exchange.close()
        return sorted(list(set(symbols)))

    symbols = asyncio.run(get_perp_symbols())
    default_symbols = symbols[:3] if len(symbols) >= 3 else symbols

    token_selector = pn.widgets.MultiChoice(
        name="✅ Select Token Pairs (PERP/USDT only)",
        options=symbols,
        value=default_symbols,
        width=800
    )

    table_widget = pn.widgets.Tabulator(pd.DataFrame(columns=[
        'Token', 'Spot Bid', 'Spot Ask', 'Spot Mid',
        'Perp Bid', 'Perp Ask', 'Perp Mid',
        'Premium', 'Premium %', 'True Premium', 'True Premium %',
        'Arbitrage', 'Funding', 'Updated'
    ]), height=700, width=1750)

    dashboard = pn.Column(
        pn.pane.Markdown("## 🧠 MEXC Premium Dashboard v1.023 — True Premium & % Added"),
        pn.Row(token_selector),
        table_widget
    )

    threading.Thread(target=start_backend, args=(table_widget, token_selector, funding_cache, funding_ts), daemon=True).start()
    pn.serve(dashboard, port=8080, show=True)

if __name__ == '__main__':
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    launch_dashboard()
