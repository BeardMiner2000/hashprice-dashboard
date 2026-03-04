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

body {{
background:{theme["bg"]};
color:{theme["accent"]};
font-family:Menlo,Monaco,Consolas,monospace;
max-width:1200px;
margin:30px auto;
padding:20px;
}}

.box {{
border:1px solid {theme["accent"]};
padding:25px;
margin-bottom:25px;
}}

.topbar {{
border:1px solid {theme["accent"]};
padding:10px;
margin-bottom:20px;
text-align:center;
}}

.theme-btn {{
padding:5px 12px;
border:1px solid {theme["accent"]};
text-decoration:none;
color:{theme["accent"]};
margin:5px;
display:inline-block;
}}

.ascii-logo {{
font-size:14px;
white-space:pre;
margin:0;
}}

.mobile-logo {{
display:none;
font-size:34px;
font-weight:bold;
}}

.kpi-value {{
font-size:70px;
font-weight:bold;
}}

.subtle {{
font-size:28px;
}}

pre.trend {{
font-size:16px;
}}

@media (max-width:600px) {{

.ascii-logo {{
display:none;
}}

.mobile-logo {{
display:block;
}}

.kpi-value {{
font-size:44px;
}}

.subtle {{
font-size:18px;
}}

pre.trend {{
font-size:13px;
}}

}}

</style>
</head>

<body>

<div class="topbar">
<a href="/?theme=orange" class="theme-btn">Orange</a>
<a href="/?theme=green" class="theme-btn">Green</a>
<a href="/?theme=blue" class="theme-btn">Blue</a>
<a href="/?theme=white" class="theme-btn">White</a>
</div>

<div class="box">

<pre class="ascii-logo">
██████╗ ███████╗ █████╗ ██████╗ ██████╗ ███╗   ███╗██╗███╗   ██╗███████╗██████╗
██╔══██╗██╔════╝██╔══██╗██╔══██╗██║  ██║████╗ ████║██║████╗  ██║██╔════╝██╔══██╗
██████╔╝█████╗  ███████║██████╔╝██║  ██║██╔████╔██║██║██╔██╗ ██║█████╗  ██████╔╝
██╔══██╗██╔══╝  ██╔══██║██╔══██╗██║  ██║██║╚██╔╝██║██║██║╚██╗██║██╔══╝  ██╔══██╗
██████╔╝███████╗██║  ██║██║  ██║██████╔╝██║ ╚═╝ ██║██║██║ ╚████║███████╗██║  ██║
╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝
</pre>

<div class="mobile-logo">BEARDMINER</div>

<h1>BITCOIN HASHPRICE DASHBOARD</h1>

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
{"▲" if data["pct_vs_7d"]>=0 else "▼"} {data["pct_vs_7d"]:+.2f}% vs 7D
</div>
</div>

<div class="box">
1-Day Raw: ${data["hashprice_1d"]:.2f}<br>
7-Day Smoothed: ${data["hashprice_7d"]:.2f}
</div>

<div class="box">
<strong>Recent Trend</strong><br><br>
<pre class="trend">{trend_desktop}</pre>
</div>

</body>
</html>
"""

    return HTMLResponse(content=html)
