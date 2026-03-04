import requests

def fetch_network_state():

    try:
        r = requests.get("https://mempool.space/api/v1/mining/hashrate/3d")
        j = r.json()

        # difficulty fallback handling
        difficulty = None

        if isinstance(j, dict):
            difficulty = j.get("currentDifficulty") or j.get("difficulty")

        if difficulty is None:
            difficulty = 0

    except Exception:
        difficulty = 0

    return difficulty
