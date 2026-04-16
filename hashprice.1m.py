#!/usr/bin/env python3

import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request


CONFIG_PATH = Path(os.getenv("HASHPRICE_CONFIG_PATH", "~/.config/hashprice-menu-bar.env")).expanduser()
DEFAULT_API_URL = "http://127.0.0.1:8000/api/hashprice"
DEFAULT_DASHBOARD_URL = "http://127.0.0.1:8000/"
DEFAULT_TIMEOUT = "8"


def load_env_file():
    if not CONFIG_PATH.exists():
        return

    for raw_line in CONFIG_PATH.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


load_env_file()

API_URL = os.getenv("HASHPRICE_API_URL", DEFAULT_API_URL)
DASHBOARD_URL = os.getenv("HASHPRICE_DASHBOARD_URL", DEFAULT_DASHBOARD_URL)
REQUEST_TIMEOUT = float(os.getenv("HASHPRICE_TIMEOUT", DEFAULT_TIMEOUT))


def fetch_payload():
    with urllib.request.urlopen(API_URL, timeout=REQUEST_TIMEOUT) as response:
        return json.load(response)


def print_error(message):
    print("₿ $/PH --")
    print("---")
    print(f"{message}")
    print(f"Open Dashboard | href={DASHBOARD_URL}")
    print("Refresh | refresh=true")


def main():
    try:
        data = fetch_payload()
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
        print_error("Hashprice API unavailable")
        return 1

    marker = "▲" if data["pct_vs_7d"] >= 0 else "▼"
    title = f"₿ $/PH {data['hashprice_rt']:.2f}"

    print(title)
    print("---")
    print(f"Realtime: ${data['hashprice_rt']:.2f} / PH / day")
    print(f"Vs 7D: {marker} {data['pct_vs_7d']:+.2f}%")
    print(f"BTC Spot: ${data['spot']:,.2f}")
    print(f"Hashrate: {data['network_hashrate_ph']:,.0f} PH/s")
    print(f"Fees/day: {data['fee_btc_day']:.3f} BTC")
    print(f"Updated: {data['timestamp']}")
    print("---")
    print(f"Open Dashboard | href={DASHBOARD_URL}")
    print(f"Open API JSON | href={API_URL}")
    print("Refresh | refresh=true")
    return 0


if __name__ == "__main__":
    sys.exit(main())
