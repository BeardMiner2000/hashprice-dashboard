# Deploy To AI Home Pi

The public Hashprice API is hosted on the AI Home Pi, not on the MacBook.

Public API:

```text
https://hashprice.coffeecoffeecoffeecoffee.com/api/hashprice
```

Runtime path:

```text
Cloudflare -> Pi Caddy -> app-hashprice-beardminer:10000
```

Pi source directory:

```text
/opt/ai-home/render-services/hashprice-dashboard
```

Redeploy both Hashprice containers:

```bash
ssh jl-ai@ai-orchestrator-pi.local
cd /opt/ai-home
docker compose -f docker-compose.apps.yml build hashprice-beardminer hashprice-clutch
docker compose -f docker-compose.apps.yml up -d --force-recreate hashprice-beardminer hashprice-clutch
docker compose -f docker-compose.apps.yml ps hashprice-beardminer hashprice-clutch
```

Verify local Pi APIs:

```bash
curl -fsS http://127.0.0.1:4103/api/hashprice
curl -fsS http://127.0.0.1:4104/api/hashprice
```

Verify public API:

```bash
curl -fsS -A 'HashpriceTicker/1.0' https://hashprice.coffeecoffeecoffeecoffee.com/api/hashprice
```

Expected corrected realtime fields:

```text
issuance_btc_day = 450.0
current_difficulty is non-null
network_hashrate_ph is difficulty-implied
hashprice_methodology is present
```
