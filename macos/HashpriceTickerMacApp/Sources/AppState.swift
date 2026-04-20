import Foundation
import SwiftUI
import AppKit
import ServiceManagement

struct HashpricePayload: Decodable {
    let timestamp: String
    let spot: Double
    let hashprice_rt: Double
    let hashprice_1d: Double
    let hashprice_7d: Double
    let pct_vs_7d: Double
    let network_hashrate_ph: Double
    let bitcoin_per_block: Double
    let issuance_btc_day: Double
    let fee_btc_day: Double
    let btc_revenue_day: Double
    let fee_pct: Double
    let spot_vs_24h_pct: Double?
    let hashprice_rt_vs_24h_pct: Double?
    let hashprice_7d_change_pct: Double?
    let network_hashrate_vs_24h_pct: Double?
    let fee_pct_vs_daily_pct: Double?
}

@MainActor
final class AppState: ObservableObject {
    @Published var currentFrame = "Loading..."
    @Published var currentAttributedFrame = NSAttributedString(string: "Loading...")
    @Published var bitcoinText = "--"
    @Published var hashpriceText = "--"
    @Published var statusText = "Loading latest data..."
    @Published var realtimeText = "--"
    @Published var oneDayText = "--"
    @Published var sevenDayText = "--"
    @Published var pctVs7dText = "--"
    @Published var pctVs7dPositive = true
    @Published var hashrateText = "--"
    @Published var feesText = "--"
    @Published var issuanceText = "--"
    @Published var revenueText = "--"
    @Published var blockRewardText = "--"
    @Published var feePctText = "--"
    @Published var bitcoinComparisonText = ""
    @Published var hashpriceComparisonText = ""
    @Published var sevenDayComparisonText = ""
    @Published var hashrateComparisonText = ""
    @Published var feePctComparisonText = ""
    @Published var scrollSpeedPercent = 90
    @Published var launchAtLoginEnabled = false
    @Published var launchAtLoginAvailable = false

    let dashboardURL: URL

    private let apiURL: URL
    private let refreshInterval: TimeInterval = 60
    private let baseScrollInterval: TimeInterval = 0.14
    private let spacer = "   "
    private let tickerWindowWidth = 16

    private var tickerFrames = [NSAttributedString(string: "Loading...")]
    private var frameIndex = 0
    private var refreshTask: Task<Void, Never>?
    private var tickerTask: Task<Void, Never>?

    private let labelAttributes: [NSAttributedString.Key: Any] = [
        .font: NSFont.monospacedSystemFont(ofSize: 12, weight: .medium),
        .foregroundColor: NSColor(calibratedRed: 0.53, green: 0.60, blue: 0.72, alpha: 0.95)
    ]
    private let accentAttributes: [NSAttributedString.Key: Any] = [
        .font: NSFont.monospacedSystemFont(ofSize: 12, weight: .medium),
        .foregroundColor: NSColor(calibratedRed: 0.98, green: 0.69, blue: 0.20, alpha: 1.0)
    ]
    private let positiveAttributes: [NSAttributedString.Key: Any] = [
        .font: NSFont.monospacedSystemFont(ofSize: 12, weight: .regular),
        .foregroundColor: NSColor(calibratedRed: 0.36, green: 0.87, blue: 0.56, alpha: 1.0)
    ]
    private let neutralValueAttributes: [NSAttributedString.Key: Any] = [
        .font: NSFont.monospacedSystemFont(ofSize: 12, weight: .regular),
        .foregroundColor: NSColor(calibratedWhite: 0.96, alpha: 1.0)
    ]
    private let negativeAttributes: [NSAttributedString.Key: Any] = [
        .font: NSFont.monospacedSystemFont(ofSize: 12, weight: .regular),
        .foregroundColor: NSColor(calibratedRed: 0.95, green: 0.38, blue: 0.44, alpha: 1.0)
    ]
    private let separatorAttributes: [NSAttributedString.Key: Any] = [
        .font: NSFont.monospacedSystemFont(ofSize: 12, weight: .medium),
        .foregroundColor: NSColor(calibratedWhite: 0.42, alpha: 1.0)
    ]

    init() {
        let env = ProcessInfo.processInfo.environment
        self.apiURL = URL(string: env["HASHPRICE_API_URL"] ?? "https://hashprice-dashboard-dtsg.onrender.com/api/hashprice")!
        self.dashboardURL = URL(string: env["HASHPRICE_DASHBOARD_URL"] ?? "https://hashprice-dashboard-dtsg.onrender.com/")!
        refreshLaunchAtLoginState()

        startTickerLoop()
        startRefreshLoop()
        Task {
            await refresh()
        }
    }

