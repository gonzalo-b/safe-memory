import Foundation

struct PairingIdentity: Codable, Sendable {
    let installationID: String
    let libraryID: String
    let deviceName: String
    let credential: String
    var claimID: String?
    var expiresAt: Int64?

    var fingerprint: String { PairingRequests.fingerprint(credential) }
    func validate() throws {
        guard PairingRequests.identifier(installationID), PairingRequests.identifier(libraryID),
              PairingRequests.text(deviceName, maximum: 100), PairingRequests.canonicalToken(credential),
              claimID.map(PairingRequests.identifier) ?? true,
              (claimID == nil && expiresAt == nil) || (claimID != nil && (expiresAt ?? 0) > 0) else { throw PairingFailure.secureStorage }
    }
}

@MainActor
protocol PairingIdentityStore {
    func load() throws -> PairingIdentity?
    func create(deviceName: String) throws -> PairingIdentity
    func saveClaim(_ identity: PairingIdentity) throws
}

protocol PairingServicing: Sendable {
    func claim(secret: String, deviceName: String, libraryID: String, credential: String) async throws -> PairingClaim
    func status(deviceID: String, credential: String) async throws -> PairingBinding
}

extension PairingTransport: PairingServicing {}

/// Loading this controller never sends a request. A confirmed binding remains
/// identity-only: it does not grant export, ingest, Photos access or disclosure.
@MainActor
final class PairingCoordinator {
    private let store: any PairingIdentityStore
    private let transport: any PairingServicing
    private(set) var identity: PairingIdentity?
    private(set) var binding: PairingBinding?
    private var running = false

    init(store: any PairingIdentityStore, transport: any PairingServicing = PairingTransport()) {
        self.store = store; self.transport = transport
    }

    func load() throws { binding = nil; identity = nil; identity = try store.load() }
    func clearVerifiedBinding() { binding = nil }

    func connect(secret: String, deviceName: String) async throws {
        guard !running, PairingRequests.canonicalToken(secret), PairingRequests.text(deviceName, maximum: 100) else { throw PairingFailure.invalidInput }
        running = true; defer { running = false }; binding = nil
        // Creation persists the credential in Keychain before any network call.
        var local = try store.load() ?? store.create(deviceName: deviceName)
        try local.validate()
        guard local.claimID == nil else { throw PairingFailure.invalidInput }
        identity = local
        try Task.checkCancellation()
        let result = try await transport.claim(secret: secret, deviceName: local.deviceName, libraryID: local.libraryID, credential: local.credential)
        guard result.fingerprint == local.fingerprint, PairingRequests.identifier(result.claimID), result.expiresAt > 0 else { throw PairingFailure.invalidResponse }
        local.claimID = result.claimID; local.expiresAt = result.expiresAt
        try store.saveClaim(local)
        identity = local
    }

    func checkStatus() async throws {
        guard !running else { throw PairingFailure.invalidInput }
        running = true; defer { running = false }; binding = nil
        guard let local = try store.load(), let claimID = local.claimID else { throw PairingFailure.invalidInput }
        try local.validate(); identity = local
        let result = try await transport.status(deviceID: claimID, credential: local.credential)
        try Task.checkCancellation()
        guard result.deviceID == claimID, !result.dataAccess else { throw PairingFailure.invalidResponse }
        binding = result
    }
}
