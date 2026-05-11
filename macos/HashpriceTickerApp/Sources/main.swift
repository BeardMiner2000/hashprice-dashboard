import AppKit
import Foundation

private struct APIResponse: Decodable {
    let timestamp: String
    let spot: Double
    let hashprice_rt: Double
}

private enum AppConfig {
    static let apiURL = URL(string: ProcessInfo.processInfo.environment["HASHPRICE_API_URL"] ?? "https://hashprice.coffeecoffeecoffeecoffee.com/api/hashprice")!
    static let dashboardURL = URL(string: ProcessInfo.processInfo.environment["HASHPRICE_DASHBOARD_URL"] ?? "https://hashprice.coffeecoffeecoffeecoffee.com/")!
    static let refreshInterval: TimeInterval = 60
    static let scrollInterval: TimeInterval = 0.18
    static let spacer = "     "
}

@MainActor
private final class HashpriceMenuBarController: NSObject, NSApplicationDelegate {
    private let statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
    private let menu = NSMenu()

    private let summaryItem = NSMenuItem(title: "Loading...", action: nil, keyEquivalent: "")
    private let timestampItem = NSMenuItem(title: "", action: nil, keyEquivalent: "")
    private let refreshItem = NSMenuItem(title: "Refresh Now", action: #selector(refreshNow), keyEquivalent: "r")
    private let openItem = NSMenuItem(title: "Open Dashboard", action: #selector(openDashboard), keyEquivalent: "")
    private let quitItem = NSMenuItem(title: "Quit", action: #selector(quitApp), keyEquivalent: "q")

    private var refreshTimer: Timer?
    private var scrollTimer: Timer?
    private var titleFrames: [String] = ["Loading..."]
    private var frameIndex = 0

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.accessory)
        configureStatusItem()
        configureMenu()
        fetchLatest()
        startTimers()
    }

    func applicationWillTerminate(_ notification: Notification) {
        refreshTimer?.invalidate()
        scrollTimer?.invalidate()
    }

    private func configureStatusItem() {
        if let button = statusItem.button {
            button.font = NSFont.monospacedSystemFont(ofSize: 12, weight: .medium)
            button.title = "Loading..."
            button.toolTip = "Hashprice Ticker"
        }
        statusItem.menu = menu
    }

    private func configureMenu() {
        summaryItem.isEnabled = false
        timestampItem.isEnabled = false

        refreshItem.target = self
        openItem.target = self
        quitItem.target = self

        menu.addItem(summaryItem)
        menu.addItem(timestampItem)
        menu.addItem(.separator())
        menu.addItem(refreshItem)
        menu.addItem(openItem)
        menu.addItem(.separator())
        menu.addItem(quitItem)
    }

    private func startTimers() {
        refreshTimer = Timer(timeInterval: AppConfig.refreshInterval, target: self, selector: #selector(handleRefreshTimer), userInfo: nil, repeats: true)
        scrollTimer = Timer(timeInterval: AppConfig.scrollInterval, target: self, selector: #selector(handleScrollTimer), userInfo: nil, repeats: true)
        if let refreshTimer {
            RunLoop.main.add(refreshTimer, forMode: .common)
        }
        if let scrollTimer {
            RunLoop.main.add(scrollTimer, forMode: .common)
        }
    }

    private func fetchLatest() {
        var request = URLRequest(url: AppConfig.apiURL)
        request.timeoutInterval = 8

        URLSession.shared.dataTask(with: request) { [weak self] data, _, error in
            guard let self else { return }

            if let error {
                DispatchQueue.main.async {
                    self.applyErrorState("API unavailable: \(error.localizedDescription)")
                }
                return
            }

            guard let data else {
                DispatchQueue.main.async {
                    self.applyErrorState("API unavailable: empty response")
                }
                return
            }

            do {
                let payload = try JSONDecoder().decode(APIResponse.self, from: data)
                DispatchQueue.main.async {
                    self.applyPayload(payload)
                }
            } catch {
                DispatchQueue.main.async {
                    self.applyErrorState("Invalid response")
                }
            }
        }.resume()
    }

    private func applyPayload(_ payload: APIResponse) {
        let btcText = formatCurrency(payload.spot)
        let hashpriceText = String(format: "%.2f", payload.hashprice_rt)
        let tickerText = "₿ \(btcText)  •  $/PH \(hashpriceText)\(AppConfig.spacer)"

        titleFrames = buildFrames(from: tickerText)
        frameIndex = 0
        statusItem.button?.title = titleFrames.first ?? tickerText
        summaryItem.title = "₿ \(btcText)   $/PH \(hashpriceText)"
        timestampItem.title = "Updated: \(payload.timestamp)"
        statusItem.button?.toolTip = "Bitcoin \(btcText) | Hashprice \(hashpriceText)"
    }

    private func applyErrorState(_ message: String) {
        titleFrames = ["₿ --  •  $/PH --"]
        frameIndex = 0
        statusItem.button?.title = titleFrames[0]
        summaryItem.title = "Unable to load hashprice"
        timestampItem.title = message
        statusItem.button?.toolTip = message
    }

    private func buildFrames(from text: String) -> [String] {
        let characters = Array(text)
        guard !characters.isEmpty else { return [""] }

        var frames: [String] = []
        for index in characters.indices {
            let suffix = characters[index...]
            let prefix = characters[..<index]
            frames.append(String(suffix + prefix))
        }
        return frames
    }

    private func advanceTicker() {
        guard !titleFrames.isEmpty else { return }
        statusItem.button?.title = titleFrames[frameIndex]
        frameIndex = (frameIndex + 1) % titleFrames.count
    }

    private func formatCurrency(_ value: Double) -> String {
        let formatter = NumberFormatter()
        formatter.numberStyle = .decimal
        formatter.maximumFractionDigits = 0
        formatter.minimumFractionDigits = 0
        return formatter.string(from: NSNumber(value: value)) ?? String(format: "%.0f", value)
    }

    @objc
    private func handleRefreshTimer() {
        fetchLatest()
    }

    @objc
    private func handleScrollTimer() {
        advanceTicker()
    }

    @objc
    private func refreshNow() {
        fetchLatest()
    }

    @objc
    private func openDashboard() {
        NSWorkspace.shared.open(AppConfig.dashboardURL)
    }

    @objc
    private func quitApp() {
        NSApp.terminate(nil)
    }
}

let app = NSApplication.shared
private let delegate = HashpriceMenuBarController()
app.delegate = delegate
app.run()