    deinit {
        refreshTask?.cancel()
        tickerTask?.cancel()
    }

    func refresh() async {
        do {
            let (data, _) = try await URLSession.shared.data(from: apiURL)
            let payload = try JSONDecoder().decode(HashpricePayload.self, from: data)
            apply(payload)
        } catch {
            applyError(error.localizedDescription)
        }
    }

    func openDashboard() {
        NSWorkspace.shared.open(dashboardURL)
    }

    func openAboutPanel() {
        NSApplication.shared.orderFrontStandardAboutPanel([
            NSApplication.AboutPanelOptionKey.applicationName: "Hashprice Ticker",
            NSApplication.AboutPanelOptionKey.applicationVersion: Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "1.0",
            NSApplication.AboutPanelOptionKey.version: Bundle.main.object(forInfoDictionaryKey: "CFBundleVersion") as? String ?? "1",
            NSApplication.AboutPanelOptionKey.credits: NSAttributedString(string: "Created by jlzoeckler"),
            NSApplication.AboutPanelOptionKey(rawValue: "Copyright"): Bundle.main.object(forInfoDictionaryKey: "NSHumanReadableCopyright") as? String ?? "Copyright © 2026 jlzoeckler"
        ])
        NSApplication.shared.activate(ignoringOtherApps: true)
    }

    func toggleLaunchAtLogin() {
        guard launchAtLoginAvailable else { return }

        do {
            if launchAtLoginEnabled {
                try SMAppService.mainApp.unregister()
            } else {
                try SMAppService.mainApp.register()
            }
            refreshLaunchAtLoginState()
        } catch {
            statusText = "Launch at login error: \(error.localizedDescription)"
        }
    }

    func increaseScrollSpeed() {
        scrollSpeedPercent = min(scrollSpeedPercent + 10, 160)
    }

    func decreaseScrollSpeed() {
        scrollSpeedPercent = max(scrollSpeedPercent - 10, 50)
    }

    private func startRefreshLoop() {
        refreshTask?.cancel()
        refreshTask = Task { [weak self] in
            guard let self else { return }
            while !Task.isCancelled {
                try? await Task.sleep(for: .seconds(refreshInterval))
                if Task.isCancelled { return }
                await refresh()
            }
        }
    }

    private func startTickerLoop() {
        tickerTask?.cancel()
        tickerTask = Task { [weak self] in
            guard let self else { return }
            while !Task.isCancelled {
                let interval = baseScrollInterval * (100.0 / Double(scrollSpeedPercent))
                try? await Task.sleep(for: .seconds(interval))
                if Task.isCancelled { return }
                advanceTicker()
            }
        }
    }

    private func apply(_ payload: HashpricePayload) {
        bitcoinText = formatNumber(payload.spot)
        hashpriceText = String(format: "%.2f", payload.hashprice_rt)
        realtimeText = String(format: "$%.2f / PH / day", payload.hashprice_rt)
        oneDayText = String(format: "$%.2f", payload.hashprice_1d)
        sevenDayText = String(format: "$%.2f", payload.hashprice_7d)
        pctVs7dText = String(format: "%@%.2f%%", payload.pct_vs_7d >= 0 ? "▲" : "▼", abs(payload.pct_vs_7d))
        pctVs7dPositive = payload.pct_vs_7d >= 0
        hashrateText = "\(formatNumber(payload.network_hashrate_ph)) PH/s"
        feesText = String(format: "%.3f BTC", payload.fee_btc_day)
        issuanceText = String(format: "%.3f BTC", payload.issuance_btc_day)
        revenueText = String(format: "%.3f BTC", payload.btc_revenue_day)
        blockRewardText = String(format: "%.3f BTC", payload.bitcoin_per_block)
        feePctText = String(format: "%.2f%%", payload.fee_pct)
        statusText = "Updated: \(payload.timestamp)"
        bitcoinComparisonText = comparisonString(percent: payload.spot_vs_24h_pct)
        hashpriceComparisonText = comparisonString(percent: payload.hashprice_rt_vs_24h_pct)
        sevenDayComparisonText = comparisonString(percent: payload.hashprice_7d_change_pct)
        hashrateComparisonText = comparisonString(percent: payload.network_hashrate_vs_24h_pct)
        feePctComparisonText = comparisonString(percent: payload.fee_pct_vs_daily_pct)

        let segments = buildTickerSegments()
        tickerFrames = buildFrames(from: segments, windowWidth: tickerWindowWidth)
        frameIndex = 0
        applyCurrentFrame()
    }

