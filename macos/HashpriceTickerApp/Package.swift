// swift-tools-version: 6.0

import PackageDescription

let package = Package(
    name: "HashpriceTickerApp",
    platforms: [
        .macOS(.v13),
    ],
    products: [
        .executable(
            name: "HashpriceTickerApp",
            targets: ["HashpriceTickerApp"]
        ),
    ],
    targets: [
        .executableTarget(
            name: "HashpriceTickerApp",
            path: "Sources"
        ),
    ]
)
