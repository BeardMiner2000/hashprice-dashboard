import pandas as pd
import requests
from datetime import datetime
import pytz

PACIFIC = pytz.timezone("US/Pacific")

COINMETRICS_CSV = "https://raw.githubusercontent.com/coinmetrics/data/master/csv/btc.csv"


def fetch_data():

    df = pd.read_csv(COINMETRICS_CSV)

    df["time"] = pd.to_datetime(df["time"], errors="coerce")

    df = df[
        ["time", "PriceUSD", "HashRate", "IssTotNtv", "FeeTotNtv"]
    ].dropna()

    df = df.sort_values("time")

    # Convert network hashrate correctly
    # CoinMetrics HashRate = hashes per second
    # 1 PH = 1e15 hashes
    df["HashRate_PH"] = df["HashRate"] / 1e15

    # BTC earned per day by network
    df["btc_revenue"] = df["IssTotNtv"] + df["FeeTotNtv"]

    # USD revenue for network
    df["usd_revenue"] = df["btc_revenue"] * df["PriceUSD"]

    # Hashprice calculations
    df["hashprice_1d"] = df["usd_revenue"] / df["HashRate_PH"]

    df["hashprice_7d"] = (
        df["usd_revenue"].rolling(7).mean()
        / df["HashRate_PH"].rolling(7).mean()
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

    # realtime hashprice using live BTC price
    realtime = (last["btc_revenue"] * live_price) / last["HashRate_PH"]

    pct_vs_7d = ((realtime / last["hashprice_7d"]) - 1.0) * 100.0

    timestamp = datetime.now(PACIFIC).strftime("%Y-%m-%d %H:%M:%S %Z")

    fee_pct = (
        (last["FeeTotNtv"] / last["btc_revenue"]) * 100.0
        if last["btc_revenue"]
        else 0.0
    )

    return {

        "timestamp": timestamp,

        "spot": live_price,

        "hashprice_rt": float(realtime),

        "hashprice_1d": float(last["hashprice_1d"]),

        "hashprice_7d": float(last["hashprice_7d"]),

        "pct_vs_7d": float(pct_vs_7d),

        "trend": trend[["time", "hashprice_1d"]],

        # network state metrics

        "network_hashrate_raw": float(last["HashRate"]),

        "network_hashrate_ph": float(last["HashRate_PH"]),

        "block_reward": float(last["IssTotNtv"]),

        "fee_btc": float(last["FeeTotNtv"]),

        "fee_pct": float(fee_pct),

        "source_coinmetrics": COINMETRICS_CSV,
    }
