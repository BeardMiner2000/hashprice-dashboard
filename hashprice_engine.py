import pandas as pd
import requests
from datetime import datetime
import pytz

PACIFIC = pytz.timezone("US/Pacific")
COINMETRICS_CSV = "https://raw.githubusercontent.com/coinmetrics/data/master/csv/btc.csv"
BLOCK_SUBSIDY_BTC = 3.125  # current subsidy after 2024 halving


def _safe_get_json(url: str, timeout: int = 8):
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.json()


def fetch_data():
    """
    Historical daily network + economics from Coin Metrics public CSV.

    Metrics used:
      - PriceUSD   : daily BTC USD price
      - HashRate   : network hashrate estimate (TH/s in Coin Metrics docs)
      - IssTotNtv  : BTC issuance per day (subsidy only)
      - FeeTotNtv  : BTC fees per day
    """
    df = pd.read_csv(COINMETRICS_CSV)
    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    df = df[["time", "PriceUSD", "HashRate", "IssTotNtv", "FeeTotNtv"]].dropna()
    df = df.sort_values("time")

    # Coin Metrics documents BTC HashRate in TH/s for this metric.
    # Convert TH/s -> PH/s for dashboard units.
    df["HashRate_PH"] = df["HashRate"] / 1000.0

    # Economics per day.
    df["issuance_btc_day"] = df["IssTotNtv"]
    df["fees_btc_day"] = df["FeeTotNtv"]
    df["btc_revenue"] = df["issuance_btc_day"] + df["fees_btc_day"]
    df["usd_revenue"] = df["btc_revenue"] * df["PriceUSD"]

    # Hashprice = USD revenue per PH/day.
    df["hashprice_1d"] = df["usd_revenue"] / df["HashRate_PH"]
    df["hashprice_7d"] = (
        df["usd_revenue"].rolling(7).mean() /
        df["HashRate_PH"].rolling(7).mean()
    )
    return df.dropna()


def fetch_live_price():
    """Try a couple of price sources and return spot BTC/USD."""
    sources = [
        ("CoinGecko", "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"),
        ("Coinbase", "https://api.coinbase.com/v2/prices/spot?currency=USD"),
    ]

    for source_name, url in sources:
        try:
            data = _safe_get_json(url)
            if "bitcoin" in data and "usd" in data["bitcoin"]:
                return float(data["bitcoin"]["usd"]), source_name
            if "data" in data and "amount" in data["data"]:
                return float(data["data"]["amount"]), source_name
        except Exception:
            continue

    raise RuntimeError("Live price sources unavailable")


def fetch_spot_24h_average():
    """
    Return a 24h average BTC/USD spot using CoinGecko hourly market chart data.
    """
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=2&interval=hourly"
    data = _safe_get_json(url)
    prices = data.get("prices", [])
    if not prices:
        return None, None

    values = [float(point[1]) for point in prices[-24:]]
    if not values:
        return None, None

    return sum(values) / len(values), "CoinGecko 24h hourly average"


def fetch_live_hashrate_ph():
    """
    Attempt live-ish hashrate from Hashrate Index / Luxor style endpoint.
    Falls back to Coin Metrics daily estimate when unavailable.
    """
    candidates = [
        ("Hashrate Index", "https://data.hashrateindex.com/api/network-data/bitcoin/hashrate"),
    ]

    for source_name, url in candidates:
        try:
            data = _safe_get_json(url)
            if isinstance(data, dict):
                for key in ("hashrate_1d", "hashrate", "current_hashrate"):
                    if key in data and data[key] is not None:
                        val = float(data[key])
                        # Endpoint commonly returns EH/s. Convert to PH/s.
                        if val < 10_000:
                            return val * 1000.0, source_name
                        return val, source_name
        except Exception:
            continue

    return None, None


def fetch_hashrate_24h_stats():
    """
    Return current and 24h average Bitcoin network hashrate from mempool.space.

    The endpoint reports hashes/second. Convert to PH/s.
    """
    try:
        data = _safe_get_json("https://mempool.space/api/v1/mining/hashrate/24h")
        current_hashrate = float(data.get("currentHashrate", 0))
        rows = data.get("hashrates", [])
        avg_hashrate = float(rows[-1]["avgHashrate"]) if rows else 0.0

        if current_hashrate <= 0 or avg_hashrate <= 0:
            return None, None, None

        current_ph = current_hashrate / 1_000_000_000_000_000.0
        avg_ph = avg_hashrate / 1_000_000_000_000_000.0
        return current_ph, avg_ph, "mempool.space 24h average"
    except Exception:
        return None, None, None


def fetch_live_fee_btc_day():
    """
    Estimate daily BTC fees from mempool projected blocks.
    This is intentionally approximate, so it is displayed as an estimate only.
    """
    try:
        blocks = _safe_get_json("https://mempool.space/api/v1/fees/mempool-blocks")
        if not isinstance(blocks, list) or not blocks:
            return None, None

        sample = blocks[:3]
        fee_btc_per_block = []
        for block in sample:
            median_fee = float(block.get("medianFee", 0))
            vsize = float(block.get("blockVSize", 0))
            sats = median_fee * vsize
            fee_btc_per_block.append(sats / 100_000_000.0)

        avg_fee_btc_per_block = sum(fee_btc_per_block) / len(fee_btc_per_block)
        return avg_fee_btc_per_block * 144.0, "mempool.space"
    except Exception:
        return None, None


