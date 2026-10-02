import Foundation

@MainActor
private final class SyntheticStore: PairingIdentityStore {
    var value: PairingIdentity?
    var failLoad = false
    var failSave = false
    var creations = 0
    func load() throws -> PairingIdentity? {
        if failLoad { throw PairingFailure.relinkRequired }
        return value
    }
    func create(deviceName: String) throws -> PairingIdentity {
        creations += 1
        let result = PairingIdentity(installationID: "synthetic-installation", libraryID: "local-library-synthetic", deviceName: deviceName, credential: String(repeating: "A", count: 43), claimID: nil, expiresAt: nil)
        value = result
        return result
    }
    func saveClaim(_ identity: PairingIdentity) throws {
        if failSave { throw PairingFailure.secureStorage }
        value = identity
    }
}

private actor SyntheticService: PairingServicing {
    let store: SyntheticStore
    var claims = 0
    var checks = 0
    var reject = true
    init(store: SyntheticStore) { self.store = store }
    func setReject(_ value: Bool) { reject = value }
    func count() -> (Int, Int) { (claims, checks) }
    func claim(secret: String, deviceName: String, libraryID: String, credential: String) async throws -> PairingClaim {
        let persisted = try await store.load()
        assert(persisted?.credential == credential && persisted?.libraryID == libraryID && persisted?.deviceName == deviceName)
        claims += 1
        return PairingClaim(claimID: "synthetic-claim", fingerprint: PairingRequests.fingerprint(credential), expiresAt: 999999)
    }
    func status(deviceID: String, credential: String) async throws -> PairingBinding {
        checks += 1
        if reject { throw PairingFailure.unauthorized }
        return PairingBinding(deviceID: deviceID, ownerID: "synthetic-owner", connectionID: "synthetic-connection", vaultID: "synthetic-vault", dataAccess: false)
    }
}

@main
struct PairingLifecycleTests {
    @MainActor static func main() async throws {
        let store = SyntheticStore()
        let service = SyntheticService(store: store)
        let client = PairingCoordinator(store: store, transport: service)
        try client.load()
        let empty = await service.count()
        assert(empty == (0, 0) && store.creations == 0)
        print("PASS load_has_no_pairing_or_key_creation_side_effect")

        store.failSave = true
        do { try await client.connect(secret: String(repeating: "A", count: 43), deviceName: "Synthetic"); fatalError("Save should fail") }
        catch PairingFailure.secureStorage {}
        let original = store.value!
        assert(original.claimID == nil && store.creations == 1)
        store.failSave = false
        try await client.connect(secret: String(repeating: "A", count: 43), deviceName: "Ignored retry rename")
        assert(store.creations == 1 && store.value?.credential == original.credential && store.value?.libraryID == original.libraryID)
        assert(client.identity?.claimID == "synthetic-claim" && client.binding == nil)
        print("PASS credential_persisted_before_claim_and_reused_after_ambiguous_save")

        do { try await client.checkStatus(); fatalError("Unconfirmed status should fail") }
        catch PairingFailure.unauthorized {}
        assert(client.binding == nil)
        await service.setReject(false)
        try await client.checkStatus()
        assert(client.binding?.deviceID == client.identity?.claimID && client.binding?.dataAccess == false)
        await service.setReject(true)
        do { try await client.checkStatus(); fatalError("Revoked status should fail") }
        catch PairingFailure.unauthorized {}
        assert(client.binding == nil)
        print("PASS only_confirmed_status_binds_and_revocation_clears_binding")

        let before = await service.count()
        store.failLoad = true
        do { try client.load(); fatalError("Reinstallation must not reuse identity") }
        catch PairingFailure.relinkRequired {}
        assert(client.identity == nil && client.binding == nil)
        do { try await client.connect(secret: String(repeating: "A", count: 43), deviceName: "Synthetic"); fatalError("Relink required") }
        catch PairingFailure.relinkRequired {}
        let after = await service.count()
        assert(before == after && store.creations == 1)
        print("PASS_unrecognized_installation_requires_relink_without_network")
    }
}
