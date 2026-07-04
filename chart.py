import io
import aiohttp
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timezone


async def get_chart_data(symbol: str) -> list:
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=1h&outputsize=24&apikey={{TWELVE_API_KEY}}"
    return []


async def generate_chart(name: str, symbol: str, current_price: float, diff: float, api_key: str) -> io.BytesIO:
    try:
        url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=1h&outputsize=24&apikey={api_key}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                data = await resp.json()

        values = data.get("values", [])
        if not values:
            return None

        times = [datetime.strptime(v["datetime"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc) for v in reversed(values)]
        prices = [float(v["close"]) for v in reversed(values)]

        color = "#00ff88" if diff >= 0 else "#ff4444"
        bg_color = "#1a1a2e"

        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)

        ax.plot(times, prices, color=color, linewidth=2)
        ax.fill_between(times, prices, alpha=0.2, color=color)

        ax.set_title(f"{name} - Son 24 Saat", color="white", fontsize=14, pad=15)
        ax.set_ylabel("Qiymət (USD)", color="white")
        ax.tick_params(colors="white")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=4))

        for spine in ax.spines.values():
            spine.set_edgecolor("#444")

        ax.grid(color="#333", linestyle="--", linewidth=0.5)

        direction = "▲" if diff >= 0 else "▼"
        ax.text(0.02, 0.95, f"${current_price:,.2f}  {direction} ${abs(diff):,.2f}",
                transform=ax.transAxes, color=color, fontsize=12,
                verticalalignment='top', bbox=dict(facecolor=bg_color, alpha=0.8))

        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', facecolor=bg_color, dpi=100)
        buf.seek(0)
        plt.close()
        return buf

    except Exception as e:
        return None
