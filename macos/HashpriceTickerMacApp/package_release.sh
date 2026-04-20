#!/bin/zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT="$ROOT_DIR/HashpriceTickerMacApp.xcodeproj"
SCHEME="HashpriceTicker"
DERIVED_DATA="$ROOT_DIR/.derived-data"
BUILD_DIR="$DERIVED_DATA/Build/Products/Debug"
APP_NAME="Hashprice Ticker.app"
APP_PATH="$BUILD_DIR/$APP_NAME"
DIST_DIR="$ROOT_DIR/dist"
DMG_DIR="$DIST_DIR/dmg-root"
BACKGROUND_DIR="$DMG_DIR/.background"
BACKGROUND_SRC="$ROOT_DIR/design/dmg-background.png"
RW_DMG_PATH="$DIST_DIR/Hashprice-Ticker-temp.dmg"
DMG_PATH="$DIST_DIR/Hashprice-Ticker.dmg"
VOLUME_NAME="Hashprice Ticker"

rm -rf "$DERIVED_DATA" "$DMG_DIR"
mkdir -p "$DIST_DIR" "$DMG_DIR"

python3 "$ROOT_DIR/design/generate_dmg_background.py"

xcodebuild \
  -project "$PROJECT" \
  -scheme "$SCHEME" \
  -configuration Debug \
  -derivedDataPath "$DERIVED_DATA" \
  -destination "platform=macOS,arch=arm64" \
  ARCHS=arm64 \
  ONLY_ACTIVE_ARCH=YES \
  build

mkdir -p "$BACKGROUND_DIR"
ditto "$APP_PATH" "$DMG_DIR/$APP_NAME"
cp "$BACKGROUND_SRC" "$BACKGROUND_DIR/dmg-background.png"
ln -s /Applications "$DMG_DIR/Applications"
cat > "$DMG_DIR/.hidden" <<'EOF'
.background
.fseventsd
EOF

rm -f "$DMG_PATH" "$RW_DMG_PATH"
while hdiutil info | grep -q "/Volumes/$VOLUME_NAME"; do
  EXISTING_DEVICE="$(hdiutil info | awk -v vol="/Volumes/$VOLUME_NAME" '$0 ~ vol {print prev} {prev=$1}' | tail -n 1)"
  if [[ -n "${EXISTING_DEVICE:-}" ]]; then
    hdiutil detach "$EXISTING_DEVICE" || true
  else
    break
  fi
done

hdiutil create \
  -srcfolder "$DMG_DIR" \
  -volname "$VOLUME_NAME" \
  -fs HFS+ \
  -fsargs "-c c=64,a=16,e=16" \
  -format UDRW \
  -size 20m \
  "$RW_DMG_PATH"

ATTACH_OUTPUT="$(hdiutil attach -readwrite -noverify -noautoopen "$RW_DMG_PATH")"
DEVICE="$(printf '%s\n' "$ATTACH_OUTPUT" | awk '/Apple_HFS/ {print $1; exit}')"
MOUNT_POINT="$(printf '%s\n' "$ATTACH_OUTPUT" | awk -F '\t' '/Apple_HFS/ {print $3; exit}')"

osascript <<EOF
tell application "Finder"
  tell disk "$(basename "$MOUNT_POINT")"
    open
    set current view of container window to icon view
    set toolbar visible of container window to false
    set statusbar visible of container window to false
    set the bounds of container window to {120, 120, 1320, 880}
    set viewOptions to the icon view options of container window
    set arrangement of viewOptions to not arranged
    set icon size of viewOptions to 128
    set text size of viewOptions to 16
    set background picture of viewOptions to file ".background:dmg-background.png"
    set position of item "$APP_NAME" of container window to {240, 410}
    set position of item "Applications" of container window to {960, 410}
    try
      set position of item ".background" of container window to {56, 660}
      set position of item ".fseventsd" of container window to {1120, 660}
    end try
    update without registering applications
    delay 2
    close
    open
    delay 2
  end tell
end tell
EOF

bless --folder "$MOUNT_POINT" --openfolder "$MOUNT_POINT" || true
chflags hidden "$MOUNT_POINT/.background" || true
chflags hidden "$MOUNT_POINT/.fseventsd" || true
SetFile -a V "$MOUNT_POINT/.background" || true
SetFile -a V "$MOUNT_POINT/.fseventsd" || true
chmod -Rf go-w "$MOUNT_POINT"
sync
hdiutil detach "$DEVICE"

hdiutil convert "$RW_DMG_PATH" -format UDZO -imagekey zlib-level=9 -o "$DMG_PATH"
rm -f "$RW_DMG_PATH"

echo "Created $DMG_PATH"
