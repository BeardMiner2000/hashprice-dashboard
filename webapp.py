import os
import json
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from hashprice_engine import calculate

BRAND = os.getenv("BRAND", "beardminer")

with open(f"brands/{BRAND}.json") as f:
    BRAND_CONFIG = json.load(f)

ASCII_HEADER = BRAND_CONFIG["ascii"]
BRAND_NAME = BRAND_CONFIG["name"]

app = FastAPI()

THEMES = {
    "orange": {"accent": "#ff9900", "bg": "#0b0b0b", "soft": "rgba(255,153,0,0.12)"},
    "green": {"accent": "#00ff88", "bg": "#0b0b0b", "soft": "rgba(0,255,136,0.12)"},
    "blue": {"accent": "#4da6ff", "bg": "#0b0b0b", "soft": "rgba(77,166,255,0.12)"},
    "white": {"accent": "#111111", "bg": "#ffffff", "soft": "rgba(17,17,17,0.06)"},
}


def build_trend_rows(data):
    trend = data["trend"]
    vals = [float(v) for v in trend["hashprice_1d"]]
    vals.append(float(data["hashprice_rt"]))
    max_val = max(vals) or 1.0

    rows = []
    for _, row in trend.iterrows():
        date = row["time"].strftime("%Y-%m-%d")
        val = float(row["hashprice_1d"])
        width_pct = max(2.0, (val / max_val) * 100.0)
        rows.append({"date": date, "value": val, "width_pct": width_pct, "is_live": False})

    rows.append({
        "date": data["timestamp"][:10],
        "value": float(data["hashprice_rt"]),
        "width_pct": max(2.0, (float(data["hashprice_rt"]) / max_val) * 100.0),
        "is_live": True,
    })
    return rows


