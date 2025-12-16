import requests
import time
from datetime import datetime, timezone

BINANCE_API = "https://api.binance.com/api/v3"
FEE = 0.001  # 0.1% per trade


# -----------------------------
# Helper Functions
# -----------------------------
def get_price(symbol: str):
    try:
        url = f"{BINANCE_API}/ticker/price?symbol={symbol}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return float(r.json()["price"])
    except Exception:
        pass
    return None


def get_coins(limit=40):
    url = f"{BINANCE_API}/exchangeInfo"
    data = requests.get(url, timeout=10).json()

    coins = []
    for s in data["symbols"]:
        if s["quoteAsset"] == "BNB" and s["status"] == "TRADING":
            base = s["baseAsset"]
            if base not in {"BNB", "USDT", "BUSD", "USDC"}:
                coins.append(base)

    return coins[:limit]


# -----------------------------
# Core Logic
# -----------------------------
def scan_triangular_arbitrage(capital_usdt=100.0):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    print("🕒 Timestamp:", timestamp)
    print(f"💰 Initial Capital: {capital_usdt} USDT")
    print(f"💸 Trading Fee: {FEE * 100}% per transaction\n")

    intermediate_price = get_price("BNBUSDT")
    if not intermediate_price:
        print("❌ Failed to fetch intermediate asset price")
        return

    print("🔍 Searching for arbitrage opportunities...\n")

    best = None

    for coin in get_coins():
        coin_bnb_price = get_price(f"{coin}BNB")
        coin_usdt_price = get_price(f"{coin}USDT")

        if not coin_bnb_price or not coin_usdt_price:
            continue

        # Step 1: USDT → BNB
        bnb_amount = (capital_usdt / intermediate_price) * (1 - FEE)

        # Step 2: BNB → COIN
        coin_amount = (bnb_amount / coin_bnb_price) * (1 - FEE)

        # Step 3: COIN → USDT
        final_usdt = (coin_amount * coin_usdt_price) * (1 - FEE)

        profit_pct = ((final_usdt - capital_usdt) / capital_usdt) * 100

        if best is None or profit_pct > best["profit_pct"]:
            best = {
                "coin": coin,
                "bnb_usdt_price": intermediate_price,
                "coin_bnb_price": coin_bnb_price,
                "coin_usdt_price": coin_usdt_price,
                "bnb_amount": bnb_amount,
                "coin_amount": coin_amount,
                "final_usdt": final_usdt,
                "profit_pct": profit_pct,
            }

        time.sleep(0.15)

    if not best:
        print("❌ No arbitrage opportunity found")
        return

    # -----------------------------
    # Status before result
    # -----------------------------
    print("⏳ Searching completed. Best opportunity identified.\n")

    # -----------------------------
    # Final Output
    # -----------------------------
    print("🏆 ARBITRAGE OPPORTUNITY DETECTED")
    print("────────────────────────────────")
    print("📊 Current Market Prices")
    print("------------------------")
    print(f"BNB/USDT        : {best['bnb_usdt_price']}")
    print(f"{best['coin']}/BNB      : {best['coin_bnb_price']}")
    print(f"{best['coin']}/USDT     : {best['coin_usdt_price']}\n")

    print(
        f"1️⃣ Buy BNB using USDT\n"
        f"   {capital_usdt} USDT → {best['bnb_amount']} BNB\n"
    )

    print(
        f"2️⃣ Buy {best['coin']} using BNB\n"
        f"   {best['bnb_amount']} BNB → {best['coin_amount']} {best['coin']}\n"
    )

    print(
        f"3️⃣ Sell {best['coin']} back to USDT\n"
        f"   {best['coin_amount']} {best['coin']} → {best['final_usdt']} USDT\n"
    )

    print(f"📈 Estimated Profit: {best['profit_pct']} %")
    print("⚠️ Theoretical calculation based on last price only")
    print("⚠️ Slippage, depth, and latency are NOT considered")
    print("⚠️ Educational purpose only")


# -----------------------------
# Entry Point
# -----------------------------
if __name__ == "__main__":
    scan_triangular_arbitrage(capital_usdt=100)
