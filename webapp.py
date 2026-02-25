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

    explanation = f"""
    <div class="calc-box">

    <strong>How This Dashboard Calculates Hashprice</strong><br><br>

    There are two economic lenses here: <br><br>

    <strong>1) Realtime Hashprice</strong><br>
    This asks: “If I mined right now, what would 1 PH earn today?”<br><br>

    We calculate it using:<br>
    (Block Reward + Live Fee Estimate) × 144 blocks × Live BTC Price<br>
    ÷ 1-Day Network Hashrate Estimate<br><br>

    Why 1-Day hashrate?<br>
    Because true hashrate can’t be observed instantly — it’s inferred from recent block times.
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
    </div>
    """

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
        max-width: 900px;
        margin: 0 auto;
    }}

    .box {{
        border: 1px solid {color};
        padding: 20px 30px;
        margin-bottom: 20px;
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

    .calc-box {{
        margin-top: 20px;
        padding-top: 15px;
        border-top: 1px solid {color};
        font-size: 14px;
        line-height: 1.7;
    }}

    button {{
        background: none;
        color: {color};
        border: 1px solid {color};
        padding: 6px 12px;
        cursor: pointer;
    }}
    </style>

    <script>
    function toggleCalc() {{
        var x = document.getElementById("calc");
        if (x.style.display === "none") {{
            x.style.display = "block";
        }} else {{
            x.style.display = "none";
        }}
    }}
    </script>

    </head>
    <body>

    <div class="container">

        <div class="box">
            <div>BITCOIN HASHPRICE DASHBOARD</div>
            <div>Last Updated: {data['timestamp']}</div>
        </div>

        <div class="box">
            <div class="theme-buttons">
                Theme:
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
            <button onclick="toggleCalc()">How It’s Calculated</button>
            <div id="calc" style="display:none;">
                {explanation}
            </div>
        </div>

    </div>

    </body>
    </html>
    """)
