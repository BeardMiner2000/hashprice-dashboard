import SwiftUI

struct ContentView: View {
    @EnvironmentObject private var appState: AppState

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack(alignment: .center, spacing: 12) {
                ZStack {
                    Circle()
                        .fill(
                            LinearGradient(
                                colors: [Color(red: 0.97, green: 0.59, blue: 0.10), Color(red: 0.98, green: 0.71, blue: 0.18)],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .frame(width: 28, height: 28)
                    Text("₿")
                        .font(.system(size: 15, weight: .heavy, design: .rounded))
                        .foregroundStyle(.black.opacity(0.85))
                }

                VStack(alignment: .leading, spacing: 3) {
                    Text("BITCOIN HASHPRICE")
                        .font(.system(size: 11, weight: .bold, design: .rounded))
                        .foregroundStyle(.white.opacity(0.88))
                    Text(appState.statusText)
                        .font(.system(size: 10, weight: .medium, design: .monospaced))
                        .foregroundStyle(.white.opacity(0.45))
                }
                Spacer()
            }

            HStack(spacing: 10) {
                Text("Ticker Speed")
                    .font(.system(size: 12, weight: .medium, design: .rounded))
                    .foregroundStyle(.white.opacity(0.68))

                Spacer()

                speedButton("◀") {
                    appState.decreaseScrollSpeed()
                }

                Text("\(appState.scrollSpeedPercent)%")
                    .font(.system(size: 12, weight: .regular, design: .monospaced))
                    .foregroundStyle(.white.opacity(0.92))
                    .frame(width: 44)

                speedButton("▶") {
                    appState.increaseScrollSpeed()
                }
            }

            tickerBoard

            VStack(alignment: .leading, spacing: 8) {
                metricRow("Realtime", "\(appState.realtimeText)\(appState.hashpriceComparisonText)", accent: colorForComparison(appState.hashpriceComparisonText, fallback: .white))
                metricRow("Vs 7D", appState.pctVs7dText, accent: appState.pctVs7dPositive ? Color.green : Color.red)
                metricRow("BTC Spot", "$\(appState.bitcoinText)\(appState.bitcoinComparisonText)", accent: colorForComparison(appState.bitcoinComparisonText, fallback: .white))
                metricRow("Network", "\(appState.hashrateText)\(appState.hashrateComparisonText)", accent: colorForComparison(appState.hashrateComparisonText, fallback: Color.white.opacity(0.9)))
                metricRow("7D Avg", "\(appState.sevenDayText)\(appState.sevenDayComparisonText)", accent: colorForComparison(appState.sevenDayComparisonText, fallback: Color.white.opacity(0.88)))
                metricRow("1D Raw", appState.oneDayText, accent: Color.white.opacity(0.88))
                metricRow("Issuance/day", appState.issuanceText, accent: Color.white.opacity(0.9))
                metricRow("Revenue/day", appState.revenueText, accent: Color.white.opacity(0.95))
                metricRow("Block Reward", appState.blockRewardText, accent: Color.orange)
            }

            Divider()
                .overlay(Color.white.opacity(0.08))

            HStack(spacing: 8) {
                appleButton("Refresh") {
                    Task { await appState.refresh() }
                }
                appleButton("Dashboard") {
                    appState.openDashboard()
                }
                appleButton(appState.launchAtLoginEnabled ? "Login: On" : "Login: Off") {
                    appState.toggleLaunchAtLogin()
                }
                appleButton("About") {
                    appState.openAboutPanel()
                }
                appleButton("Quit") {
                    NSApplication.shared.terminate(nil)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .padding(16)
        .frame(width: 332)
        .background(
            ZStack {
                LinearGradient(
                    colors: [
                        Color(red: 0.09, green: 0.10, blue: 0.12),
                        Color(red: 0.05, green: 0.06, blue: 0.08)
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
                RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .stroke(Color.white.opacity(0.06), lineWidth: 1)
                    .padding(1)
            }
        )
    }

    private var tickerBoard: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 8) {
                Circle()
                    .fill(Color.red)
                    .frame(width: 6, height: 6)
                Circle()
                    .fill(Color.yellow)
                    .frame(width: 6, height: 6)
                Circle()
                    .fill(Color.green)
                    .frame(width: 6, height: 6)
                Spacer()
                Text("LIVE TICKER")
                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                    .foregroundStyle(.white.opacity(0.48))
            }

            HStack(spacing: 0) {
                Text("₿ ")
                    .font(.system(size: 18, weight: .bold, design: .monospaced))
                    .foregroundStyle(Color(red: 0.97, green: 0.62, blue: 0.16))
                Text(appState.currentFrame)
                    .font(.system(size: 18, weight: .bold, design: .monospaced))
                    .foregroundStyle(.white)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.horizontal, 10)
            .padding(.vertical, 10)
            .background(
                RoundedRectangle(cornerRadius: 10, style: .continuous)
                    .fill(Color.black.opacity(0.33))
            )
        }
        .padding(12)
        .background(
            RoundedRectangle(cornerRadius: 16, style: .continuous)
                .fill(
                    LinearGradient(
                        colors: [
                            Color(red: 0.10, green: 0.13, blue: 0.18),
                            Color(red: 0.07, green: 0.08, blue: 0.11)
                        ],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .overlay(
                    RoundedRectangle(cornerRadius: 16, style: .continuous)
                        .stroke(Color.white.opacity(0.08), lineWidth: 1)
                )
        )
    }

    private func metricRow(_ label: String, _ value: String, accent: Color) -> some View {
        HStack(spacing: 10) {
            Text(label)
                .font(.system(size: 13, weight: .medium, design: .monospaced))
                .foregroundStyle(.white.opacity(0.52))
            Spacer(minLength: 8)
            Text(value)
                .font(.system(size: 14, weight: .bold, design: .monospaced))
                .foregroundStyle(accent)
        }
        .padding(.vertical, 2)
    }

    private func appleButton(_ title: String, action: @escaping () -> Void) -> some View {
        Button(title, action: action)
            .buttonStyle(.plain)
            .font(.system(size: 12, weight: .semibold))
            .foregroundStyle(.white.opacity(0.92))
            .padding(.horizontal, 12)
            .padding(.vertical, 7)
            .background(
                Capsule(style: .continuous)
                    .fill(Color.white.opacity(0.10))
            )
            .overlay(
                Capsule(style: .continuous)
                    .stroke(Color.white.opacity(0.06), lineWidth: 1)
            )
    }

    private func speedButton(_ title: String, action: @escaping () -> Void) -> some View {
        Button(title, action: action)
            .buttonStyle(.plain)
            .font(.system(size: 11, weight: .bold, design: .rounded))
            .foregroundStyle(.white.opacity(0.92))
            .frame(width: 22, height: 22)
            .background(
                RoundedRectangle(cornerRadius: 6, style: .continuous)
                    .fill(Color.white.opacity(0.10))
            )
            .overlay(
                RoundedRectangle(cornerRadius: 6, style: .continuous)
                    .stroke(Color.white.opacity(0.06), lineWidth: 1)
            )
    }

    private func colorForComparison(_ comparison: String, fallback: Color) -> Color {
        guard let first = comparison.first else { return fallback }
        if first == "▲" { return .green }
        if first == "▼" { return .red }
        return fallback
    }
}
