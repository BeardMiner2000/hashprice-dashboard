import pandas as pd
import requests

def fetch_btc_data():
    url = "https://raw.githubusercontent.com/coinmetrics/data/master/csv/btc.csv"
    df = pd.read_csv(url)
    df['time'] = pd.to_datetime(df['time'])
    df = df[['time','PriceUSD','HashRate','IssTotNtv','FeeTotNtv']].dropna()
    return df.sort_values('time')

def fetch_live_price():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    return float(requests.get(url).json()['bitcoin']['usd'])

def calculate_hashprice():
    df = fetch_btc_data()

    df['HashRate_PH'] = df['HashRate'] / 1000
    df['btc_revenue'] = df['IssTotNtv'] + df['FeeTotNtv']
    df['usd_revenue'] = df['btc_revenue'] * df['PriceUSD']

    df['revenue_7d'] = df['usd_revenue'].rolling(7).mean()
    df['hashrate_7d'] = df['HashRate_PH'].rolling(7).mean()
    df['hashprice_7d'] = df['revenue_7d'] / df['hashrate_7d']
    df['hashprice_1d'] = df['usd_revenue'] / df['HashRate_PH']

    df = df.dropna()
    latest = df.iloc[-1]

    live_price = fetch_live_price()

    realtime = (latest['btc_revenue'] * live_price) / latest['hashrate_7d']

    return {
        "date": str(latest['time'].date()),
        "live_price": live_price,
        "hashrate_ph": latest['hashrate_7d'],
        "hashprice_realtime": realtime,
        "hashprice_1d": latest['hashprice_1d'],
        "hashprice_7d": latest['hashprice_7d']
    }
