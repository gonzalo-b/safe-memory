import SwiftUI

@MainActor
struct PairingSection: View {
    @Environment(\.scenePhase) private var scenePhase
    @State private var coordinator = PairingCoordinator(store: PairingKeychain())
    @State private var secret = ""
    @State private var deviceName = "iPhone"
    @State private var acknowledgesAlias = false
    @State private var running = false
    @State private var identityExists = false
    @State private var claimExists = false
    @State private var blocked = false
    @State private var fingerprint = ""
    @State private var libraryAlias = ""
    @State private var status = "Not connected. Start a pairing code in your signed-in Memory web account."
    @State private var operation: Task<Void, Never>?

    var body: some View {
        Section("Connect to Memory") {
            Text("Destination: https://memory.lazyagent.ai")
            Text("Connecting sends only a new Memory credential, this device label and a local library alias. Pairing sends no Photos data and does not start an import.")
            Text("The alias identifies this installation’s chosen library; Apple has not verified its identity. A changed library or reinstallation requires explicit relinking, which this probe does not yet provide.")
            if !claimExists {
                TextField("Device label", text: $deviceName).disabled(identityExists || running)
                SecureField("Pairing code from Memory web", text: $secret)
                    .textInputAutocapitalization(.never).autocorrectionDisabled().privacySensitive()
                    .disabled(running || blocked)
                    .onChange(of: secret) { _, value in if value.utf8.count > 256 { secret = "" } }
                Toggle("Use this installation for the chosen library", isOn: $acknowledgesAlias).disabled(running || blocked)
                Button(running ? "Connecting…" : "Connect") { connect() }
                    .disabled(running || blocked || !acknowledgesAlias || !PairingRequests.canonicalToken(secret) || !PairingRequests.text(deviceName, maximum: 100))
            }
            if !fingerprint.isEmpty {
                Text("Compare all 64 characters with the pending device in Memory web. Confirm there only if the complete fingerprint matches.")
                Text(fingerprint).font(.system(.footnote, design: .monospaced))
                    .textSelection(.enabled).fixedSize(horizontal: false, vertical: true)
                    .accessibilityLabel("Full credential SHA-256 fingerprint: " + fingerprint)
            }
            if !libraryAlias.isEmpty {
                Text("Local alias: " + libraryAlias).font(.caption).textSelection(.enabled)
            }
            Button(running ? "Working…" : "Check status") { check() }
                .disabled(running || blocked || !claimExists)
            Text(status)
            Text("A new connection starts restricted. Metadata import requires its own explicit selection and consent; local metadata inspection remains separate.")
        }
        .task { load() }
        .onChange(of: scenePhase) { _, phase in
            if phase == .active { load() }
            else {
                secret = ""; acknowledgesAlias = false
                operation?.cancel(); coordinator.clearVerifiedBinding()
            }
        }
    }

    private func snapshot() {
        identityExists = coordinator.identity != nil
        claimExists = coordinator.identity?.claimID != nil
        fingerprint = coordinator.identity?.fingerprint ?? ""
        libraryAlias = coordinator.identity?.libraryID ?? ""
        if let saved = coordinator.identity?.deviceName { deviceName = saved }
    }

    private func load() {
        guard !running else { return }
        do {
            try coordinator.load(); snapshot(); blocked = false
            if claimExists { status = "Claim retained. Confirm its full fingerprint in Memory web, then explicitly check status." }
            else if identityExists { status = "Identity retained after an unfinished attempt. Retry Connect only with the same pairing code. New/relink setup is not available here." }
        } catch {
            blocked = true; fingerprint = ""; libraryAlias = ""; identityExists = false; claimExists = false
            status = message(error)
        }
    }

    private func connect() {
        let transient = secret; secret = ""
        let label = deviceName
        running = true; status = "Saving the local identity and requesting a claim."
        operation = Task {
            do {
                try await coordinator.connect(secret: transient, deviceName: label)
                status = "Claim received. Compare the complete fingerprint and confirm in Memory web. This is not yet a confirmed device."
            } catch { status = message(error) }
            snapshot(); running = false; operation = nil
        }
    }

    private func check() {
        running = true; status = "Checking owner confirmation."
        operation = Task {
            do {
                try await coordinator.checkStatus()
                status = "Owner confirmation verified. This checks identity only. It does not read Photos, send a sample or grant access to server records."
            } catch { status = message(error) }
            snapshot(); running = false; operation = nil
        }
    }

    private func message(_ error: Error) -> String {
        switch error {
        case PairingFailure.unauthorized: return "Not confirmed or no longer authorized. Check the owner web account; no Photos data is accessible."
        case PairingFailure.relinkRequired: return "Installation identity is missing or differs from Keychain. Explicit new/relink setup is required and is not implemented in this probe."
        case PairingFailure.secureStorage: return "Secure identity storage is unavailable. Unlock the device and reopen the probe. No replacement credential was created."
        case PairingFailure.cancelled, is CancellationError: return "Request cancelled. Its server outcome may be unknown; the local credential is retained."
        default: return "Connection could not be verified safely. No automatic retry occurred. A pending claim may still exist; retain this identity and check the owner web account."
        }
    }
}
