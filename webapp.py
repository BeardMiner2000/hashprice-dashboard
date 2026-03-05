
import os
import json

BRAND=os.getenv("BRAND","beardminer")

with open(f"brands/{BRAND}.json") as f:
    BRAND_CONFIG=json.load(f)

ASCII_HEADER=BRAND_CONFIG["ascii"]
BRAND_NAME=BRAND_CONFIG["name"]

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

def build_trend_ascii(data, width):

    trend = data["trend"]
    max_val = max(float(v) for v in trend["hashprice_1d"]) or 1.0

    lines = []

    for _, row in trend.iterrows():

        date = row["time"].strftime("%Y-%m-%d")
        val = float(row["hashprice_1d"])

        bar_len = max(1, int((val/max_val)*width))
        bar = "▓"*bar_len

        lines.append(f"{date} | {bar:<{width}} ${val:,.2f}")

    marker = "▲" if data["pct_vs_7d"] >= 0 else "▼"

    lines.append("─"*(width+26))
    lines.append(
        f"{data['timestamp'][:10]} | {'▓'*min(width,24):<{width}} "
        f"${data['hashprice_rt']:,.2f} {marker} {data['pct_vs_7d']:+.2f}% vs 7D"
    )

    return "\n".join(lines)


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):

    theme_name = request.query_params.get("theme","green")
    theme = THEMES.get(theme_name, THEMES["green"])

    data = calculate()

    trend_desktop = build_trend_ascii(data,56)
    trend_mobile = build_trend_ascii(data,24)

    html = f"""
<html>

<head>

<meta http-equiv="refresh" content="60">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<style>

html,body {{{{
overflow-x:hidden;
}}}}

body {{{{
background:{{theme["bg"]}};
color:{{theme["accent"]}};
font-family:Menlo,Monaco,Consolas,monospace;
max-width:1250px;
margin:30px auto;
padding:22px;
line-height:1.45;
}}}}

.box {{{{
border:1px solid {{theme["accent"]}};
padding:26px 30px;
margin-bottom:28px;
}}}}

.topbar {{{{
border:1px solid {{theme["accent"]}};
padding:10px 16px;
margin-bottom:22px;
display:flex;
justify-content:flex-start;
}}}}

.theme-buttons {{{{
display:flex;
gap:12px;
flex-wrap:wrap;
}}}}

.theme-btn {{{{
padding:5px 12px;
border:1px solid {{theme["accent"]}};
text-decoration:none;
color:{{theme["accent"]}};
font-size:12px;
}}}}

.logo {{{{
margin-bottom:10px;
}}}}

.ascii-logo {{{{
font-size:14px;
white-space:pre;
margin:0;
}}}}

.mobile-logo {{{{
display:none;
font-size:34px;
font-weight:700;
letter-spacing:2px;
}}}}

.main-title {{{{
font-size:44px;
font-weight:700;
}}}}

.kpi-value {{{{
font-size:72px;
font-weight:700;
}}}}

.subtle {{{{
font-size:28px;
opacity:.85;
}}}}

pre.trend {{{{
margin:0;
white-space:pre;
font-size:16px;
}}}}

.trend-mobile {{{{
display:none;
}}}}

.trend-desktop {{{{
display:block;
}}}}

input {{{{
background:transparent;
border:1px solid {{theme["accent"]}};
color:{{theme["accent"]}};
padding:7px;
width:140px;
font-family:inherit;
}}}}

button {{{{
padding:8px 16px;
border:1px solid {{theme["accent"]}};
background:transparent;
color:{{theme["accent"]}};
cursor:pointer;
font-family:inherit;
}}}}

details summary {{{{
cursor:pointer;
font-weight:700;
}}}}

@media (max-width:600px) {{{{

body {{{{
padding:14px;
margin:16px auto;
}}}}

.box {{{{
padding:16px;
margin-bottom:18px;
}}}}

.main-title {{{{
font-size:26px;
}}}}

.kpi-value {{{{
font-size:44px;
}}}}

.subtle {{{{
font-size:18px;
}}}}

.ascii-logo {{{{
display:none;
}}}}

.mobile-logo {{{{
display:block;
}}}}

pre.trend {{{{
font-size:13px;
}}}}

.trend-mobile {{{{
display:block;
}}}}

.trend-desktop {{{{
display:none;
}}}}

input {{{{
width:100%;
max-width:260px;
}}}}

}}}}


/* ----- HEADER HANDLING ----- */

.header-ascii {{
  font-family: monospace;
  white-space: pre;
  line-height: 1.1;
}}

.header-mobile {{
  display:none;
  font-family:monospace;
  font-weight:bold;
  letter-spacing:4px;
  font-size:32px;
}}

@media (max-width:700px){{

  .header-ascii{{
    display:none;
  }}

  .header-mobile{{
    display:block;
  }}

  .trend-box{{
    font-size:12px;
  }}

}}



.trend-box{{
  overflow-x:hidden;
  padding-right:10px;
}}

.trend-separator{{
  margin-top:10px;
  margin-bottom:10px;
  border-top:1px solid currentColor;
}}

.trend-today{{
  padding-top:6px;
}}


</style>

</head>

<body>

<div class="topbar">
<div class="theme-buttons">
<a href="/?theme=orange" class="theme-btn">Orange</a>
<a href="/?theme=green" class="theme-btn">Green</a>
<a href="/?theme=blue" class="theme-btn">Blue</a>
<a href="/?theme=white" class="theme-btn">White</a>
</div>
</div>

<div class="box">

<div class="logo">

<pre class="ascii-logo">
██████╗ ███████╗ █████╗ ██████╗ ██████╗ ███╗   ███╗██╗███╗   ██╗███████╗██████╗
██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔══██╗████╗ ████║██║████╗  ██║██╔════╝██╔══██╗
██████╔╝█████╗  ███████║██████╔╝██║  ██║██╔████╔██║██║██╔██╗ ██║█████╗  ██████╔╝
██╔══██╗██╔══╝  ██╔══██║██╔══██╗██║  ██║██║╚██╔╝██║██║██║╚██╗██║██╔══╝  ██╔══██╗
██████╔╝███████╗██║  ██║██║  ██║██████╔╝██║ ╚═╝ ██║██║██║ ╚████║███████╗██║  ██║
╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝
</pre>

<div class="mobile-logo">
{BRAND_NAME}
</div>

</div>

<div class="main-title">BITCOIN HASHPRICE DASHBOARD</div>

Last Updated: {data["timestamp"]}

</div>

<div class="box">
<strong>BTC Spot Price</strong><br><br>
<div class="kpi-value">${data["spot"]:,.2f}</div>
</div>

<div class="box">
<strong>Realtime Hashprice (USD / PH / Day)</strong><br><br>
<div class="kpi-value">${data["hashprice_rt"]:,.2f}</div>
<div class="subtle">
{"▲" if data["pct_vs_7d"]>=0 else "▼"} {data["pct_vs_7d"]:+.2f}% vs 7D
</div>
</div>

<div class="box">
<strong>Network State</strong><br><br>

Network Hashrate: {data["network_hashrate_ph"]:,.0f} PH/s<br>
Block Reward: {data["block_reward"]:.3f} BTC<br>
Fees (BTC/day): {data["fee_btc"]:.3f}<br>
Fee % (est): {data["fee_pct"]:.2f}%
</div>

<div class="box">
1-Day Raw: ${data["hashprice_1d"]:.2f}<br>
7-Day Smoothed: ${data["hashprice_7d"]:.2f}
</div>

<div class="box">

<strong>Recent Trend</strong><br><br>

<pre class="trend trend-desktop">{trend_desktop}</pre>
<pre class="trend trend-mobile">{trend_mobile}</pre>

</div>

<div class="box">

<details>

<summary><strong>Profitability Calculator</strong></summary>

<br>

Total PH<br>
<input id="ph" value="100"><br><br>

Machine Efficiency (J/TH)<br>
<input id="eff" value="18"><br><br>

Power Price ($/kWh)<br>
<input id="power" value="0.05"><br><br>

<button onclick="calc()">Calculate</button>

<div id="result" style="margin-top:15px;"></div>

</details>

</div>

<div class="box">

<details>

<summary><strong>How This Dashboard Calculates Hashprice</strong></summary>

<br>

Two economic views are presented here.

<br><br>

<strong>Realtime Hashprice</strong>

<br><br>

This represents the estimated daily revenue produced by 1 PH/s of Bitcoin mining power.

<br><br>

Realtime Hashprice is calculated using live network conditions:

<br><br>

(Block Reward + Estimated Fees) × BTC Spot Price  
÷ Network Hashrate

<br><br>

Network Hashrate is derived from the current Bitcoin difficulty using the canonical formula:

<br><br>

hashrate = difficulty × 2³² ÷ 600

<br><br>

Inputs used:

<br>

BTC Price → Coinbase API (fallback CoinGecko)  
Network Difficulty → mempool.space API  
Fee Environment → mempool.space  
Historical issuance + fees → CoinMetrics dataset

<br><br>

<strong>7-Day Smoothed Hashprice</strong>

<br><br>

The 7-day value smooths both revenue and hashrate across a rolling window to reveal the structural economic baseline for miners.

<br><br>

Realtime Hashprice = operational signal  
7-Day Hashprice = structural baseline

<br><br>

Luxor's index uses proprietary internal feeds and smoothing methods.

This dashboard intentionally uses transparent public data sources.

</details>

</div>

<script>

function calc() {{

let ph=parseFloat(document.getElementById("ph").value)
let eff=parseFloat(document.getElementById("eff").value)
let power=parseFloat(document.getElementById("power").value)

let revenue=ph*{data["hashprice_rt"]}
let power_kw=ph*eff
let power_cost=power_kw*24*power
let profit=revenue-power_cost

document.getElementById("result").innerHTML=

"Daily Revenue: $"+revenue.toFixed(2)+"<br>"+
"Daily Power Cost: $"+power_cost.toFixed(2)+"<br>"+
"Daily Profit: $"+profit.toFixed(2)

}}

</script>

</body>
</html>
"""

    return HTMLResponse(content=html)
