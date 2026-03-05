import pathlib

p = pathlib.Path("webapp.py")
txt = p.read_text()

insert = """

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

function calc(){

let ph=parseFloat(document.getElementById("ph").value)
let eff=parseFloat(document.getElementById("eff").value)
let power=parseFloat(document.getElementById("power").value)

let revenue=ph*HASHPRICE_RT
let power_kw=ph*eff
let power_cost=power_kw*24*power
let profit=revenue-power_cost

document.getElementById("result").innerHTML=
"Daily Revenue: $"+revenue.toFixed(2)+"<br>"+
"Daily Power Cost: $"+power_cost.toFixed(2)+"<br>"+
"Daily Profit: $"+profit.toFixed(2)

}

</script>

"""

txt = txt.replace("</body>", insert + "\n</body>")
txt = txt.replace("html = f\"\"\"", "HASHPRICE_RT=data['hashprice_rt']\n\nhtml = f\"\"\"")

p.write_text(txt)

print("Sections restored.")
