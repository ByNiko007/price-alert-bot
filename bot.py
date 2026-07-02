import asyncio
import logging
import os
import aiohttp
from aiohttp import web
from telegram import Bot

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHAT_ID = os.environ.get("CHAT_ID", "")
THRESHOLD = 1000
last_price = None


async def get_price() -> float:
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            data = await resp.json()
            return data["bitcoin"]["usd"]


async def check_price(bot: Bot):
    global last_price
    try:
        current = await get_price()
        if last_price is None:
            last_price = current
            logger.info(f"Başlanğıc qiymət: ${current:,.0f}")
            return

        diff = current - last_price
        if abs(diff) >= THRESHOLD:
            direction = "🚀 YUXARI" if diff > 0 else "📉 AŞAĞI"
            msg = (
                f"⚠️ <b>Bitcoin Qiymət Alerti!</b>\n\n"
                f"{direction}\n"
                f"💰 Cari qiymət: <b>${current:,.0f}</b>\n"
                f"📊 Dəyişiklik: <b>${diff:+,.0f}</b>\n\n"
                f"#Bitcoin #BTC #Alert"
            )
            await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="HTML")
            logger.info(f"Alert! ${last_price:,.0f} → ${current:,.0f}")
            last_price = current
    except Exception as e:
        logger.error(f"Xəta: {e}")


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
        await check_price(bot)
        await asyncio.sleep(60)  # Hər dəqiqə yoxla


if __name__ == "__main__":
    asyncio.run(main())
