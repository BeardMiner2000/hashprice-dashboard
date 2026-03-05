import pandas as pd
import requests
from datetime import datetime
import pytz

PACIFIC = pytz.timezone("US/Pacific")

COINMETRICS_CSV = "https://raw.githubusercontent.com/coinmetrics/data/master/csv/btc.csv"

def fetch_data():
    """
    Pull daily network + economics from Coin Metrics public CSV.
    We use:
      - PriceUSD (daily close-ish)
      - HashRate (network hashrate, Coin Metrics)
      - IssTotNtv (BTC issuance)
      - FeeTotNtv (BTC fees)
    """
    df = pd.read_csv(COINMETRICS_CSV)
    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    df = df[["time", "PriceUSD", "HashRate", "IssTotNtv", "FeeTotNtv"]].dropna()
    df = df.sort_values("time")

    # IMPORTANT:
    # The dashboard historically used: HashRate_PH = HashRate / 1000
    # (this keeps hashprice in the expected ~$20–$60 / PH / day range for this dataset).
    df["HashRate_PH"] = df["HashRate"] / 1000.0

    df["btc_revenue"] = df["IssTotNtv"] + df["FeeTotNtv"]
    df["usd_revenue"] = df["btc_revenue"] * df["PriceUSD"]

    df["hashprice_1d"] = df["usd_revenue"] / df["HashRate_PH"]
    df["hashprice_7d"] = (
        df["usd_revenue"].rolling(7).mean() /
        df["HashRate_PH"].rolling(7).mean()
    )

    return df.dropna()

def fetch_live_price():
    sources = [
        ("CoinGecko", "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"),
        ("Coinbase", "https://api.coinbase.com/v2/prices/spot?currency=USD"),
    ]

    for _, url in sources:
        try:
            r = requests.get(url, timeout=8)
            if r.status_code != 200:
                continue
            data = r.json()
            if "bitcoin" in data and "usd" in data["bitcoin"]:
                return float(data["bitcoin"]["usd"])
            if "data" in data and "amount" in data["data"]:
                return float(data["data"]["amount"])
        except Exception:
            continue

    raise RuntimeError("Live price sources unavailable")

def calculate():
    df = fetch_data()
    last = df.iloc[-1]
    trend = df.tail(14).copy()

    live_price = fetch_live_price()

    # Realtime hashprice = today's BTC revenue per PH * live BTC spot price.
    realtime = (last["btc_revenue"] * live_price) / last["HashRate_PH"]

    pct_vs_7d = ((realtime / last["hashprice_7d"]) - 1.0) * 100.0

    timestamp = datetime.now(PACIFIC).strftime("%Y-%m-%d %H:%M:%S %Z")

    # Extra "network state" metrics derived from the same Coin Metrics daily row.
    fee_pct = (last["FeeTotNtv"] / last["btc_revenue"]) * 100.0 if last["btc_revenue"] else 0.0

    return {
        "timestamp": timestamp,
        "spot": live_price,
        "hashprice_rt": float(realtime),
        "hashprice_1d": float(last["hashprice_1d"]),
        "hashprice_7d": float(last["hashprice_7d"]),
        "pct_vs_7d": float(pct_vs_7d),
        "trend": trend[["time", "hashprice_1d"]],
        # Network State (approx, from Coin Metrics)
        "network_hashrate_raw": float(last["HashRate"]),
        "network_hashrate_ph": float(last["HashRate_PH"]),
        "block_reward": float(last["IssTotNtv"]),
        "fee_btc": float(last["FeeTotNtv"]),
        "fee_pct": float(fee_pct),
        "source_coinmetrics": COINMETRICS_CSV,
    }
