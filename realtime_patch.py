import requests

def fetch_live_hashrate():
    try:
        url = "https://data.hashrateindex.com/api/network-data/bitcoin/hashrate"
        r = requests.get(url, timeout=5)
        data = r.json()
        # Luxor returns EH/s — convert to PH/s
        return float(data["hashrate_1d"]) * 1000
    except:
        return None

def fetch_live_fee_estimate():
    try:
        url = "https://mempool.space/api/v1/fees/mempool-blocks"
        r = requests.get(url, timeout=5)
        blocks = r.json()
        # estimate avg fee per block from first few projected blocks
        avg_fee_sat = sum(b["blockVSize"] * b["medianFee"] for b in blocks[:3]) / 3
        avg_fee_btc = avg_fee_sat / 100_000_000
        return avg_fee_btc
    except:
        return 0