def calculate():
    df = fetch_data()
    last = df.iloc[-1]
    prev = df.iloc[-2]
    trend = df.tail(14).copy()

    live_price, price_source = fetch_live_price()
    spot_avg_24h, spot_avg_24h_source = fetch_spot_24h_average()
    current_hashrate_24h_ph, avg_hashrate_24h_ph, hashrate_24h_source = fetch_hashrate_24h_stats()
    live_hashrate_ph, hashrate_source = fetch_live_hashrate_ph()
    fee_btc_day_live, fee_source = fetch_live_fee_btc_day()

    # Prefer explicit 24h/current stats when available, otherwise fall back.
    if current_hashrate_24h_ph is not None:
        network_hashrate_ph = float(current_hashrate_24h_ph)
        hashrate_source = hashrate_24h_source
    elif live_hashrate_ph:
        network_hashrate_ph = float(live_hashrate_ph)
        hashrate_source = hashrate_source
    else:
        network_hashrate_ph = float(last["HashRate_PH"])
        hashrate_source = "Coin Metrics daily"

    fee_btc_day = float(fee_btc_day_live) if fee_btc_day_live is not None else float(last["fees_btc_day"])
    fee_source = fee_source or "Coin Metrics daily"

    issuance_btc_day = float(last["issuance_btc_day"])
    btc_revenue_day = issuance_btc_day + fee_btc_day
    realtime = (btc_revenue_day * live_price) / network_hashrate_ph
    pct_vs_7d = ((realtime / float(last["hashprice_7d"])) - 1.0) * 100.0

    prev_hashprice_7d = float(prev["hashprice_7d"])
    hashprice_7d_change_pct = ((float(last["hashprice_7d"]) / prev_hashprice_7d) - 1.0) * 100.0 if prev_hashprice_7d else None

    spot_avg_24h = float(spot_avg_24h) if spot_avg_24h is not None else None
    spot_vs_24h_pct = ((live_price / spot_avg_24h) - 1.0) * 100.0 if spot_avg_24h else None

    hashrate_avg_24h_ph = float(avg_hashrate_24h_ph) if avg_hashrate_24h_ph is not None else None
    hashrate_vs_24h_pct = ((network_hashrate_ph / hashrate_avg_24h_ph) - 1.0) * 100.0 if hashrate_avg_24h_ph else None

    hashprice_rt_avg_24h = None
    hashprice_rt_vs_24h_pct = None
    if spot_avg_24h and hashrate_avg_24h_ph:
        hashprice_rt_avg_24h = (btc_revenue_day * spot_avg_24h) / hashrate_avg_24h_ph
        if hashprice_rt_avg_24h:
            hashprice_rt_vs_24h_pct = ((realtime / hashprice_rt_avg_24h) - 1.0) * 100.0

    fee_pct = (fee_btc_day / btc_revenue_day) * 100.0 if btc_revenue_day else 0.0
    fee_pct_daily = (float(last["fees_btc_day"]) / float(last["btc_revenue"])) * 100.0 if float(last["btc_revenue"]) else None
    fee_pct_vs_daily_pct = ((fee_pct / fee_pct_daily) - 1.0) * 100.0 if fee_pct_daily else None
    timestamp = datetime.now(PACIFIC).strftime("%Y-%m-%d %H:%M:%S %Z")

    return {
        "timestamp": timestamp,
        "spot": float(live_price),
        "spot_source": price_source,
        "hashprice_rt": float(realtime),
        "hashprice_rt_avg_24h": float(hashprice_rt_avg_24h) if hashprice_rt_avg_24h is not None else None,
        "hashprice_rt_vs_24h_pct": float(hashprice_rt_vs_24h_pct) if hashprice_rt_vs_24h_pct is not None else None,
        "hashprice_1d": float(last["hashprice_1d"]),
        "hashprice_7d": float(last["hashprice_7d"]),
        "hashprice_7d_prev": float(prev_hashprice_7d),
        "hashprice_7d_change_pct": float(hashprice_7d_change_pct) if hashprice_7d_change_pct is not None else None,
        "pct_vs_7d": float(pct_vs_7d),
        "trend": trend[["time", "hashprice_1d"]],
        "network_hashrate_ph": float(network_hashrate_ph),
        "network_hashrate_source": hashrate_source,
        "network_hashrate_24h_avg_ph": float(hashrate_avg_24h_ph) if hashrate_avg_24h_ph is not None else None,
        "network_hashrate_vs_24h_pct": float(hashrate_vs_24h_pct) if hashrate_vs_24h_pct is not None else None,
        "bitcoin_per_block": float(BLOCK_SUBSIDY_BTC),
        "issuance_btc_day": float(issuance_btc_day),
        "fee_btc_day": float(fee_btc_day),
        "fee_source": fee_source,
        "btc_revenue_day": float(btc_revenue_day),
        "fee_pct": float(fee_pct),
        "fee_pct_daily": float(fee_pct_daily) if fee_pct_daily is not None else None,
        "fee_pct_vs_daily_pct": float(fee_pct_vs_daily_pct) if fee_pct_vs_daily_pct is not None else None,
        "spot_avg_24h": float(spot_avg_24h) if spot_avg_24h is not None else None,
        "spot_avg_24h_source": spot_avg_24h_source,
        "spot_vs_24h_pct": float(spot_vs_24h_pct) if spot_vs_24h_pct is not None else None,
        "source_coinmetrics": COINMETRICS_CSV,
        "comparison_logic": {
            "hashprice_rt": "current realtime vs last 24h average inputs",
            "spot": "current spot vs last 24h average spot",
            "network_hashrate_ph": "current hashrate vs last 24h average hashrate",
            "hashprice_7d": "current 7d window vs previous 7d window",
            "fee_pct": "current fee share vs latest daily Coin Metrics row",
        },
    }
