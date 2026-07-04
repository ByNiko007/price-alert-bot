import asyncio
import logging
import os
import aiohttp
from aiohttp import web
from telegram import Bot
from chart import generate_chart

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHAT_ID = os.environ.get("CHAT_ID", "")
TWELVE_API_KEY = os.environ.get("TWELVE_API_KEY", "")

COINS = {
    "bitcoin": {"name": "Bitcoin", "symbol": "BTC/USD", "threshold": 50},
    "ethereum": {"name": "Ethereum", "symbol": "ETH/USD", "threshold": 10},
    "solana": {"name": "Solana", "symbol": "SOL/USD", "threshold": 1},
    "binancecoin": {"name": "BNB", "symbol": "BNB/USD", "threshold": 1},
}

STOCKS = {
    "AAPL": {"name": "Apple", "threshold": 10},
    "MSFT": {"name": "Microsoft", "threshold": 15},
    "NVDA": {"name": "Nvidia", "threshold": 15},
    "AMZN": {"name": "Amazon", "threshold": 10},
    "GOOGL": {"name": "Google", "threshold": 10},
    "META": {"name": "Meta", "threshold": 15},
    "TSLA": {"name": "Tesla", "threshold": 15},
    "BRK/B": {"name": "Berkshire Hathaway", "threshold": 5},
    "JPM": {"name": "JP Morgan", "threshold": 10},
    "SPCX": {"name": "SpaceX", "threshold": 10},
    "MU": {"name": "Micron", "threshold": 5},
}

last_crypto_prices = {}
last_stock_prices = {}


async def get_crypto_prices() -> dict:
    symbols = ",".join([info["symbol"] for info in COINS.values()])
    url = f"https://api.twelvedata.com/price?symbol={symbols}&apikey={TWELVE_API_KEY}"
    result = {}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                data = await resp.json()
                for coin_id, info in COINS.items():
                    symbol = info["symbol"]
                    if symbol in data and "price" in data[symbol]:
                        result[coin_id] = {"usd": float(data[symbol]["price"])}
                        logger.info(f"{coin_id}: ${float(data[symbol]['price']):,.2f}")
    except Exception as e:
        logger.error(f"Kripto xəta: {e}")
    return result


async def get_stock_prices() -> dict:
    symbols = ",".join(STOCKS.keys())
    url = f"https://api.twelvedata.com/price?symbol={symbols}&apikey={TWELVE_API_KEY}"
    result = {}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                data = await resp.json()
                for symbol in STOCKS.keys():
                    if symbol in data and "price" in data[symbol]:
                        result[symbol] = float(data[symbol]["price"])
                        logger.info(f"{symbol}: ${float(data[symbol]['price']):,.2f}")
    except Exception as e:
        logger.error(f"Səhm xəta: {e}")
    return result


async def check_crypto(bot: Bot):
    global last_crypto_prices
    try:
        data = await get_crypto_prices()
        if not data:
            return
        for coin_id, info in COINS.items():
            if coin_id not in data:
                continue
            current = data[coin_id]["usd"]
            if coin_id not in last_crypto_prices:
                last_crypto_prices[coin_id] = current
                logger.info(f"{info['name']}: ${current:,.2f}")
                continue
            diff = current - last_crypto_prices[coin_id]
            logger.info(f"{info['name']}: ${current:,.2f} (fərq: ${diff:+,.2f})")
            if abs(diff) >= info["threshold"]:
                direction = "🚀 YUXARI" if diff > 0 else "📉 AŞAĞI"
                caption = (
                    f"⚠️ <b>{info['name']} Alerti!</b>\n\n"
                    f"{direction}\n"
                    f"💰 Qiymət: <b>${current:,.2f}</b>\n"
                    f"📊 Dəyişiklik: <b>${diff:+,.2f}</b>\n\n"
                    f"#BTC #Kripto #Alert"
                )
                chart = await generate_chart(info['name'], info['symbol'], current, diff, TWELVE_API_KEY)
                if chart:
                    await bot.send_photo(chat_id=CHAT_ID, photo=chart, caption=caption, parse_mode="HTML")
                else:
                    await bot.send_message(chat_id=CHAT_ID, text=caption, parse_mode="HTML")
                last_crypto_prices[coin_id] = current
    except Exception as e:
        logger.error(f"Kripto yoxlama xəta: {e}")


async def check_stocks(bot: Bot):
    global last_stock_prices
    try:
        data = await get_stock_prices()
        for symbol, info in STOCKS.items():
            if symbol not in data:
                continue
            current = data[symbol]
            if symbol not in last_stock_prices:
                last_stock_prices[symbol] = current
                logger.info(f"{info['name']} ({symbol}): ${current:,.2f}")
                continue
            diff = current - last_stock_prices[symbol]
            if abs(diff) >= info["threshold"]:
                direction = "🚀 YUXARI" if diff > 0 else "📉 AŞAĞI"
                caption = (
                    f"⚠️ <b>{info['name']} ({symbol}) Alerti!</b>\n\n"
                    f"{direction}\n"
                    f"💰 Qiymət: <b>${current:,.2f}</b>\n"
                    f"📊 Dəyişiklik: <b>${diff:+,.2f}</b>\n\n"
                    f"#{symbol} #Səhm #Alert"
                )
                chart = await generate_chart(info['name'], symbol, current, diff, TWELVE_API_KEY)
                if chart:
                    await bot.send_photo(chat_id=CHAT_ID, photo=chart, caption=caption, parse_mode="HTML")
                else:
                    await bot.send_message(chat_id=CHAT_ID, text=caption, parse_mode="HTML")
                last_stock_prices[symbol] = current
    except Exception as e:
        logger.error(f"Səhm yoxlama xəta: {e}")


async def health(request):
    return web.Response(text="OK")


async def main():
    bot = Bot(token=BOT_TOKEN)
    logger.info("Qiymət alert botu işə düşdü!")

    app = web.Application()
    app.router.add_get("/", health)
    port = int(os.environ.get("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    while True:
        await check_crypto(bot)
        await check_stocks(bot)
        await asyncio.sleep(120)


if __name__ == "__main__":
    asyncio.run(main())
