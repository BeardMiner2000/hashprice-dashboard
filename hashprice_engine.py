import pandas as pd
import requests
from datetime import datetime
import pytz

PACIFIC = pytz.timezone("US/Pacific")

COINMETRICS_CSV = "https://raw.githubusercontent.com/coinmetrics/data/master/csv/btc.csv"

BLOCK_REWARD = 3.125
BLOCKS_PER_DAY = 144


def fetch_live_price():

    sources = [
        "https://api.coinbase.com/v2/prices/spot?currency=USD",
        "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",
    ]

    for url in sources:
        try:
            r = requests.get(url, timeout=8)
            if r.status_code != 200:
                continue

            data = r.json()

            if "data" in data:
                return float(data["data"]["amount"])

            if "bitcoin" in data:
                return float(data["bitcoin"]["usd"])

        except:
            pass

    raise RuntimeError("Price sources unavailable")


def fetch_network_state():

    difficulty = requests.get(
        "https://mempool.space/api/v1/difficulty-adjustment",
        timeout=10
    ).json()["currentDifficulty"]

    return difficulty


def calculate_hashrate_ph(difficulty):

    hashes_per_second = difficulty * 2**32 / 600
    ph = hashes_per_second / 1e15

    return ph


def fetch_coinmetrics_trend():

    df = pd.read_csv(COINMETRICS_CSV)

    df["time"] = pd.to_datetime(df["time"], errors="coerce")

    df = df[
        ["time", "PriceUSD", "HashRate", "IssTotNtv", "FeeTotNtv"]
    ].dropna()

    df = df.sort_values("time")

    df["HashRate_PH"] = df["HashRate"] / 1e15

    # daily miner revenue
    df["btc_revenue"] = (BLOCK_REWARD * BLOCKS_PER_DAY) + df["FeeTotNtv"]

    df["usd_revenue"] = df["btc_revenue"] * df["PriceUSD"]

    df["hashprice_1d"] = df["usd_revenue"] / df["HashRate_PH"]

    df["hashprice_7d"] = (
        df["usd_revenue"].rolling(7).mean()
        / df["HashRate_PH"].rolling(7).mean()
    )

    return df.dropna()


def calculate():

    df = fetch_coinmetrics_trend()

    last = df.iloc[-1]

    trend = df.tail(14).copy()

    live_price = fetch_live_price()

    difficulty = fetch_network_state()

    network_ph = calculate_hashrate_ph(difficulty)

    btc_revenue = (BLOCK_REWARD * BLOCKS_PER_DAY) + last["FeeTotNtv"]

    realtime = (btc_revenue * live_price) / network_ph

    pct_vs_7d = ((realtime / last["hashprice_7d"]) - 1.0) * 100

    timestamp = datetime.now(PACIFIC).strftime("%Y-%m-%d %H:%M:%S %Z")

    fee_pct = (last["FeeTotNtv"] / btc_revenue) * 100 if btc_revenue else 0

    return {

        "timestamp": timestamp,
        "spot": live_price,
        "hashprice_rt": float(realtime),
        "hashprice_1d": float(last["hashprice_1d"]),
        "hashprice_7d": float(last["hashprice_7d"]),
        "pct_vs_7d": float(pct_vs_7d),
        "trend": trend[["time", "hashprice_1d"]],
        "network_hashrate_raw": network_ph * 1e15,
        "network_hashrate_ph": network_ph,
        "block_reward": BLOCK_REWARD,
        "fee_btc": float(last["FeeTotNtv"]),
        "fee_pct": float(fee_pct),
        "source_coinmetrics": COINMETRICS_CSV,
    }

