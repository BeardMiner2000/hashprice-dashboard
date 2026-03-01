from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from hashprice_engine import calculate

app = FastAPI()

THEMES = {
    "orange": {"accent": "#ff9900", "bg": "#0b0b0b"},
    "green": {"accent": "#00ff88", "bg": "#0b0b0b"},
    "blue": {"accent": "#4da6ff", "bg": "#0b0b0b"},
    "white": {"accent": "#111111", "bg": "#ffffff"},
}


def build_trend_ascii(data):
    trend = data["trend"]
    max_val = max(float(v) for v in trend["hashprice_1d"]) if len(trend) else 1.0
    lines = []

    for _, row in trend.iterrows():
        date_str = row["time"].strftime("%Y-%m-%d")
        val = float(row["hashprice_1d"])
        bar_len = max(1, int((val / max_val) * 56))
        bar = "▓" * bar_len
        lines.append(f"{date_str} | {bar:<56} ${val:,.2f}")

    marker = "▲" if data["vs_7d"] >= 0 else "▼"
    lines.append("─" * 96)
    lines.append(
        f"{data['timestamp'][:10]} | {'▓' * 50:<56} ${data['realtime_hashprice']:,.2f} {marker} {data['vs_7d']:+.2f}% vs 7D"
    )
    return "\n".join(lines)


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    theme_name = request.query_params.get("theme", "orange")
    theme = THEMES.get(theme_name, THEMES["orange"])
    data = calculate()

    trend_ascii = build_trend_ascii(data)

    html = f"""
    <html>
    <head>
    <meta http-equiv="refresh" content="60">
    <style>
        body {{
            background: {theme["bg"]};
            color: {theme["accent"]};
            font-family: Menlo, Monaco, Consolas, "Courier New", monospace;
            max-width: 1250px;
            margin: 34px auto;
            line-height: 1.35;
        }}
        .box {{
            border: 1px solid {theme["accent"]};
            padding: 24px 28px;
            margin-bottom: 28px;
        }}
        .brand {{
            float: right;
            opacity: 0.85;
        }}
        .theme-row {{
            display: flex;
            align-items: center;
            gap: 20px;
            flex-wrap: wrap;
        }}
        .theme-buttons {{
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }}
        .theme-btn {{
            padding: 8px 16px;
            border: 1px solid {theme["accent"]};
            text-decoration: none;
            color: {theme["accent"]};
            display: inline-block;
        }}
        .theme-btn:hover {{
            background: {theme["accent"]};
            color: black;
        }}
        .kpi-value {{
            font-size: 72px;
            font-weight: 700;
            letter-spacing: 0.5px;
        }}
        .subtle {{
            opacity: 0.9;
            font-size: 38px;
            font-weight: 600;
        }}
        input {{
            background: transparent;
            border: 1px solid {theme["accent"]};
            color: {theme["accent"]};
            padding: 7px;
            width: 135px;
            font-family: inherit;
        }}
        button {{
            padding: 8px 16px;
            border: 1px solid {theme["accent"]};
            background: transparent;
            color: {theme["accent"]};
            cursor: pointer;
            font-family: inherit;
        }}
        button:hover {{
            background: {theme["accent"]};
            color: black;
        }}
        details summary {{
            cursor: pointer;
            font-weight: 700;
            display: inline-block;
            padding: 6px 12px;
            border: 1px solid {theme["accent"]};
        }}
        pre {{
            margin: 0;
            white-space: pre-wrap;
            font-size: 34px;
            line-height: 1.5;
        }}
        .calc-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit,minmax(240px,1fr));
            gap: 14px;
            margin-top: 14px;
        }}
    </style>
    </head>
    <body>

    <div class="box">
        <strong style="font-size:42px;">BITCOIN HASHPRICE DASHBOARD</strong>
        <span class="brand">BeardMiner2000 Industries</span><br>
        Last Updated: {data["timestamp"]}
    </div>

    <div class="box">
        <div class="theme-row">
            <strong>Theme:</strong>
            <div class="theme-buttons">
                <a href="/?theme=orange" class="theme-btn">Orange</a>
                <a href="/?theme=green" class="theme-btn">Green</a>
                <a href="/?theme=blue" class="theme-btn">Blue</a>
                <a href="/?theme=white" class="theme-btn">White</a>
            </div>
        </div>

        <div style="margin-top:18px;">
            <details>
                <summary>Profitability Calculator</summary>
                <div class="calc-grid">
                    <div>
                        Total PH:<br>
                        <input id="ph" value="100">
                    </div>
                    <div>
                        Machine Efficiency (J/TH):<br>
                        <input id="eff" value="18">
                    </div>
                    <div>
                        Power Price ($/kWh):<br>
                        <input id="power" value="0.05">
                    </div>
                </div>
                <div style="margin-top:14px;">
                    <button onclick="calc()">Calculate</button>
                </div>
                <div id="result" style="margin-top:15px;"></div>
            </details>
        </div>
    </div>

    <div class="box">
        <strong>BTC Spot Price</strong><br><br>
        <span class="kpi-value">${data["btc_price"]:,.2f}</span>
    </div>

    <div class="box">
        <strong>Realtime Hashprice</strong><br><br>
        <span class="kpi-value">${data["realtime_hashprice"]:,.2f}</span><br>
        <span class="subtle">{"▲" if data["vs_7d"] >= 0 else "▼"} {data["vs_7d"]:+.2f}% vs 7D</span>
    </div>

    <div class="box">
        1-Day Raw: ${data["raw_1d"]:.2f}<br>
        7-Day Smoothed: ${data["smoothed_7d"]:.2f}
    </div>

    <div class="box">
        <strong>Recent Trend</strong><br><br>
        <pre>{trend_ascii}</pre>
    </div>

    <div class="box">
        <details open>
            <summary>How It's Calculated</summary>
            <br><br>
            <strong>How This Dashboard Calculates Hashprice</strong><br><br>
            There are two economic lenses here:<br><br>

            <strong>1) Realtime Hashprice</strong><br>
            This asks: "If I mined right now, what would 1 PH earn today?"<br><br>

            We calculate it using:<br>
            (Block Reward + Live Fee Estimate) × 144 blocks × Live BTC Price<br>
            ÷ 1-Day Network Hashrate Estimate<br><br>

            <strong>Why 1-Day hashrate?</strong><br>
            True hashrate can’t be observed instantly — it’s inferred from recent block times.
            A 1-day estimate reacts quickly but avoids noise from short bursts in block timing.<br><br>

            <strong>2) 7-Day Smoothed Hashprice</strong><br>
            This provides structural context. It smooths revenue and hashrate over a rolling window
            so you can see trend rather than volatility.<br><br>

            <strong>How This Differs From Luxor</strong><br>
            Luxor’s public hashprice index uses internal smoothing, proprietary data feeds,
            and sometimes shorter rolling hashrate windows. That can make their spot value
            slightly more reactive or slightly more damped depending on market conditions.<br><br>

            This dashboard intentionally separates:
            • A fast-reacting economic pulse (Realtime)
            • A conservative structural baseline (7-Day)<br><br>

            The goal is transparency. All components are visible and based on publicly available data:
            BTC spot, block reward, mempool fee estimates, and 1-day hashrate inference.<br><br>

            This is meant to be an independent economic truth, not a proprietary index.
        </details>
    </div>

    <script>
        function calc() {{
            let ph = parseFloat(document.getElementById("ph").value);
            let eff = parseFloat(document.getElementById("eff").value);
            let power = parseFloat(document.getElementById("power").value);

            let revenue = ph * {data["realtime_hashprice"]};
            let power_kw = ph * eff;
            let power_cost = power_kw * 24 * power;
            let profit = revenue - power_cost;

            document.getElementById("result").innerHTML =
                "Daily Revenue: $" + revenue.toFixed(2) + "<br>" +
                "Daily Power Cost: $" + power_cost.toFixed(2) + "<br>" +
                "Daily Profit: $" + profit.toFixed(2);
        }}
    </script>

    </body>
    </html>
    """

    return HTMLResponse(content=html)
