import requests

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

            # CoinGecko format
            if "bitcoin" in data and "usd" in data["bitcoin"]:
                return float(data["bitcoin"]["usd"])

            # Coinbase format
            if "data" in data and "amount" in data["data"]:
                return float(data["data"]["amount"])

        except Exception:
            continue

    raise Exception("All live price sources failed")
