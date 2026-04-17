import AppKit
import Combine
import SwiftUI

@MainActor
final class StatusBarController: NSObject {
    private let appState: AppState
    private let statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
    private let popover = NSPopover()
    private var cancellables: Set<AnyCancellable> = []

    init(appState: AppState) {
        self.appState = appState
        super.init()
        configureStatusItem()
        configurePopover()
        bindState()
    }

    private func configureStatusItem() {
        guard let button = statusItem.button else { return }
        button.target = self
        button.action = #selector(togglePopover)
        button.font = NSFont.monospacedSystemFont(ofSize: 12, weight: .semibold)
        button.attributedTitle = appState.currentAttributedFrame
        button.appearsDisabled = false
    }

    private func configurePopover() {
        popover.behavior = .transient
        popover.animates = true
        popover.contentSize = NSSize(width: 332, height: 374)
        popover.contentViewController = NSHostingController(
            rootView: ContentView()
                .environmentObject(appState)
        )
    }

    private func bindState() {
        appState.$currentAttributedFrame
            .receive(on: RunLoop.main)
            .sink { [weak self] frame in
                self?.statusItem.button?.attributedTitle = frame
            }
            .store(in: &cancellables)
    }

    @objc
    private func togglePopover() {
        guard let button = statusItem.button else { return }

        if popover.isShown {
            popover.performClose(nil)
        } else {
            popover.show(relativeTo: button.bounds, of: button, preferredEdge: .minY)
            popover.contentViewController?.view.window?.becomeKey()
        }
    }
}
