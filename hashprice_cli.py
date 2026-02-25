from hashprice_engine import calculate

def print_dashboard():
    data = calculate()
    trend = data['trend']
    max_val = trend['hashprice_1d'].max()

    print()
    print("BITCOIN HASHPRICE DASHBOARD")
    print("Last Updated:", data['timestamp'])
    print("-" * 60)
    print(f"BTC Spot Price     : ${data['spot']:,.2f}")
    print(f"Realtime Hashprice : ${data['hashprice_rt']:.2f}   ▲ {data['pct_vs_7d']:+.2f}% vs 7D")
    print()
    print(f"1-Day Raw          : ${data['hashprice_1d']:.2f}")
    print(f"7-Day Smoothed     : ${data['hashprice_7d']:.2f}")
    print("-" * 60)
    print("Recent Trend (1-Day Raw + Realtime Today):")
    for _, row in trend.iterrows():
        length = int((row['hashprice_1d'] / max_val) * 40)
        bar = "░" * length
        print(f"{row['time'].date()} | {bar} ${row['hashprice_1d']:.2f}")

    length = int((data['hashprice_rt'] / max_val) * 40)
    bar = "░" * length
    print("-" * 60)
    print(f"{data['timestamp'][:10]} | {bar} ${data['hashprice_rt']:.2f}")

if __name__ == "__main__":
    print_dashboard()
