# Hashprice Ticker Mac App

Native macOS menu bar app project for the hosted hashprice API.

## Generate the Xcode project

```bash
xcodegen generate
```

## Build from terminal

```bash
xcodebuild -project HashpriceTickerMacApp.xcodeproj -scheme HashpriceTicker -configuration Debug build
```

## Run in Xcode

1. Open `HashpriceTickerMacApp.xcodeproj`
2. Choose the `HashpriceTicker` scheme
3. Run

The app is an `LSUIElement` menu bar app and should not appear in the Dock.
