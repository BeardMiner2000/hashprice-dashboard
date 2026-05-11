# Hashprice Ticker App

Native macOS menu bar app prototype for the hosted hashprice API.

## What it does

- polls the hosted API every 60 seconds
- renders a scrolling menu bar ticker:
  - `₿ <bitcoin price> • $/PH <hashprice>`
- opens the dashboard from the menu

## Local development

From this folder:

```bash
swift run
```

Optional environment variables:

```bash
HASHPRICE_API_URL=https://hashprice.coffeecoffeecoffeecoffee.com/api/hashprice
HASHPRICE_DASHBOARD_URL=https://hashprice.coffeecoffeecoffeecoffee.com/
```

## Current limitation

This repo currently contains a Swift Package, not a signed `.app` bundle.
To ship a drag-to-Applications install, the next step is to open this in Xcode,
create a proper macOS app target, archive it, and then sign/notarize it.
