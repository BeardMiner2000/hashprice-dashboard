#!/usr/bin/env python3

from hashprice_engine import calculate


def calculate_hashprice():
    data = calculate()
    return {
        "date": data["historical_data_date"],
        "live_price": data["spot"],
        "hashrate_ph": data["network_hashrate_ph"],
        "hashprice_realtime": data["hashprice_rt"],
        "hashprice_1d": data["hashprice_1d"],
        "hashprice_7d": data["hashprice_7d"],
        "historical_data_fresh": data["historical_data_fresh"],
        "source_coinmetrics": data["source_coinmetrics"],
    }


if __name__ == "__main__":
    result = calculate_hashprice()
    for key, value in result.items():
        print(f"{key}: {value}")
