import pathlib

p = pathlib.Path("webapp.py")
txt = p.read_text()

start = txt.find("<script>")
end = txt.find("</script>") + len("</script>")

safe_script = """
<script>

function calc() {{

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

}}

</script>
"""

txt = txt[:start] + safe_script + txt[end:]

p.write_text(txt)

print("Calculator script fixed.")
