# Hashprice Ticker Distribution

## Current status

- Native app name: `Hashprice Ticker`
- Real macOS app icon: included
- Launch at login: built into the app menu
- Author metadata: `jlzoeckler`

## Build a local DMG

```bash
cd /Users/jl/hashprice_project/macos/HashpriceTickerMacApp
chmod +x package_release.sh
./package_release.sh
```

This creates:

- `dist/Hashprice-Ticker.dmg`

## Important note on signing

This Mac currently has no valid Apple code-signing identity, so the DMG and app can be built locally but cannot yet be signed with a real `Developer ID Application` certificate or notarized by Apple.

To make distribution smooth for other people, the final public release should be:

1. Signed with `Developer ID Application`
2. Notarized with Apple
3. Stapled after notarization

Without that, colleagues may see Gatekeeper warnings when opening the app.
