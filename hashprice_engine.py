import pandas as pd
import requests
from datetime import datetime
import pytz

PACIFIC = pytz.timezone("US/Pacific")
COINMETRICS_CSV = "https://raw.githubusercontent.com/coinmetrics/data/master/csv/btc.csv"
BLOCK_SUBSIDY_BTC = 3.125  # current subsidy after 2024 halving
EXPECTED_BLOCKS_PER_DAY = 144.0
HASHES_PER_DIFFICULTY = 2 ** 32


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

    return None, None


def fetch_spot_24h_average():
    """
    Return a 24h average BTC/USD spot using CoinGecko hourly market chart data.
    """
    try:
        url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=2&interval=hourly"
        data = _safe_get_json(url)
        prices = data.get("prices", [])
        if not prices:
            return None, None

        values = [float(point[1]) for point in prices[-24:]]
        if not values:
            return None, None

        return sum(values) / len(values), "CoinGecko 24h hourly average"
    except Exception:
        pass

    try:
        data = _safe_get_json("https://api.exchange.coinbase.com/products/BTC-USD/candles?granularity=3600")
        if not isinstance(data, list) or not data:
            return None, None

        # Coinbase returns candles newest-first: [time, low, high, open, close, volume].
        closes = [float(candle[4]) for candle in data[:24] if len(candle) >= 5]
        if closes:
            return sum(closes) / len(closes), "Coinbase 24h hourly close average"
    except Exception:
        pass

    try:
        data = _safe_get_json("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true")
        bitcoin = data.get("bitcoin", {})
        current = float(bitcoin["usd"])
        change_pct = float(bitcoin["usd_24h_change"])
        prior = current / (1.0 + (change_pct / 100.0))
        return (current + prior) / 2.0, "CoinGecko 24h change midpoint estimate"
    except Exception:
        return None, None


def difficulty_to_ph(difficulty: float):
    return (float(difficulty) * HASHES_PER_DIFFICULTY / 600.0) / 1_000_000_000_000_000.0


def fetch_hashrate_24h_stats():
    """
    Return current and 24h average Bitcoin network hashrate from mempool.space.

    The endpoint reports hashes/second. Convert to PH/s.
    """
    try:
        data = _safe_get_json("https://mempool.space/api/v1/mining/hashrate/24h")
        current_hashrate = float(data.get("currentHashrate", 0))
        current_difficulty = float(data.get("currentDifficulty", 0))
        rows = data.get("hashrates", [])
        avg_hashrate = float(rows[-1]["avgHashrate"]) if rows else 0.0

        if current_hashrate <= 0 or avg_hashrate <= 0 or current_difficulty <= 0:
            raise RuntimeError("mempool hashrate payload missing values")

        current_ph = current_hashrate / 1_000_000_000_000_000.0
        avg_ph = avg_hashrate / 1_000_000_000_000_000.0
        difficulty_implied_ph = difficulty_to_ph(current_difficulty)
        return current_ph, avg_ph, current_difficulty, difficulty_implied_ph, "mempool.space"
    except Exception:
        pass

    try:
        data = _safe_get_json("https://api.blockchain.info/charts/hash-rate?timespan=2days&sampled=false&metadata=false&format=json")
        rows = data.get("values", [])
        if not rows:
            return None, None, None, None, None

        values_ph = [float(row["y"]) / 1000.0 for row in rows if row.get("y") is not None]
        if not values_ph:
            return None, None, None, None, None

        current_ph = values_ph[-1]
        avg_ph = sum(values_ph) / len(values_ph)
        return current_ph, avg_ph, None, None, "Blockchain.com 2-day chart average"
    except Exception:
        return None, None, None, None, None


def fetch_fee_144_block_average():
    """
    Estimate fee revenue with a trailing 144-block average, matching the
    standard hashprice-index treatment more closely than mempool projections.
    """
    try:
        blocks = _safe_get_json("https://mempool.space/api/v1/mining/blocks/fees/24h")
        if not isinstance(blocks, list) or not blocks:
            return None, None

        fee_btc_per_block = [
            float(block["avgFees"]) / 100_000_000.0
            for block in blocks[-144:]
            if block.get("avgFees") is not None
        ]
        if not fee_btc_per_block:
            return None, None

        avg_fee_btc_per_block = sum(fee_btc_per_block) / len(fee_btc_per_block)
        return avg_fee_btc_per_block * EXPECTED_BLOCKS_PER_DAY, "mempool.space 144-block fee average"
    except Exception:
        return None, None


