import Foundation

@MainActor private final class MemoryCheckpoints: ImportCheckpointStore {
    var value: ImportCheckpoint?
    func load() throws -> ImportCheckpoint? { value }
    func save(_ checkpoint: ImportCheckpoint) throws { value = checkpoint }
}
@MainActor private final class MemoryIdentity: PairingIdentityStore {
    let value = PairingIdentity(installationID: "synthetic-install", libraryID: "local-library", deviceName: "Synthetic", credential: String(repeating: "A", count: 43), claimID: "synthetic-device", expiresAt: 999999)
    func load() throws -> PairingIdentity? { value }
    func create(deviceName: String) throws -> PairingIdentity { fatalError("Import must not create credentials") }
    func saveClaim(_ identity: PairingIdentity) throws { fatalError("Import must not alter pairing") }
}
@MainActor private final class MemoryReader: ImportReading {
    var authorization = "limited"
    var available = true
    var changed = false
    func permission() -> String { authorization }
    func selection(ids: [String], consent: ImportConsent) async throws -> ImportSelection {
        guard available, ["full", "limited"].contains(authorization) else { throw ImportFailure.selectionChanged }
        let row = ProbeAsset(localIdentifier: "synthetic-selected", creationInstant: "2026-10-02T12:00:00.000Z", modificationInstant: nil, addedInstant: nil,
            mediaType: 1, mediaSubtypes: 0, pixelWidth: 20, pixelHeight: 10, duration: 0, isHidden: false, isFavorite: changed, sourceType: 1,
            location: nil, burstIdentifier: nil, burstSelectionTypes: 0, representsBurst: false, hasAdjustments: false, adjustmentFormatIdentifier: nil,
            resources: [], unavailable: ["capture_offset": "not_exposed_by_phasset"])
        return try ImportSelection(ids: ids, manifest: ProbeManifest(probeInstallationID: "synthetic-install", authorization: authorization, requestedLimit: 1, assets: [row]), consent: consent)
    }
}
private actor MemoryIngestion: ImportServicing {
    var began: String?
    var batch: Data?
    var appendCalls = 0
    var committed = 0
    var lostResponse = true
    var offline = false
    var permissions: [String] = []
    var authentications = 0
    func authenticationCount() -> Int { authentications }
    var delayPermission = false
    func delay() { delayPermission = true }
    func setOffline(_ value: Bool) { offline = value }
    func counts() -> (Int, Int, [String]) { (appendCalls, committed, permissions) }
    func authenticate(_ identity: PairingIdentity) async throws { authentications += 1 }
    func permission(_ identity: PairingIdentity, value: String) async throws {
        if offline { throw PairingFailure.unavailable }
        if delayPermission { try await Task.sleep(for: .milliseconds(50)) }
        permissions.append(value)
    }
    func begin(_ identity: PairingIdentity, checkpoint: ImportCheckpoint) async throws -> ImportBegin {
        if let began { assert(began == checkpoint.jobID) } else { began = checkpoint.jobID }
        return ImportBegin(run_id: "synthetic-run", next_sequence: committed > 0 ? 1 : 0, state: "active", coverage: "bounded_authorized_sample")
    }
    func append(_ identity: PairingIdentity, checkpoint: ImportCheckpoint, runID: String) async throws -> ImportReceipt {
        appendCalls += 1
        let bytes = try NativeJSON.encode(ImportTransport.Append(device_id: checkpoint.deviceID, run_id: runID, batch_key: checkpoint.batchKey, sequence: 0,
            checkpoint: "bounded-sample:" + checkpoint.jobID, assets: checkpoint.selection.assets))
        if let batch { assert(batch == bytes, "Replay must keep identical keys, wrapper revisions and bytes") }
        else { batch = bytes; committed += 1 }
        if lostResponse { lostResponse = false; throw PairingFailure.unavailable }
        return ImportReceipt(run_id: runID, sequence: 0, next_sequence: 1, accepted: 1, excluded: 0, assets: [.init(native_id: "synthetic-selected", asset_id: "synthetic-asset")])
    }
    func finish(_ identity: PairingIdentity, runID: String) async throws -> ImportFinish {
        ImportFinish(run_id: runID, state: "complete", coverage: "bounded_authorized_sample", media_ready: 0)
    }
}

@main struct ImportWorkflowTests {
    @MainActor static func main() async throws {
        let store = MemoryCheckpoints(), identity = MemoryIdentity(), reader = MemoryReader(), server = MemoryIngestion()
        let consent = ImportConsent(includeHidden: false, includeSharedLibrary: true, includeSharedAlbums: true)
        let worker = ImportCoordinator(store: store, identities: identity, reader: reader, service: server)
        do { _ = try await worker.start(ids: [], consent: consent); fatalError("Empty selection admitted") } catch {}
        let invalidRequests = await server.authenticationCount()
        assert(invalidRequests == 0 && store.value == nil, "Invalid input must not contact server or alter the previous selection")
        do { _ = try await worker.start(ids: ["synthetic-selected"], consent: consent); fatalError("Lost response should interrupt") }
        catch PairingFailure.unavailable {}
        assert(store.value?.stage == .ready)
        let recovered = ImportCoordinator(store: store, identities: identity, reader: reader, service: server)
        let receipt = try await recovered.resume()
        let counts = await server.counts()
        assert(receipt.stage == .complete && receipt.accepted == 1 && counts.0 == 2 && counts.1 == 1 && counts.2 == ["limited"])
        print("PASS lost_append_response_replays_frozen_payload_without_duplicate")

        await server.setOffline(true)
        reader.authorization = "denied"
        do { try await recovered.inspectChanges(); fatalError("Offline revocation must remain pending") } catch {}
        assert(store.value?.stage == .revocationPending)
        do { _ = try await recovered.resume(); fatalError("Pending revocation must block upload") } catch {}
        let deniedCounts = await server.counts()
        assert(deniedCounts.0 == counts.0)
        await server.setOffline(false)
        try await recovered.flushRevocation()
        assert(store.value?.stage == .revoked)
        let revokedCounts = await server.counts()
        assert(revokedCounts.2.last == "denied")
        print("PASS permission_denial_persists_revocation_and_blocks_resume_offline")

        // Same selected IDs but changed metadata must invalidate the old wrapper.
        reader.authorization = "limited"
        var restored = receipt; restored.stage = .complete; try store.save(restored)
        reader.changed = true
        do { try await recovered.inspectChanges(); fatalError("Changed metadata must invalidate") } catch {}
        assert(store.value?.stage == .revoked)
        let final = await server.counts()
        assert(final.0 == counts.0 && final.2.last == "limited")
        print("PASS same_ids_changed_metadata_revokes_old_selection")

        restored.stage = .complete; try store.save(restored)
        reader.changed = false; reader.available = false
        do { try await recovered.inspectChanges(); fatalError("Limited selection removal must invalidate") } catch {}
        assert(store.value?.stage == .revoked)
        print("PASS unavailable_selected_id_revokes_without_enumeration")
        restored.stage = .complete; try store.save(restored)
        reader.available = true
        await server.delay()
        let beforeConcurrent = await server.counts()
        async let first: Void = recovered.invalidate()
        async let second: Void = recovered.invalidate()
        _ = try await (first, second)
        let afterConcurrent = await server.counts()
        assert(afterConcurrent.2.count == beforeConcurrent.2.count + 1, "Concurrent invalidations must share one in-flight revocation")
        print("PASS_concurrent_revocations_cannot_leave_a_late_request")
    }
}
