import Foundation
import Security
import LocalAuthentication

@MainActor
final class PairingKeychain: PairingIdentityStore {
    private let service = "org.safememory.probe.pairing"
    private let account = "installation-v1"
    private let marker = "SafeMemoryProbe.installation-v1"

    private var query: [String: Any] {
        [kSecClass as String: kSecClassGenericPassword, kSecAttrService as String: service,
         kSecAttrAccount as String: account, kSecAttrSynchronizable as String: false]
    }

    func load() throws -> PairingIdentity? {
        var request = query
        request[kSecReturnData as String] = true
        request[kSecMatchLimit as String] = kSecMatchLimitOne
        let context = LAContext(); context.interactionNotAllowed = true
        request[kSecUseAuthenticationContext as String] = context
        var result: CFTypeRef?
        let status = SecItemCopyMatching(request as CFDictionary, &result)
        let installation = UserDefaults.standard.string(forKey: marker)
        if status == errSecItemNotFound {
            guard installation == nil else { throw PairingFailure.relinkRequired }
            return nil
        }
        guard status == errSecSuccess, let data = result as? Data, data.count <= 4096,
              let identity = try? JSONDecoder().decode(PairingIdentity.self, from: data) else { throw PairingFailure.secureStorage }
        try identity.validate()
        // Keychain may outlive app deletion. A missing/mismatched sandbox marker
        // never silently resurrects a prior installation or library association.
        guard installation == identity.installationID else { throw PairingFailure.relinkRequired }
        return identity
    }

    func create(deviceName: String) throws -> PairingIdentity {
        guard try load() == nil, PairingRequests.text(deviceName, maximum: 100) else { throw PairingFailure.relinkRequired }
        var bytes = [UInt8](repeating: 0, count: 32)
        guard SecRandomCopyBytes(kSecRandomDefault, bytes.count, &bytes) == errSecSuccess else { throw PairingFailure.secureStorage }
        let credential = Data(bytes).base64EncodedString().replacingOccurrences(of: "+", with: "-").replacingOccurrences(of: "/", with: "_").replacingOccurrences(of: "=", with: "")
        let local = PairingIdentity(installationID: UUID().uuidString, libraryID: "local-library-" + UUID().uuidString,
            deviceName: deviceName, credential: credential, claimID: nil, expiresAt: nil)
        try local.validate()
        var item = query
        item[kSecAttrAccessible as String] = kSecAttrAccessibleWhenUnlockedThisDeviceOnly
        item[kSecValueData as String] = try JSONEncoder().encode(local)
        guard SecItemAdd(item as CFDictionary, nil) == errSecSuccess else { throw PairingFailure.secureStorage }
        // Only this non-secret installation marker is stored outside Keychain.
        UserDefaults.standard.set(local.installationID, forKey: marker)
        return local
    }

    func saveClaim(_ identity: PairingIdentity) throws {
        try identity.validate()
        guard let previous = try load(), previous.installationID == identity.installationID,
              previous.libraryID == identity.libraryID, previous.deviceName == identity.deviceName,
              previous.credential == identity.credential, identity.claimID != nil,
              previous.claimID == nil || previous.claimID == identity.claimID else { throw PairingFailure.relinkRequired }
        let update: [String: Any] = [kSecValueData as String: try JSONEncoder().encode(identity)]
        guard SecItemUpdate(query as CFDictionary, update as CFDictionary) == errSecSuccess else { throw PairingFailure.secureStorage }
    }
}
