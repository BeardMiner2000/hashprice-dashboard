# Hashprice Menu Bar Setup

## What was added

- `GET /api/hashprice` on the FastAPI app
- `GET /healthz` for hosted service health checks
- `hashprice.1m.py` SwiftBar plugin script for a macOS menu bar item

## Recommended architecture

- Host the FastAPI app on a cloud service
- Point SwiftBar on your Mac at the hosted API URL
- Let SwiftBar refresh the menu bar item every minute

This removes the dependency on your laptop running the API locally.

## Deploy the API

The repo now includes [`render.yaml`](/Users/jl/hashprice_project/render.yaml) for Render.

1. Push this repo to GitHub.
2. Create a new Render Blueprint service from the repo.
3. Render will build from `requirements.txt` and start:

```bash
uvicorn webapp:app --host 0.0.0.0 --port $PORT
```

4. After deploy, confirm these URLs work:

- Dashboard: `https://YOUR-RENDER-URL/`
- JSON API: `https://YOUR-RENDER-URL/api/hashprice`
- Health check: `https://YOUR-RENDER-URL/healthz`

## Install the menu bar item with SwiftBar

1. Install SwiftBar on your Mac.
2. Turn on SwiftBar login/startup so it launches automatically when you log in.
3. Open SwiftBar and set its plugin folder.
4. Copy `hashprice.1m.py` into that plugin folder.
5. Make it executable:

```bash
chmod +x /path/to/SwiftBar/Plugins/hashprice.1m.py
```

6. Create a local config file on your Mac:

```bash
mkdir -p ~/.config
cp /path/to/hashprice-menu-bar.env.example ~/.config/hashprice-menu-bar.env
```

7. Edit `~/.config/hashprice-menu-bar.env` and set:

```bash
HASHPRICE_API_URL=https://YOUR-RENDER-URL/api/hashprice
HASHPRICE_DASHBOARD_URL=https://YOUR-RENDER-URL/
```

The plugin reads that file automatically.
The `.1m` in the filename tells SwiftBar to refresh every minute.
The menu bar title format is now `₿ $/PH 33.93`.

## Important constraint

The hosted API works even when your laptop is off.
The menu bar item itself only appears when your Mac is on and SwiftBar is running.