    private func applyError(_ message: String) {
        bitcoinText = "--"
        hashpriceText = "--"
        realtimeText = "--"
        oneDayText = "--"
        sevenDayText = "--"
        pctVs7dText = "--"
        pctVs7dPositive = true
        hashrateText = "--"
        feesText = "--"
        issuanceText = "--"
        revenueText = "--"
        blockRewardText = "--"
        feePctText = "--"
        bitcoinComparisonText = ""
        hashpriceComparisonText = ""
        sevenDayComparisonText = ""
        hashrateComparisonText = ""
        feePctComparisonText = ""
        statusText = "Error: \(message)"
        tickerFrames = [makeErrorFrame()]
        frameIndex = 0
        applyCurrentFrame()
    }

    private func advanceTicker() {
        guard !tickerFrames.isEmpty else { return }
        applyCurrentFrame()
        frameIndex = (frameIndex + 1) % tickerFrames.count
    }

    private func applyCurrentFrame() {
        let frame = tickerFrames[frameIndex]
        currentAttributedFrame = frame
        currentFrame = frame.string
    }

    private func buildTickerSegments() -> [(String, [NSAttributedString.Key: Any])] {
        return [
            ("₿ ", accentAttributes),
            (bitcoinText, neutralValueAttributes),
            (bitcoinComparisonText, comparisonAttributes(for: bitcoinComparisonText)),
            (spacer, separatorAttributes),
            ("$/PH ", labelAttributes),
            (hashpriceText, neutralValueAttributes),
            (hashpriceComparisonText, comparisonAttributes(for: hashpriceComparisonText)),
            (spacer, separatorAttributes),
            ("7D ", labelAttributes),
            (sevenDayText, neutralValueAttributes),
            (sevenDayComparisonText, comparisonAttributes(for: sevenDayComparisonText)),
            (spacer, separatorAttributes),
            ("NETWORK ", labelAttributes),
            (hashrateText, neutralValueAttributes),
            (hashrateComparisonText, comparisonAttributes(for: hashrateComparisonText)),
            (spacer, separatorAttributes)
        ]
    }

    private func buildFrames(from segments: [(String, [NSAttributedString.Key: Any])], windowWidth: Int) -> [NSAttributedString] {
        let glyphs = flattenGlyphs(segments: segments)
        guard !glyphs.isEmpty else { return [makeErrorFrame()] }

        let source = glyphs
        let looped = source + source

        return source.indices.map { start in
            let frame = NSMutableAttributedString()
            for glyph in looped[start..<(start + windowWidth)] {
                frame.append(NSAttributedString(string: glyph.0, attributes: glyph.1))
            }
            return frame
        }
    }

    private func flattenGlyphs(segments: [(String, [NSAttributedString.Key: Any])]) -> [(String, [NSAttributedString.Key: Any])] {
        var glyphs: [(String, [NSAttributedString.Key: Any])] = []
        for (text, attributes) in segments {
            for char in text {
                glyphs.append((String(char), attributes))
            }
        }
        return glyphs
    }

    private func makeErrorFrame() -> NSAttributedString {
        let frame = NSMutableAttributedString()
        frame.append(NSAttributedString(string: "₿ ", attributes: accentAttributes))
        frame.append(NSAttributedString(string: "--", attributes: neutralValueAttributes))
        frame.append(NSAttributedString(string: "   $/PH ", attributes: labelAttributes))
        frame.append(NSAttributedString(string: "--", attributes: neutralValueAttributes))
        return frame
    }

    private func comparisonString(percent: Double?) -> String {
        guard let pct = percent else { return "" }
        if abs(pct) < 0.005 { return "→0.00%" }
        let arrow = pct >= 0 ? "▲" : "▼"
        return String(format: "%@%.2f%%", arrow, abs(pct))
    }

    private func comparisonAttributes(for text: String) -> [NSAttributedString.Key: Any] {
        guard let first = text.first else { return neutralValueAttributes }
        if first == "▲" { return positiveAttributes }
        if first == "▼" { return negativeAttributes }
        return labelAttributes
    }

    private func formatNumber(_ value: Double) -> String {
        let formatter = NumberFormatter()
        formatter.numberStyle = .decimal
        formatter.maximumFractionDigits = 0
        return formatter.string(from: NSNumber(value: value)) ?? String(format: "%.0f", value)
    }

    private func refreshLaunchAtLoginState() {
        let status = SMAppService.mainApp.status
        launchAtLoginAvailable = status != .notFound
        launchAtLoginEnabled = status == .enabled
    }
}
