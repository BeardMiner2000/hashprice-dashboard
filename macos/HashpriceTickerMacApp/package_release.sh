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
DMG_PATH="$DIST_DIR/Hashprice-Ticker.dmg"

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

cp -R "$APP_PATH" "$DMG_DIR/$APP_NAME"
ln -s /Applications "$DMG_DIR/Applications"
rm -f "$DMG_PATH"

hdiutil create \
  -volname "Hashprice Ticker" \
  -srcfolder "$DMG_DIR" \
  -ov \
  -format UDZO \
  "$DMG_PATH"

echo "Created $DMG_PATH"
