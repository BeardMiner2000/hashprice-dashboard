import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var appState: AppState

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Hashprice Ticker")
                .font(.title2)

            Text("API")
                .font(.headline)
            Text(appState.statusText)
                .foregroundStyle(.secondary)

            Button("Open Dashboard") {
                appState.openDashboard()
            }
        }
        .padding(20)
        .frame(width: 360)
    }
}
