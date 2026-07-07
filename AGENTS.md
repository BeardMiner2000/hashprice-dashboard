# Hashprice Deployment Notes For Agents

This project is currently deployed on the AI Home Raspberry Pi, not Render.

Do not use Render, `render.yaml`, or Render CLI commands for this app unless the user explicitly says the deployment target has changed.

## Current Production Path

```text
Cloudflare -> Pi Caddy -> app-hashprice-beardminer:10000
```

Public endpoints:

```text
https://hashprice.coffeecoffeecoffeecoffee.com/
https://hashprice.coffeecoffeecoffeecoffee.com/api/hashprice
https://hashprice.coffeecoffeecoffeecoffee.com/healthz
```

Pi source directory:

```text
/opt/ai-home/render-services/hashprice-dashboard
```

The directory name contains `render-services` for historical reasons. It does not mean the app is deployed on Render.

## Deploy Changes

After changing backend or dashboard files locally, sync the changed files to the Pi source directory and rebuild both containers:

```bash
rsync -av hashprice_engine.py webapp.py hashprice_dashboard.py jl-ai@ai-orchestrator-pi.local:/opt/ai-home/render-services/hashprice-dashboard/
ssh jl-ai@ai-orchestrator-pi.local
cd /opt/ai-home
docker compose -f docker-compose.apps.yml build hashprice-beardminer hashprice-clutch
docker compose -f docker-compose.apps.yml up -d --force-recreate hashprice-beardminer hashprice-clutch
docker compose -f docker-compose.apps.yml ps hashprice-beardminer hashprice-clutch
```

## Verify

Verify Pi-local APIs:

```bash
curl -fsS http://127.0.0.1:4103/api/hashprice
curl -fsS http://127.0.0.1:4104/api/hashprice
```

Verify public API:

```bash
curl -fsS -A 'HashpriceTicker/1.0' https://hashprice.coffeecoffeecoffeecoffee.com/api/hashprice
curl -fsS -A 'HashpriceTicker/1.0' https://hashprice.coffeecoffeecoffeecoffee.com/healthz
```

Expected historical-data sanity checks:

```text
historical_data_fresh = true
historical_data_age_days <= 3
source_coinmetrics = https://community-api.coinmetrics.io/v4/timeseries/asset-metrics
```
