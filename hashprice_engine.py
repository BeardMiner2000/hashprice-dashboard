import pandas as pd
import requests
from datetime import datetime
import pytz

PACIFIC = pytz.timezone("US/Pacific")

def fetch_data():
    url = "https://raw.githubusercontent.com/coinmetrics/data/master/csv/btc.csv"
    df = pd.read_csv(url)
    df['time'] = pd.to_datetime(df['time'])
    df = df[['time','PriceUSD','HashRate','IssTotNtv','FeeTotNtv']].dropna()
    df = df.sort_values('time')

    df['HashRate_PH'] = df['HashRate'] / 1000
    df['btc_revenue'] = df['IssTotNtv'] + df['FeeTotNtv']
    df['usd_revenue'] = df['btc_revenue'] * df['PriceUSD']

    df['hashprice_1d'] = df['usd_revenue'] / df['HashRate_PH']
    df['hashprice_7d'] = (
        df['usd_revenue'].rolling(7).mean() /
        df['HashRate_PH'].rolling(7).mean()
    )

    return df.dropna()

def fetch_live_price():
    sources = [
        "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",
        "https://api.coinbase.com/v2/prices/spot?currency=USD"
    ]

    for url in sources:
        try:
            r = requests.get(url, timeout=5)
            if r.status_code != 200:
                continue
            data = r.json()
            if "bitcoin" in data:
                return float(data["bitcoin"]["usd"])
            if "data" in data:
                return float(data["data"]["amount"])
        except:
            continue

    raise Exception("Live price sources unavailable")

def calculate():
    df = fetch_data()
    last = df.iloc[-1]
    trend = df.tail(14)

    live_price = fetch_live_price()

    # 🔥 REALTIME = RAW HASHRATE (NOT SMOOTHED)
    realtime = (last['btc_revenue'] * live_price) / last['HashRate_PH']

    pct_vs_7d = ((realtime / last['hashprice_7d']) - 1) * 100

    timestamp = datetime.now(PACIFIC).strftime("%Y-%m-%d %H:%M:%S %Z")

    return {
        "timestamp": timestamp,
        "spot": live_price,
        "hashprice_rt": realtime,
        "hashprice_1d": last['hashprice_1d'],
        "hashprice_7d": last['hashprice_7d'],
        "pct_vs_7d": pct_vs_7d,
        "trend": trend[['time','hashprice_1d']]
    }
