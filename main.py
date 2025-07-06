import asyncio
from datetime import datetime, timezone
from telegram import Bot
import ccxt.async_support as ccxt

# ————————— PARAMÈTRES
TOKEN = "7374774625:AAHz6Livg34KQwvlbTlZNeFowjUaQemiQGI"
CHAT_ID = 805187048

SYMBOL = "BTC/USDT"
TP_PERCENT = 0.60
SL_PERCENT = 0.20

exchange = ccxt.binanceusdm({'enableRateLimit': True})

def get_session_now():
    utc = datetime.now(timezone.utc).hour
    if 0 <= utc < 8: return "Asiatique"
    if 8 <= utc < 13: return "Européenne"
    if 13 <= utc < 21: return "Américaine"
    return "Hors session"

async def fetch_imbalance_and_price():
    ob = await exchange.fetch_order_book(SYMBOL, limit=100)
    bids = sum(price * amount for price, amount in ob['bids'])
    asks = sum(price * amount for price, amount in ob['asks'])
    total = bids + asks
    buy_pct = bids / total * 100 if total else 0
    sell_pct = asks / total * 100 if total else 0

    # Estimation du prix d'entrée comme moyenne des meilleurs bid/ask
    bid_price = ob['bids'][0][0] if ob['bids'] else 0
    ask_price = ob['asks'][0][0] if ob['asks'] else 0
    entry_price = (bid_price + ask_price) / 2 if bid_price and ask_price else 0

    return round(buy_pct, 1), round(sell_pct, 1), round(entry_price, 2)

async def send_message(text):
    bot = Bot(TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=text)

async def main_loop():
    while True:
        session = get_session_now()
        buy_pct, sell_pct, entry = await fetch_imbalance_and_price()

        if buy_pct > 70:
            direction = "LONG"
            signal = "📈 Signal LONG"
            tp_price = entry * (1 + TP_PERCENT / 100)
            sl_price = entry * (1 - SL_PERCENT / 100)
        elif sell_pct > 70:
            direction = "SHORT"
            signal = "📉 Signal SHORT"
            tp_price = entry * (1 - TP_PERCENT / 100)
            sl_price = entry * (1 + SL_PERCENT / 100)
        else:
            direction = None
            signal = "⚠️ Neutre"

        msg = f"📊 {SYMBOL} Futures\n🕐 Session : {session}\n{signal}\n"
        msg += f"Acheteurs : {buy_pct}% | Vendeurs : {sell_pct}%\n"

        if direction:
            msg += (
                f"💰 Prix d'entrée estimé : {entry} USDT\n"
                f"🎯 TP : {round(tp_price, 2)} USDT (+{TP_PERCENT}%)\n"
                f"🛡️ SL : {round(sl_price, 2)} USDT (-{SL_PERCENT}%)\n"
            )

        msg += f"🕓 {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}"

        await send_message(msg)
        print("Envoyé :", msg)

        now = datetime.now(timezone.utc)
        sleep_seconds = (60 - now.minute) * 60 - now.second + 1
        await asyncio.sleep(sleep_seconds)

if __name__ == "__main__":
    asyncio.run(main_loop())
