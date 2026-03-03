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


def build_trend_ascii(data, bar_width: int, include_values: bool = True, include_today_line: bool = True) -> str:
    trend = data["trend"]
    if len(trend) == 0:
        return "No trend data available."

    max_val = max(float(v) for v in trend["hashprice_1d"]) or 1.0

    lines = []
    for _, row in trend.iterrows():
        date_str = row["time"].strftime("%Y-%m-%d")
        val = float(row["hashprice_1d"])
        bar_len = max(1, int((val / max_val) * bar_width))
        bar = "▓" * bar_len

        if include_values:
            lines.append(f"{date_str} | {bar:<{bar_width}} ${val:,.2f}")
        else:
            lines.append(f"{date_str} | {bar:<{bar_width}}")

    if include_today_line:
        marker = "▲" if data["pct_vs_7d"] >= 0 else "▼"
        lines.append("─" * (bar_width + (16 if include_values else 8) + 16))
        # Keep this one compact so it doesn't explode on small screens
        lines.append(
            f"{data['timestamp'][:10]} | {'▓' * min(bar_width, 24):<{bar_width}} "
            f"${data['hashprice_rt']:,.2f} {marker} {data['pct_vs_7d']:+.2f}% vs 7D"
        )

    return "\n".join(lines)


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    theme_name = request.query_params.get("theme", "orange")
    theme = THEMES.get(theme_name, THEMES["orange"])
    data = calculate()

    # Desktop vs mobile trend strings. Mobile uses shorter bars so it fits the viewport.
    trend_ascii_desktop = build_trend_ascii(data, bar_width=56, include_values=True, include_today_line=True)
    trend_ascii_mobile = build_trend_ascii(data, bar_width=26, include_values=True, include_today_line=True)

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

        /* ---------------- Header / Brand ---------------- */
        .ascii-clip {{
          width: 100%;
          overflow: hidden; /* prevents Safari from zooming out due to overflow */
        }}

        .ascii-brand {{
          font-size: 14px;
          white-space: pre;
          margin: 0;
          display: inline-block;
          transform-origin: top left;
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

        /* ---------------- Controls ---------------- */
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

        /* ---------------- Trend ---------------- */
        pre.trend {{
          margin: 0;
          white-space: pre;
          font-size: 16px;
        }}

        /* We intentionally DO NOT allow horizontal scrolling on mobile.
           Instead we render a shorter-bar mobile version. */
        .trend-mobile {{ display: none; }}
        .trend-desktop {{ display: block; }}

        /* ---------------- Inputs ---------------- */
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

        /* ---------------- Mobile-only adjustments ---------------- */
        @media (max-width: 600px) {{
          body {{
            padding: 14px;
            margin: 16px auto;
          }}

          .box {{
            padding: 16px;
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

          /* Scale ASCII down until it comfortably fits mobile width.
             The clip container prevents overflow-based zoom. */
          .ascii-brand {{
            transform: scale(0.58);
          }}

          pre.trend {{
            font-size: 13px;
          }}

          input {{
            width: 100%;
            max-width: 260px;
          }}

          .trend-mobile {{ display: block; }}
          .trend-desktop {{ display: none; }}
        }}
      </style>
    </head>

    <body>

      <div class="box">
        <div class="ascii-clip">
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

        <pre class="trend trend-desktop">{trend_ascii_desktop}</pre>
        <pre class="trend trend-mobile">{trend_ascii_mobile}</pre>
      </div>

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

          <strong>Realtime Hashprice</strong><br>
          This estimates what 1 PH earns today using live BTC price, a live fee environment estimate,
          and a 1-day inferred network hashrate.<br><br>

          <strong>Core logic (conceptual)</strong><br>
          (Block Reward + Estimated Fees) × ~144 blocks/day × BTC Price<br>
          ÷ (Estimated Network Hashrate per day)<br><br>

          <strong>Why 1-Day Network Hashrate?</strong><br>
          Network hashrate isn’t measured directly. It’s inferred from block timing and difficulty.
          A 1-day estimate reacts quickly enough for operations but avoids the worst noise from short bursts
          of fast/slow blocks.<br><br>

          <strong>7-Day Smoothed Hashprice</strong><br>
          The 7-day metric is a structural baseline. It smooths over volatility to show trend direction
          rather than intraday chop.<br><br>

          This dashboard intentionally separates:
          • A fast economic pulse (Realtime)<br>
          • A structural baseline (7-Day)<br><br>

          Use Realtime for decisions. Use 7-Day for sanity and strategy.
        </details>
      </div>

      <script>
        function calc() {{
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
        }}
      </script>

    </body>
    </html>
    """

    return HTMLResponse(content=html)
