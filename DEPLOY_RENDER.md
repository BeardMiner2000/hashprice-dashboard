# Deploy To Render

This project is already configured for Render with [`render.yaml`](/Users/jl/hashprice_project/render.yaml).

## Prerequisites

- A GitHub repo containing this project
- A Render account connected to GitHub

## 1. Push the code to GitHub

From the project root:

```bash
git checkout -b codex/hosted-menubar
git add webapp.py hashprice.1m.py render.yaml MAC_MENU_BAR_SETUP.md hashprice-menu-bar.env.example DEPLOY_RENDER.md
git commit -m "Add hosted hashprice API and SwiftBar integration"
git push -u origin codex/hosted-menubar
```

If you prefer to deploy from `main`, merge the branch first and push `main` instead.

## 2. Create the Render service

1. In Render, click `New +`.
2. Choose `Blueprint`.
3. Select your GitHub repo.
4. Render should detect `render.yaml`.
5. Confirm the web service named `hashprice-dashboard`.

The service will:

- install dependencies with `pip install -r requirements.txt`
- run `uvicorn webapp:app --host 0.0.0.0 --port $PORT`
- use `/healthz` as the health check

## 3. Verify the deployment

After deploy finishes, open these URLs:

- `https://YOUR-RENDER-URL/healthz`
- `https://YOUR-RENDER-URL/api/hashprice`
- `https://YOUR-RENDER-URL/`

Expected health response:

```json
{"status":"ok"}
```

## 4. Update the SwiftBar config on your Mac

Copy [`hashprice-menu-bar.env.example`](/Users/jl/hashprice_project/hashprice-menu-bar.env.example) to:

```bash
~/.config/hashprice-menu-bar.env
```

Then replace the example host with your real Render URL.

The plugin reads that file automatically on each refresh.
