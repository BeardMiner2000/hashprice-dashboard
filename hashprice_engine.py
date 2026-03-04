import requests
import pandas as pd
from datetime import datetime

def calculate():

    btc_price = requests.get(
        "https://api.coinbase.com/v2/prices/spot?currency=USD"
    ).json()["data"]["amount"]

    btc_price = float(btc_price)

    mempool = requests.get(
        "https://mempool.space/api/v1/fees/recommended"
    ).json()

    fee_est = mempool["hourFee"]

    difficulty_data = requests.get(
        "https://blockchain.info/q/getdifficulty"
    ).text

    difficulty = float(difficulty_data)

    block_reward = 3.125

    network_hashrate = difficulty * 2**32 / 600 / 1e18

    fee_pct = (fee_est / 100) * 0.5

    hashprice_rt = (block_reward * btc_price * 144) / (network_hashrate * 1e6)

    hashprice_1d = hashprice_rt * 0.94
    hashprice_7d = hashprice_rt * 0.92

    trend = pd.DataFrame({
        "time":[datetime.utcnow()],
        "hashprice_1d":[hashprice_1d]
    })

    return {
        "spot":btc_price,
        "timestamp":datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S PST"),
        "hashprice_rt":hashprice_rt,
        "hashprice_1d":hashprice_1d,
        "hashprice_7d":hashprice_7d,
        "pct_vs_7d":((hashprice_rt-hashprice_7d)/hashprice_7d)*100,
        "trend":trend,
        "network_hashrate":network_hashrate,
        "difficulty":difficulty,
        "block_reward":block_reward,
        "fee_pct":fee_pct
    }
