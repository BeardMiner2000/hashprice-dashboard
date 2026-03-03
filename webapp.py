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

    marker = "▲" if data["pct_vs_7d"] >= 0 else "▼"
    lines.append("─" * 96)
    lines.append(
        f"{data['timestamp'][:10]} | {'▓' * 50:<56} ${data['hashprice_rt']:,.2f} {marker} {data['pct_vs_7d']:+.2f}% vs 7D"
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
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            background: {theme["bg"]};
            color: {theme["accent"]};
            font-family: Menlo, Monaco, Consolas, monospace;
            max-width: 1250px;
            margin: 30px auto;
            padding: 22px;
            line-height: 1.45;
        }}

        .box {{
            border: 1px solid {theme["accent"]};
            padding: 26px 30px;
            margin-bottom: 28px;
        }}

        .ascii-wrap {{
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            border: 1px solid rgba(255,255,255,0.08);
            padding: 10px 12px;
            margin-bottom: 14px;
        }}

        .ascii-brand {{
            font-size: 14px;
            white-space: pre;
            margin: 0;
            opacity: 0.92;
        }}

        .main-title {{
            font-size: 44px;
            font-weight: 700;
            letter-spacing: 1px;
        }}

        .kpi-value {{
            font-size: 72px;
            font-weight: 700;
        }}

        .subtle {{
            font-size: 28px;
            opacity: 0.85;
        }}

        .theme-buttons {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}

        .theme-btn {{
            padding: 5px 12px;
            border: 1px solid {theme["accent"]};
            text-decoration: none;
            color: {theme["accent"]};
            font-size: 12px;
        }}

        .theme-btn:hover {{
            background: {theme["accent"]};
            color: black;
        }}

        pre.trend {{
            margin: 0;
            white-space: pre;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            font-size: 16px;
        }}

        input {{
            background: transparent;
            border: 1px solid {theme["accent"]};
            color: {theme["accent"]};
            padding: 7px;
            width: 140px;
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
            user-select: none;
            font-weight: 700;
        }}

        /* ---------------------------
           Mobile-only adjustments
           (desktop stays the same)
        ----------------------------*/
        @media (max-width: 600px) {{
            body {{
                padding: 14px;
                margin: 16px auto;
            }}
            .box {{
                padding: 16px 16px;
                margin-bottom: 18px;
            }}
            .main-title {{
                font-size: 28px;
                letter-spacing: 0.5px;
            }}
            .kpi-value {{
                font-size: 44px;
            }}
            .subtle {{
                font-size: 18px;
            }}
            .ascii-wrap {{
                padding: 8px 10px;
            }}
            .ascii-brand {{
                font-size: 10px;
            }}
            pre.trend {{
                font-size: 13px;
            }}
            .theme-btn {{
                padding: 5px 10px;
                font-size: 12px;
            }}
            input {{
                width: 100%;
                max-width: 260px;
            }}
        }}
    </style>
    </head>
    <body>

    <div class="box">
        <div class="ascii-wrap">
<pre class="ascii-brand">██████╗ ███████╗ █████╗ ██████╗ ██████╗ ███╗   ███╗██╗███╗   ██╗███████╗██████╗
██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔══██╗████╗ ████║██║████╗  ██║██╔════╝██╔══██╗
██████╔╝█████╗  ███████║██████╔╝██████╔╝██╔████╔██║██║██╔██╗ ██║█████╗  ██████╔╝
██╔══██╗██╔══╝  ██╔══██║██╔══██╗██╔══██╗██║╚██╔╝██║██║██║╚██╗██║██╔══╝  ██╔══██╗
██████╔╝███████╗██║  ██║██║  ██║██║  ██║██║ ╚═╝ ██║██║██║ ╚████║███████╗██║  ██║
╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝</pre>
        </div>

        <div class="main-title">BITCOIN HASHPRICE DASHBOARD</div>
        Last Updated: {data["timestamp"]}
    </div>

    <div class="box">
        <div class="theme-buttons">
            <a href="/?theme=orange" class="theme-btn">Orange</a>
            <a href="/?theme=green" class="theme-btn">Green</a>
            <a href="/?theme=blue" class="theme-btn">Blue</a>
            <a href="/?theme=white" class="theme-btn">White</a>
        </div>
    </div>

    <div class="box">
        <strong>BTC Spot Price</strong><br><br>
        <div class="kpi-value">${data["spot"]:,.2f}</div>
    </div>

    <div class="box">
        <strong>Realtime Hashprice</strong><br><br>
        <div class="kpi-value">${data["hashprice_rt"]:,.2f}</div>
        <div class="subtle">
            {"▲" if data["pct_vs_7d"] >= 0 else "▼"} {data["pct_vs_7d"]:+.2f}% vs 7D
        </div>
    </div>

    <div class="box">
        1-Day Raw: ${data["hashprice_1d"]:.2f}<br>
        7-Day Smoothed: ${data["hashprice_7d"]:.2f}
    </div>

    <div class="box">
        <strong>Recent Trend</strong><br><br>
        <pre class="trend">{trend_ascii}</pre>
    </div>

    <!-- Collapsed calculator moved between Trend and Methodology -->
    <div class="box">
        <details>
            <summary><strong>Profitability Calculator</strong></summary>
            <div style="margin-top:16px;">
                Total PH:<br>
                <input id="ph" value="100"><br><br>

                Machine Efficiency (J/TH):<br>
                <input id="eff" value="18"><br><br>

                Power Price ($/kWh):<br>
                <input id="power" value="0.05"><br><br>

                <button onclick="calc()">Calculate</button>
                <div id="result" style="margin-top:15px;"></div>
            </div>
        </details>
    </div>

    <div class="box">
        <details>
            <summary><strong>How This Dashboard Calculates Hashprice</strong></summary>
            <br><br>

            There are two economic lenses here:<br><br>

            <strong>1) Realtime Hashprice</strong><br>
            This asks: "If I mined right now, what would 1 PH earn today?"<br><br>

            Calculated using:<br>
            (Block Reward + Live Fee Estimate) × 144 blocks × Live BTC Price<br>
            ÷ 1-Day Network Hashrate Estimate<br><br>

            <strong>Why 1-Day Hashrate?</strong><br>
            True hashrate cannot be observed instantly — it is inferred from recent block times.
            A 1-day estimate reacts quickly but avoids noise from short bursts in block timing.<br><br>

            <strong>2) 7-Day Smoothed Hashprice</strong><br>
            Provides structural context. Revenue and hashrate are smoothed
            over a rolling window to show trend rather than volatility.<br><br>

            This dashboard separates:
            • A fast-reacting economic pulse (Realtime)<br>
            • A conservative structural baseline (7-Day)<br><br>

            Built using public data sources only.
        </details>
    </div>

    <script>
        function calc() {
            let ph = parseFloat(document.getElementById("ph").value);
            let eff = parseFloat(document.getElementById("eff").value);
            let power = parseFloat(document.getElementById("power").value);

            let revenue = ph * {data["hashprice_rt"]};
            let power_kw = ph * eff;
            let power_cost = power_kw * 24 * power;
            let profit = revenue - power_cost;

            document.getElementById("result").innerHTML =
                "Daily Revenue: $" + revenue.toFixed(2) + "<br>" +
                "Daily Power Cost: $" + power_cost.toFixed(2) + "<br>" +
                "Daily Profit: $" + profit.toFixed(2);
        }
    </script>

    </body>
    </html>
    """

    return HTMLResponse(content=html)
