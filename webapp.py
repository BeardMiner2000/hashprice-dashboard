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

BEARDMINER_ASCII = r"""
██████╗ ███████╗ █████╗ ██████╗ ██████╗ ███╗   ███╗██╗███╗   ██╗███████╗██████╗
██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔══██╗████╗ ████║██║████╗  ██║██╔════╝██╔══██╗
██████╔╝█████╗  ███████║██████╔╝██████╔╝██╔████╔██║██║██╔██╗ ██║█████╗  ██████╔╝
██╔══██╗██╔══╝  ██╔══██║██╔══██╗██╔══██╗██║╚██╔╝██║██║██║╚██╗██║██╔══╝  ██╔══██╗
██████╔╝███████╗██║  ██║██║  ██║██║  ██║██║ ╚═╝ ██║██║██║ ╚████║███████╗██║  ██║
╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝
""".strip("\n")

def build_trend_ascii(data, width: int) -> str:
    trend = data["trend"]
    max_val = max(float(v) for v in trend["hashprice_1d"]) if len(trend) else 1.0

    lines = []
    for _, row in trend.iterrows():
        date = row["time"].strftime("%Y-%m-%d")
        val = float(row["hashprice_1d"])
        bar_len = max(1, int((val / max_val) * width))
        bar = "▓" * bar_len
        lines.append(f"{date} | {bar:<{width}} ${val:,.2f}")

    marker = "▲" if data["pct_vs_7d"] >= 0 else "▼"
    lines.append("─" * (width + 26))
    lines.append(
        f"{data['timestamp'][:10]} | {'▓'*min(width,24):<{width}} "
        f"${data['hashprice_rt']:,.2f} {marker} {data['pct_vs_7d']:+.2f}% vs 7D"
    )
    return "\n".join(lines)

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    theme_name = request.query_params.get("theme", "green")
    theme = THEMES.get(theme_name, THEMES["green"])

    data = calculate()

    # Keep desktop rich, keep mobile fitting the viewport (no swipe).
    trend_desktop = build_trend_ascii(data, 56)
    trend_mobile = build_trend_ascii(data, 24)

    html = f"""
<html>
<head>
<meta http-equiv="refresh" content="60">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
html, body {{
  overflow-x: hidden;
}}
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

.topbar {{
  border: 1px solid {theme["accent"]};
  padding: 10px 16px;
  margin-bottom: 22px;
  display: flex;
  justify-content: flex-start;
}}

.theme-buttons {{
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}}

.theme-btn {{
  padding: 5px 12px;
  border: 1px solid {theme["accent"]};
  text-decoration: none;
  color: {theme["accent"]};
  font-size: 12px;
}}

.logo {{
  margin-bottom: 10px;
}}

.ascii-logo {{
  font-size: 14px;
  white-space: pre;
  margin: 0;
  line-height: 1.0;
}}

.mobile-logo {{
  display: none;
  font-size: 34px;
  font-weight: 700;
  letter-spacing: 2px;
}}

.main-title {{
  font-size: 44px;
  font-weight: 700;
}}

.kpi-value {{
  font-size: 72px;
  font-weight: 700;
}}

.subtle {{
  font-size: 28px;
  opacity: .85;
}}

pre.trend {{
  margin: 0;
  white-space: pre;
  font-size: 16px;
}}

.trend-mobile {{ display: none; }}
.trend-desktop {{ display: block; }}

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

details summary {{
  cursor: pointer;
  font-weight: 700;
}}

@media (max-width: 600px) {{
  body {{
    padding: 14px;
    margin: 16px auto;
  }}
  .box {{
    padding: 16px;
    margin-bottom: 18px;
  }}
  .main-title {{ font-size: 26px; }}
  .kpi-value {{ font-size: 44px; }}
  .subtle {{ font-size: 18px; }}

  /* Mobile: keep the BEARDMINER ASCII, but scale it down and clip cleanly */
  .ascii-logo {{
    font-size: 9px;
    transform: scale(0.92);
    transform-origin: left top;
    max-width: 100%;
  }}

  pre.trend {{ font-size: 13px; }}
  .trend-mobile {{ display: block; }}
  .trend-desktop {{ display: none; }}

  input {{
    width: 100%;
    max-width: 260px;
  }}
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
<pre class="ascii-logo">{BEARDMINER_ASCII}</pre>
  </div>

  <div class="main-title">BITCOIN HASHPRICE DASHBOARD</div>
  Last Updated: {data["timestamp"]}
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
  <pre class="trend trend-desktop">{trend_desktop}</pre>
  <pre class="trend trend-mobile">{trend_mobile}</pre>
</div>

<div class="box">
  <strong>Network State</strong><br><br>
  Network Hashrate (PH/s): {data["network_hashrate_ph"]:,.0f}<br>
  Block Reward (BTC/day): {data["block_reward"]:.3f}<br>
  Fees (BTC/day): {data["fee_btc"]:.3f}<br>
  Fee % (est): {data["fee_pct"]:.2f}%
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

    <strong>Two economic lenses:</strong><br><br>

    <strong>1) Realtime Hashprice (fast signal)</strong><br>
    This answers: “If I mined right now, what would 1 PH earn today?”<br><br>

    We compute:<br>
    <code>(Block Reward + Fees) × BTC Spot Price ÷ Network Hashrate</code><br><br>

    In this build, all components come from transparent public inputs:<br><br>

    <strong>Network + revenue (daily):</strong><br>
    • Coin Metrics public CSV (btc.csv) provides daily <code>IssTotNtv</code> (issuance), <code>FeeTotNtv</code> (fees), and <code>HashRate</code>.<br>
    • We compute daily BTC revenue = <code>IssTotNtv + FeeTotNtv</code>.<br>
    • We compute PH-denominated hashrate as <code>HashRate_PH = HashRate / 1000</code> (matching the dashboard’s historical calibration with this dataset).<br><br>

    <strong>BTC spot price (live):</strong><br>
    • Coinbase spot API (fallback) and CoinGecko simple price API (fallback).<br><br>

    That gives realtime USD / PH / day:<br>
    <code>Realtime = (BTC_revenue_per_day × Live_BTC_Price) ÷ HashRate_PH</code><br><br>

    <strong>2) 7-Day Smoothed Hashprice (structural baseline)</strong><br>
    We smooth both revenue and hashrate across a rolling 7-day window:<br>
    <code>7D = (USD_revenue rolling 7 mean) ÷ (Hashrate_PH rolling 7 mean)</code><br><br>

    <strong>Why split these?</strong><br>
    • Realtime = operational pulse (reacts quickly).<br>
    • 7-Day = structural baseline (reduces noise).<br><br>

    <strong>How this differs from Luxor</strong><br>
    Luxor’s public index can use proprietary smoothing choices and internal feeds. This dashboard is intentionally “glass box”: it’s built from public network + fee + issuance series and a live spot price.
  </details>
</div>

<script>
function calc() {{
  let ph = parseFloat(document.getElementById("ph").value || "0");
  let eff = parseFloat(document.getElementById("eff").value || "0");
  let power = parseFloat(document.getElementById("power").value || "0");

  // revenue is in $/PH/day, so multiply by PH.
  let revenue = ph * {data["hashprice_rt"]};

  // eff (J/TH) * PH => kW approx:
  // 1 PH = 1,000,000 TH. J/TH * TH/s => W. Use a conventional mining approximation:
  // Power (kW) ≈ PH * eff
  // (this matches your existing calculator behavior, keep it consistent)
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
