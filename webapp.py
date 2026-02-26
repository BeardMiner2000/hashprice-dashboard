from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from hashprice_engine import calculate

app = FastAPI()

THEMES = {
    "orange": "#F7931A",
    "green": "#00FF88",
    "blue": "#4FC3F7",
    "white": "#FFFFFF"
}

@app.get("/", response_class=HTMLResponse)
def homepage(request: Request):

    theme = request.query_params.get("theme", "orange")
    if theme not in THEMES:
        theme = "orange"

    color = THEMES[theme]

    data = calculate()
    trend = data['trend']
    max_val = trend['hashprice_1d'].max()

    bars = ""
    for _, row in trend.iterrows():
        length = int((row['hashprice_1d'] / max_val) * 40)
        bar = "░" * length
        bars += f"<div class='barline'>{row['time'].date()} | {bar.ljust(40)} ${row['hashprice_1d']:.2f}</div>"

    length = int((data['hashprice_rt'] / max_val) * 40)
    bar = "░" * length
    bars += "<div class='separator'></div>"
    bars += f"<div class='barline'>{data['timestamp'][:10]} | {bar.ljust(40)} ${data['hashprice_rt']:.2f} ▲ {data['pct_vs_7d']:+.2f}% vs 7D</div>"

    return HTMLResponse(f"""
    <html>
    <head>
    <meta http-equiv="refresh" content="60">
    <style>
    body {{
        background: #111;
        color: {color};
        font-family: monospace;
        margin: 0;
        padding: 40px 0;
    }}

    .container {{
        max-width: 1000px;
        margin: 0 auto;
    }}

    .box {{
        border: 1px solid {color};
        padding: 20px 30px;
        margin-bottom: 20px;
    }}

    .header-flex {{
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}

    .brand {{
        font-size: 14px;
        opacity: 0.8;
    }}

    .big {{
        font-size: 36px;
    }}

    .separator {{
        height: 1px;
        background-color: {color};
        margin: 12px 0;
    }}

    .barline {{
        white-space: pre;
        margin-bottom: 4px;
    }}

    .theme-buttons a {{
        margin-right: 12px;
        text-decoration: none;
        color: {color};
        border: 1px solid {color};
        padding: 6px 12px;
    }}

    input {{
        background: #000;
        color: {color};
        border: 1px solid {color};
        padding: 6px;
        margin-right: 10px;
        width: 120px;
    }}

    button {{
        background: none;
        color: {color};
        border: 1px solid {color};
        padding: 6px 12px;
        cursor: pointer;
    }}

    .result {{
        margin-top: 15px;
        line-height: 1.8;
    }}

    </style>

    <script>
    function calculateProfit() {{

        const ph = parseFloat(document.getElementById("ph").value);
        const jth = parseFloat(document.getElementById("jth").value);
        const power = parseFloat(document.getElementById("power").value);

        const hashprice = {data['hashprice_rt']};

        const revenue = ph * hashprice;

        const watts = ph * 1000 * jth;  // PH → TH then × J/TH
        const kw = watts / 1000;
        const daily_kwh = kw * 24;

        const power_cost = daily_kwh * power;

        const margin = revenue - power_cost;

        document.getElementById("profit_result").innerHTML =
            "Daily Revenue: $" + revenue.toFixed(2) + "<br>" +
            "Daily Power Cost: $" + power_cost.toFixed(2) + "<br>" +
            "Daily Gross Margin: $" + margin.toFixed(2);
    }}
    </script>

    </head>
    <body>

    <div class="container">

        <div class="box header-flex">
            <div>
                <div>BITCOIN HASHPRICE DASHBOARD</div>
                <div>Last Updated: {data['timestamp']}</div>
            </div>
            <div class="brand">
                BeardMiner2000 Industries
            </div>
        </div>

        <div class="box">
            Theme:
            <div class="theme-buttons">
                <a href="/?theme=orange">Orange</a>
                <a href="/?theme=green">Green</a>
                <a href="/?theme=blue">Blue</a>
                <a href="/?theme=white">White</a>
            </div>
        </div>

        <div class="box">
            <div>BTC Spot Price</div>
            <div class="big">${data['spot']:,.2f}</div>
        </div>

        <div class="box">
            <div>Realtime Hashprice</div>
            <div class="big">${data['hashprice_rt']:.2f}</div>
            <div>▲ {data['pct_vs_7d']:+.2f}% vs 7D</div>
        </div>

        <div class="box">
            <div>1-Day Raw: ${data['hashprice_1d']:.2f}</div>
            <div>7-Day Smoothed: ${data['hashprice_7d']:.2f}</div>
        </div>

        <div class="box">
            <div>Recent Trend</div>
            {bars}
        </div>

        <div class="box">
            <strong>Profitability Calculator</strong><br><br>
            Total PH:
            <input id="ph" type="number" step="0.1" placeholder="100"><br><br>
            Machine Efficiency (J/TH):
            <input id="jth" type="number" step="0.1" placeholder="18"><br><br>
            Power Price ($/kWh):
            <input id="power" type="number" step="0.001" placeholder="0.05"><br><br>
            <button onclick="calculateProfit()">Calculate</button>
            <div id="profit_result" class="result"></div>
        </div>

    </div>

    </body>
    </html>
    """)
