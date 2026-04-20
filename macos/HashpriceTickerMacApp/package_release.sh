#!/bin/zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT="$ROOT_DIR/HashpriceTickerMacApp.xcodeproj"
SCHEME="HashpriceTicker"
DERIVED_DATA="$ROOT_DIR/.derived-data"
BUILD_DIR="$DERIVED_DATA/Build/Products/Release"
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

xcodebuild \
  -project "$PROJECT" \
  -scheme "$SCHEME" \
  -configuration Release \
  -derivedDataPath "$DERIVED_DATA" \
  -destination "platform=macOS,arch=arm64" \
  ARCHS=arm64 \
  ONLY_ACTIVE_ARCH=YES \
  build

mkdir -p "$BACKGROUND_DIR"
cp -R "$APP_PATH" "$DMG_DIR/$APP_NAME"
cp "$BACKGROUND_SRC" "$BACKGROUND_DIR/dmg-background.png"
ln -s /Applications "$DMG_DIR/Applications"

rm -f "$DMG_PATH" "$RW_DMG_PATH"
hdiutil create \
  -srcfolder "$DMG_DIR" \
  -volname "$VOLUME_NAME" \
  -fs HFS+ \
  -fsargs "-c c=64,a=16,e=16" \
  -format UDRW \
  -size 20m \
  "$RW_DMG_PATH"

DEVICE="$(hdiutil attach -readwrite -noverify -noautoopen "$RW_DMG_PATH" | awk '/Apple_HFS/ {print $1; exit}')"
MOUNT_POINT="/Volumes/$VOLUME_NAME"

osascript <<EOF
tell application "Finder"
  tell disk "$VOLUME_NAME"
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
    close
    open
    update without registering applications
    delay 2
  end tell
end tell
EOF

chmod -Rf go-w "$MOUNT_POINT"
sync
hdiutil detach "$DEVICE"

hdiutil convert "$RW_DMG_PATH" -format UDZO -imagekey zlib-level=9 -o "$DMG_PATH"
rm -f "$RW_DMG_PATH"

echo "Created $DMG_PATH"
