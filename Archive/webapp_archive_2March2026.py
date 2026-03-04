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

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    theme_name = request.query_params.get("theme", "orange")
    theme = THEMES.get(theme_name, THEMES["orange"])
    data = calculate()

    html = f"""
    <html>
    <head>
    <meta http-equiv="refresh" content="60">
    <style>
        body {{
            background: {theme["bg"]};
            color: {theme["accent"]};
            font-family: monospace;
            max-width: 1000px;
            margin: 40px auto;
        }}
        .box {{
            border: 1px solid {theme["accent"]};
            padding: 20px;
            margin-bottom: 20px;
        }}
        .brand {{
            float: right;
        }}
        .theme-row {{
            display: flex;
            align-items: center;
            gap: 20px;
        }}
        .theme-buttons {{
            display: flex;
            gap: 12px;
        }}
        .theme-btn {{
            padding: 6px 14px;
            border: 1px solid {theme["accent"]};
            text-decoration: none;
            color: {theme["accent"]};
        }}
        .theme-btn:hover {{
            background: {theme["accent"]};
            color: black;
        }}
        input {{
            background: transparent;
            border: 1px solid {theme["accent"]};
            color: {theme["accent"]};
            padding: 6px;
            width: 120px;
        }}
        button {{
            padding: 6px 14px;
            border: 1px solid {theme["accent"]};
            background: transparent;
            color: {theme["accent"]};
            cursor: pointer;
        }}
        button:hover {{
            background: {theme["accent"]};
            color: black;
        }}
        details summary {{
            cursor: pointer;
        }}
    </style>
    </head>
    <body>

    <div class="box">
        <strong>BITCOIN HASHPRICE DASHBOARD</strong>
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
    </div>

    <div class="box">
        <strong>BTC Spot Price</strong><br><br>
        <span style="font-size:40px">${data["btc_price"]:,.2f}</span>
    </div>

    <div class="box">
        <strong>Realtime Hashprice</strong><br><br>
        <span style="font-size:40px">${data["realtime_hashprice"]:,.2f}</span><br>
        {"▲" if data["vs_7d"] >= 0 else "▼"} {data["vs_7d"]:.2f}% vs 7D
    </div>

    <div class="box">
        <strong>Profitability Calculator</strong><br><br>

        Total PH:<br>
        <input id="ph" value="100"><br><br>

        Machine Efficiency (J/TH):<br>
        <input id="eff" value="18"><br><br>

        Power Price ($/kWh):<br>
        <input id="power" value="0.05"><br><br>

        <button onclick="calc()">Calculate</button>

        <div id="result" style="margin-top:15px;"></div>
    </div>

    <div class="box">
        1-Day Raw: ${data["raw_1d"]:.2f}<br>
        7-Day Smoothed: ${data["smoothed_7d"]:.2f}
    </div>

    <div class="box">
        <strong>Recent Trend</strong><br><br>
        {data["trend_html"]}
    </div>

    <div class="box">
        <details>
            <summary><strong>How is this calculated?</strong></summary>
            <br>
            Hashprice ($/PH/day) =
            (BTC Price × Daily BTC Issued) ÷ Network Hashrate (PH)
            <br><br>
            This dashboard intentionally uses short-term
            hashrate and fee estimates to reflect current
            market conditions rather than long smoothing windows.
        </details>
    </div>

    <script>
        function calc() {{
            let ph = parseFloat(document.getElementById("ph").value);
            let eff = parseFloat(document.getElementById("eff").value);
            let power = parseFloat(document.getElementById("power").value);

            let revenue = ph * {data["realtime_hashprice"]};
            let power_kw = ph * 1000 * eff / 1000;
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