def build_api_payload(data):
    return {
        "timestamp": data["timestamp"],
        "spot": float(data["spot"]),
        "spot_source": data["spot_source"],
        "spot_avg_24h": float(data["spot_avg_24h"]) if data["spot_avg_24h"] is not None else None,
        "spot_avg_24h_source": data["spot_avg_24h_source"],
        "spot_vs_24h_pct": float(data["spot_vs_24h_pct"]) if data["spot_vs_24h_pct"] is not None else None,
        "hashprice_rt": float(data["hashprice_rt"]),
        "hashprice_rt_avg_24h": float(data["hashprice_rt_avg_24h"]) if data["hashprice_rt_avg_24h"] is not None else None,
        "hashprice_rt_vs_24h_pct": float(data["hashprice_rt_vs_24h_pct"]) if data["hashprice_rt_vs_24h_pct"] is not None else None,
        "hashprice_1d": float(data["hashprice_1d"]),
        "hashprice_7d": float(data["hashprice_7d"]),
        "hashprice_7d_prev": float(data["hashprice_7d_prev"]) if data["hashprice_7d_prev"] is not None else None,
        "hashprice_7d_change_pct": float(data["hashprice_7d_change_pct"]) if data["hashprice_7d_change_pct"] is not None else None,
        "pct_vs_7d": float(data["pct_vs_7d"]),
        "network_hashrate_ph": float(data["network_hashrate_ph"]),
        "network_hashrate_source": data["network_hashrate_source"],
        "network_hashrate_current_ph": float(data["network_hashrate_current_ph"]) if data["network_hashrate_current_ph"] is not None else None,
        "network_hashrate_current_source": data["network_hashrate_current_source"],
        "network_hashrate_24h_avg_ph": float(data["network_hashrate_24h_avg_ph"]) if data["network_hashrate_24h_avg_ph"] is not None else None,
        "network_hashrate_vs_24h_pct": float(data["network_hashrate_vs_24h_pct"]) if data["network_hashrate_vs_24h_pct"] is not None else None,
        "current_difficulty": float(data["current_difficulty"]) if data["current_difficulty"] is not None else None,
        "difficulty_implied_hashrate_ph": float(data["difficulty_implied_hashrate_ph"]) if data["difficulty_implied_hashrate_ph"] is not None else None,
        "bitcoin_per_block": float(data["bitcoin_per_block"]),
        "issuance_btc_day": float(data["issuance_btc_day"]),
        "fee_btc_day": float(data["fee_btc_day"]),
        "fee_source": data["fee_source"],
        "btc_revenue_day": float(data["btc_revenue_day"]),
        "fee_pct": float(data["fee_pct"]),
        "fee_pct_daily": float(data["fee_pct_daily"]) if data["fee_pct_daily"] is not None else None,
        "fee_pct_vs_daily_pct": float(data["fee_pct_vs_daily_pct"]) if data["fee_pct_vs_daily_pct"] is not None else None,
        "source_coinmetrics": data["source_coinmetrics"],
        "historical_data_date": data["historical_data_date"],
        "historical_data_age_days": int(data["historical_data_age_days"]),
        "hashprice_methodology": data["hashprice_methodology"],
        "comparison_logic": data["comparison_logic"],
        "trend": [
            {
                "time": row["time"].strftime("%Y-%m-%d"),
                "hashprice_1d": float(row["hashprice_1d"]),
            }
            for _, row in data["trend"].iterrows()
        ],
    }


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    theme_name = request.query_params.get("theme", "green")
    theme = THEMES.get(theme_name, THEMES["green"])
    data = calculate()
    trend_rows = build_trend_rows(data)
    marker = "▲" if data["pct_vs_7d"] >= 0 else "▼"

    calculator_hashprice = data["hashprice_rt"]
    observed_hashrate_html = ""
    if data["network_hashrate_current_ph"] is not None:
        observed_hashrate_html = f"<div>Observed hashrate: {data['network_hashrate_current_ph']:,.0f} PH/s ({data['network_hashrate_current_source']})</div>"

    trend_html = ""
    for row in trend_rows:
        extra = f" {marker} {data['pct_vs_7d']:+.2f}% vs 7D" if row["is_live"] else ""
        row_class = "trend-row live" if row["is_live"] else "trend-row"
        trend_html += f"""
        <div class=\"{row_class}\">
            <div class=\"trend-date\">{row['date']}</div>
            <div class=\"trend-bar-wrap\"><div class=\"trend-bar\" style=\"width:{row['width_pct']:.2f}%\"></div></div>
            <div class=\"trend-value\">${row['value']:,.2f}{extra}</div>
        </div>
        """

    explanation_html = f"""
    <div class=\"formula\">
        <div><strong>Realtime hashprice</strong> = ((expected subsidy issuance + trailing fee average) × live BTC spot) ÷ difficulty-implied network hashrate (PH/s)</div>
        <br>
        <div>For this dashboard right now, that means:</div>
        <br>
        <div>({data['issuance_btc_day']:.3f} BTC/day expected subsidy + {data['fee_btc_day']:.3f} BTC/day fees) × ${data['spot']:,.2f} ÷ {data['network_hashrate_ph']:,.0f} PH/s = <strong>${data['hashprice_rt']:,.2f} / PH / day</strong></div>
        <br>
        <div><strong>Network</strong> uses current difficulty converted to expected PH/s at the 10-minute target.</div>
        <div><strong>1-Day Raw</strong> and <strong>7-Day Smoothed</strong> use Coin Metrics daily history. Latest historical row: {data['historical_data_date']} ({data['historical_data_age_days']} days old).</div>
        <br>
        <div>Sources used by the app:</div>
        <div>Spot price: {data['spot_source']}</div>
        <div>Difficulty-implied network hashrate: {data['network_hashrate_source']}</div>
        {observed_hashrate_html}
        <div>Fees/day: {data['fee_source']}</div>
        <div>Historical daily economics: Coin Metrics public BTC CSV</div>
    </div>
    """

    html = f"""
<html>
<head>
<meta http-equiv=\"refresh\" content=\"60\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
<style>
:root {{
  --accent: {theme['accent']};
  --bg: {theme['bg']};
  --soft: {theme['soft']};
}}
* {{ box-sizing: border-box; }}
body {{
  background: var(--bg);
  color: var(--accent);
  font-family: Menlo, Monaco, Consolas, monospace;
  max-width: 1200px;
  margin: 30px auto;
  padding: 20px;
  line-height: 1.4;
}}
.box {{
  border: 1px solid var(--accent);
  padding: 22px;
  margin-bottom: 22px;
  overflow: hidden;
}}
.theme-btn {{
  display: inline-block;
  margin-right: 10px;
  margin-bottom: 10px;
  text-decoration: none;
  color: var(--accent);
  border: 1px solid var(--accent);
  padding: 4px 10px;
  font-size: 12px;
}}
.ascii-logo {{ white-space: pre; font-size: 14px; overflow-x: auto; }}
.mobile-logo {{ display:none; font-size:34px; font-weight:bold; letter-spacing:2px; }}
.main-title {{ font-size:38px; font-weight:bold; }}
.kpi {{ font-size:64px; font-weight:bold; line-height: 1.05; overflow-wrap: anywhere; }}
.subtle {{ font-size:22px; opacity:.85; overflow-wrap: anywhere; }}
.network-grid {{ display:grid; grid-template-columns: repeat(2, minmax(220px, 1fr)); gap: 10px 24px; }}
.calc-grid {{ display:grid; grid-template-columns: repeat(3, minmax(180px, 1fr)); gap:18px; }}
.field label {{ display:block; margin-bottom:8px; }}
input {{
  width: 100%;
  background: var(--soft);
  color: var(--accent);
  border: 1px solid var(--accent);
  padding: 12px 14px;
  border-radius: 6px;
  font-family: inherit;
  font-size: 18px;
  outline: none;
  appearance: none;
}}
input::placeholder {{ color: var(--accent); opacity: .55; }}
button {{
  background: var(--soft);
  color: var(--accent);
  border: 1px solid var(--accent);
  padding: 12px 16px;
  border-radius: 6px;
  font-family: inherit;
  font-size: 16px;
  cursor: pointer;
}}
.result {{ margin-top: 18px; overflow-wrap: anywhere; }}
summary {{ cursor: pointer; }}
.formula {{ overflow-wrap: anywhere; }}
.trend-chart {{ width: 100%; }}
.trend-row {{
  display: grid;
  grid-template-columns: 160px minmax(120px, 1fr) 270px;
  gap: 14px;
  align-items: center;
  padding: 6px 0;
}}
.trend-row.live {{
  margin-top: 14px;
  padding-top: 18px;
  border-top: 1px solid var(--accent);
}}
.trend-date, .trend-value {{ white-space: nowrap; }}
.trend-value {{ text-align: right; overflow-wrap: anywhere; }}
.trend-bar-wrap {{ width: 100%; min-width: 0; }}
.trend-bar {{
  height: 24px;
  border: 1px solid var(--accent);
  background:
    radial-gradient(circle, transparent 28%, var(--accent) 30%, var(--accent) 45%, transparent 47%) 0 0/8px 8px,
    var(--soft);
}}
@media (max-width: 860px) {{
  .kpi {{ font-size: 48px; }}
  .trend-row {{ grid-template-columns: 120px minmax(90px, 1fr) 180px; gap: 10px; }}
  .trend-bar {{ height: 20px; }}
}}
@media (max-width: 700px) {{
  body {{ padding: 14px; margin: 18px auto; }}
  .ascii-logo {{ display:none; }}
  .mobile-logo {{ display:block; }}
  .main-title {{ font-size:26px; }}
  .kpi {{ font-size: 40px; }}
  .subtle {{ font-size: 18px; }}
  .network-grid, .calc-grid {{ grid-template-columns: 1fr; }}
  .trend-row {{
    grid-template-columns: 1fr;
    gap: 6px;
    padding: 10px 0;
  }}
  .trend-date, .trend-value {{ white-space: normal; }}
  .trend-value {{ text-align: left; }}
}}
</style>
</head>
<body>
<div>
<a href=\"/?theme=orange\" class=\"theme-btn\">Orange</a>
<a href=\"/?theme=green\" class=\"theme-btn\">Green</a>
<a href=\"/?theme=blue\" class=\"theme-btn\">Blue</a>
<a href=\"/?theme=white\" class=\"theme-btn\">White</a>
</div>
<div class=\"box\">
<pre class=\"ascii-logo\">{ASCII_HEADER}</pre>
<div class=\"mobile-logo\">{BRAND_NAME}</div>
<div class=\"main-title\">BITCOIN HASHPRICE DASHBOARD</div>
Last Updated: {data['timestamp']}
</div>
<div class=\"box\"><strong>BTC Spot Price</strong><br><br><div class=\"kpi\">${data['spot']:,.2f}</div></div>
<div class=\"box\">
<strong>Realtime Hashprice (USD / PH / Day)</strong><br><br>
<div class=\"kpi\">${data['hashprice_rt']:,.2f}</div>
<div class=\"subtle\">{marker} {data['pct_vs_7d']:+.2f}% vs 7D</div>
</div>
<div class=\"box\">
<strong>Network State</strong><br><br>
<div class=\"network-grid\">
  <div>Difficulty-Implied Network: {data['network_hashrate_ph']:,.0f} PH/s</div>
  <div>Bitcoin per Block: {data['bitcoin_per_block']:.3f} BTC</div>
  <div>Issuance (BTC/day): {data['issuance_btc_day']:.3f}</div>
  <div>Fees (BTC/day): {data['fee_btc_day']:.3f}</div>
  <div>Total BTC Revenue/Day: {data['btc_revenue_day']:.3f}</div>
  <div>Fee % (est): {data['fee_pct']:.2f}%</div>
</div>
</div>
<div class=\"box\">1-Day Raw: ${data['hashprice_1d']:.2f}<br>7-Day Smoothed: ${data['hashprice_7d']:.2f}</div>
<div class=\"box\">
<strong>Recent Trend</strong><br><br>
<div class=\"trend-chart\">{trend_html}</div>
</div>
<div class=\"box\">
<details>
<summary><strong>Profitability Calculator</strong></summary>
<br>
<div class=\"calc-grid\">
  <div class=\"field\"><label>Total PH</label><input id=\"ph\" value=\"100\"></div>
  <div class=\"field\"><label>Machine Efficiency (J/TH)</label><input id=\"eff\" value=\"18\"></div>
  <div class=\"field\"><label>Power Price ($/kWh)</label><input id=\"power\" value=\"0.05\"></div>
</div>
<br>
<button onclick=\"calc()\">Calculate</button>
<div id=\"result\" class=\"result\"></div>
</details>
</div>
<div class=\"box\">
<details>
<summary><strong>How This Dashboard Calculates Hashprice</strong></summary>
<br>
{explanation_html}
</details>
</div>
<script>
const HASHPRICE_RT = {calculator_hashprice};
function calc() {{
  const ph = parseFloat(document.getElementById("ph").value) || 0;
  const eff = parseFloat(document.getElementById("eff").value) || 0;
  const power = parseFloat(document.getElementById("power").value) || 0;

  const revenue = ph * HASHPRICE_RT;
  const powerKw = ph * eff;
  const powerCost = powerKw * 24 * power;
  const profit = revenue - powerCost;

  document.getElementById("result").innerHTML =
    "Daily Revenue: $" + revenue.toFixed(2) + "<br>" +
    "Daily Power Cost: $" + powerCost.toFixed(2) + "<br>" +
    "Daily Profit: $" + profit.toFixed(2);
}}
</script>
</body>
</html>
"""
    return HTMLResponse(content=html)


@app.get("/api/hashprice", response_class=JSONResponse)
def hashprice_api():
    return JSONResponse(content=build_api_payload(calculate()))


@app.get("/healthz", response_class=JSONResponse)
def healthcheck():
    return JSONResponse(content={"status": "ok"})