def calculate():
    df = fetch_data()
    last = df.iloc[-1]
    prev = df.iloc[-2]
    trend = df.tail(14).copy()

    live_price, price_source = fetch_live_price()
    spot_avg_24h, spot_avg_24h_source = fetch_spot_24h_average()
    (
        observed_hashrate_ph,
        avg_hashrate_24h_ph,
        current_difficulty,
        difficulty_implied_hashrate_ph,
        hashrate_24h_source,
    ) = fetch_hashrate_24h_stats()
    fee_btc_day_live, fee_source = fetch_fee_144_block_average()

    live_price = float(live_price) if live_price is not None else float(last["PriceUSD"])
    price_source = price_source or "Coin Metrics daily"

    historical_data_date = last["time"].date()
    data_age_days = (datetime.now(PACIFIC).date() - historical_data_date).days

    network_hashrate_ph = (
        float(difficulty_implied_hashrate_ph)
        if difficulty_implied_hashrate_ph is not None
        else float(last["HashRate_PH"])
    )
    hashrate_source = (
        "mempool.space current difficulty implied at 10m target"
        if difficulty_implied_hashrate_ph is not None
        else "Coin Metrics daily"
    )

    fee_btc_day = float(fee_btc_day_live) if fee_btc_day_live is not None else float(last["fees_btc_day"])
    fee_source = fee_source or "Coin Metrics daily"

    issuance_btc_day = BLOCK_SUBSIDY_BTC * EXPECTED_BLOCKS_PER_DAY
    btc_revenue_day = issuance_btc_day + fee_btc_day
    realtime = (btc_revenue_day * live_price) / network_hashrate_ph
    pct_vs_7d = ((realtime / float(last["hashprice_7d"])) - 1.0) * 100.0

    prev_hashprice_7d = float(prev["hashprice_7d"])
    hashprice_7d_change_pct = ((float(last["hashprice_7d"]) / prev_hashprice_7d) - 1.0) * 100.0 if prev_hashprice_7d else None

    spot_avg_24h = float(spot_avg_24h) if spot_avg_24h is not None else None
    spot_avg_24h_source = spot_avg_24h_source or None
    spot_vs_24h_pct = ((live_price / spot_avg_24h) - 1.0) * 100.0 if spot_avg_24h else None

    hashrate_avg_24h_ph = float(avg_hashrate_24h_ph) if avg_hashrate_24h_ph is not None else None
    hashrate_vs_24h_pct = (
        ((network_hashrate_ph / hashrate_avg_24h_ph) - 1.0) * 100.0
        if network_hashrate_ph and hashrate_avg_24h_ph else None
    )

    hashprice_rt_avg_24h = None
    hashprice_rt_vs_24h_pct = None
    if spot_avg_24h and network_hashrate_ph:
        hashprice_rt_avg_24h = (btc_revenue_day * spot_avg_24h) / network_hashrate_ph
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
        "network_hashrate_current_ph": float(observed_hashrate_ph) if observed_hashrate_ph is not None else None,
        "network_hashrate_current_source": hashrate_24h_source,
        "network_hashrate_24h_avg_ph": float(hashrate_avg_24h_ph) if hashrate_avg_24h_ph is not None else None,
        "network_hashrate_vs_24h_pct": float(hashrate_vs_24h_pct) if hashrate_vs_24h_pct is not None else None,
        "current_difficulty": float(current_difficulty) if current_difficulty is not None else None,
        "difficulty_implied_hashrate_ph": float(difficulty_implied_hashrate_ph) if difficulty_implied_hashrate_ph is not None else None,
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
        "historical_data_date": historical_data_date.strftime("%Y-%m-%d"),
        "historical_data_age_days": int(data_age_days),
        "hashprice_methodology": (
            "Realtime hashprice uses current network difficulty converted to expected PH/s at "
            "the 10-minute target, fixed current block subsidy, a 144-block trailing fee "
            "average, and live BTC spot."
        ),
        "comparison_logic": {
            "hashprice_rt": "current difficulty-based realtime vs 24h average spot using the same difficulty and fee basis",
            "spot": "current spot vs last 24h average spot",
            "network_hashrate_ph": "difficulty-implied current hashrate vs observed 24h average hashrate",
            "hashprice_7d": "current 7d window vs previous 7d window",
            "fee_pct": "144-block fee share vs latest daily Coin Metrics row",
        },
    }
