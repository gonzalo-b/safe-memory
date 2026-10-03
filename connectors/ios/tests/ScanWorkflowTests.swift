import Foundation
import CryptoKit

@MainActor private final class Journal: ScanStoring {
    var state: ScanState?
    var pages: [Int: ScanPageRecord] = [:]
    func load() throws -> ScanState? { state }
    func save(_ value: ScanState) throws { state = value }
    func page(scanID: String, sequence: Int) throws -> ScanPageRecord? { pages[sequence] }
    func savePage(_ value: ScanPageRecord, scanID: String) throws { pages[value.sequence] = value }
}
@MainActor private final class Identity: PairingIdentityStore {
    let value = PairingIdentity(installationID: "installation", libraryID: "library", deviceName: "Synthetic", credential: String(repeating: "A", count: 43), claimID: "device", expiresAt: 999999)
    func load() throws -> PairingIdentity? { value }
    func create(deviceName: String) throws -> PairingIdentity { fatalError("No identity rotation") }
    func saveClaim(_ identity: PairingIdentity) throws { fatalError("No pairing writes") }
}
private actor Reader: ScanReading {
    var changed = false
    var permissionValue = "limited"
    var assets: [ImportAsset]
    init(empty: Bool = false) throws {
        assets = try (empty ? [] : ["2026-09-01T00:00:00.000Z", "2026-06-01T00:00:00.000Z", nil]).enumerated().map { index, instant in
            try ImportAsset(ProbeAsset(localIdentifier: "synthetic-\(index)", creationInstant: instant, modificationInstant: nil, addedInstant: nil, mediaType: 1, mediaSubtypes: 0,
                pixelWidth: 1, pixelHeight: 1, duration: 0, isHidden: false, isFavorite: false, sourceType: 1, location: nil, burstIdentifier: nil,
                burstSelectionTypes: 0, representsBurst: false, hasAdjustments: false, adjustmentFormatIdentifier: nil, resources: [], unavailable: [:]))
        }
    }
    func deny() { changed = true; permissionValue = "denied" }
    func alterFirstMetadata() throws {
        let first = assets[0]
        assets[0] = try ImportAsset(ProbeAsset(localIdentifier: first.nativeID, creationInstant: first.captureTime, modificationInstant: nil, addedInstant: nil, mediaType: 1, mediaSubtypes: 0,
            pixelWidth: 1, pixelHeight: 1, duration: 0, isHidden: false, isFavorite: true, sourceType: 1, location: nil, burstIdentifier: nil,
            burstSelectionTypes: 0, representsBurst: false, hasAdjustments: false, adjustmentFormatIdentifier: nil, resources: [], unavailable: [:]))
    }
    func permission() async -> String { permissionValue }
    func freeze(consent: ImportConsent) async throws -> ScanSnapshot {
        ScanSnapshot(permission: permissionValue, expectedCount: assets.count, orderedIDHash: String(repeating: "a", count: 64), changeToken: Data("fixture-token".utf8))
    }
    func verify(_ snapshot: ScanSnapshot, consent: ImportConsent, full: Bool) async throws { if changed { throw ScanFailure.snapshotChanged } }
    func page(_ snapshot: ScanSnapshot, start: Int, count: Int, consent: ImportConsent) async throws -> [ImportAsset] {
        if changed { throw ScanFailure.snapshotChanged }
        return Array(assets[start..<min(assets.count, start + count)])
    }
}
private actor Server: ScanServicing {
    var keys = Set<String>()
    var receipts: [Int: ScanReceipt] = [:]
    var payloads: [Int: Data] = [:]
    var lost = true
    var offline = false
    var appendCalls = 0
    var permissions = 0
    func setOffline(_ value: Bool) { offline = value }
    func stats() -> (Int, Int, Int) { (appendCalls, keys.count, permissions) }
    func permission(_ local: PairingIdentity, value: String) async throws {
        if offline { throw PairingFailure.unavailable }; permissions += 1
    }
    func begin(_ local: PairingIdentity, state: ScanState) async throws -> ScanBegin {
        keys.insert(state.id)
        let observed = receipts.values.map(\.accepted).reduce(0,+)
        return ScanBegin(run_id: "scan", next_sequence: receipts.count, state: "active", coverage: "authorized_limited_scan", recent_after: "2026-07-01T00:00:00+00:00",
            observed: observed, expected_count: state.snapshot!.expectedCount, checkpoint: nil)
    }
    func append(_ local: PairingIdentity, state: ScanState, page: ScanPage) async throws -> ScanReceipt {
        appendCalls += 1
        let bytes = try NativeJSON.encode(page)
        if let old = payloads[page.sequence] { assert(old == bytes, "Replay changed frozen page/key/phase") }
        else { payloads[page.sequence] = bytes }
        let receipt = ScanReceipt(run_id: "scan", sequence: page.sequence, next_sequence: page.sequence + 1, accepted: page.assets.count, excluded: 0,
            assets: page.assets.map { .init(native_id: $0.nativeID, asset_id: "asset-" + $0.nativeID) }, observed: page.start + page.assets.count,
            expected_count: state.snapshot!.expectedCount, phase: page.phase)
        receipts[page.sequence] = receipt
        if lost { lost = false; throw PairingFailure.unavailable }
        return receipt
    }
    func finish(_ local: PairingIdentity, state: ScanState) async throws -> ScanFinish {
        ScanFinish(run_id: "scan", state: "complete", coverage: "authorized_limited_scan", observed: state.observed,
            expected_count: state.snapshot!.expectedCount, media_ready: 99)
    }
}
@MainActor private final class Copies: ScanCopying {
    var calls = 0
    func copy(sequence: Int) async throws -> String { calls += 1; if calls == 1 { throw PairingFailure.capacity }; return "ready" }
}
@MainActor private struct Exported: MediaExporting, MediaFileReading {
    let bytes = Data("synthetic optimized component".utf8)
    var hash: String { SHA256.hash(data: bytes).map { String(format: "%02x", $0) }.joined() }
    func export(_ sample: ImportCheckpoint, allowICloud: Bool) async throws -> ExportBatchResult {
        ExportBatchResult(jobID: UUID().uuidString, assets: sample.acceptedAssets!.map {
            ExportAssetResult(localIdentifier: $0.native_id, state: "ready", components: [ExportComponent(role: .photo, filename: UUID().uuidString + ".jpg",
                byteCount: Int64(bytes.count), sha256: hash, contentType: "image/jpeg", pixelWidth: 1, pixelHeight: 1, duration: nil, hasAudio: false)], reason: nil)
        })
    }
    func validate(_ upload: MediaUpload) throws { assert(upload.sha256 == hash && upload.size == bytes.count) }
    func read(_ upload: MediaUpload, offset: Int, count: Int) throws -> Data { bytes.subdata(in: offset..<offset + count) }
}
private actor MediaServer: MediaServicing {
    let isIndexing: @MainActor @Sendable () -> Bool
    var completed = 0
    init(isIndexing: @escaping @MainActor @Sendable () -> Bool) { self.isIndexing = isIndexing }
    func count() -> Int { completed }
    func begin(_ local: PairingIdentity, upload: MediaUpload) async throws -> MediaBegin {
        let indexing = await isIndexing(); assert(indexing, "Page eligibility must not mark the global scan complete")
        return MediaBegin(upload_id: upload.requestKey, next_offset: 0, state: "active")
    }
    func chunk(_ local: PairingIdentity, uploadID: String, offset: Int, data: Data) async throws -> MediaChunk { MediaChunk(upload_id: uploadID, next_offset: offset + data.count) }
    func complete(_ local: PairingIdentity, upload: MediaUpload) async throws -> MediaComplete {
        completed += 1; return MediaComplete(component_id: "component-" + upload.requestKey, state: "ready", size: upload.size, mime: upload.mime)
    }
}

@main struct ScanWorkflowTests {
    @MainActor static func main() async throws {
        let consent = ImportConsent(includeHidden: false, includeSharedLibrary: true, includeSharedAlbums: true)
        let journal = Journal(), identity = Identity(), reader = try Reader(), server = Server(), copies = Copies()
        let first = ScanCoordinator(store: journal, identities: identity, reader: reader, service: server)
        first.copier = copies
        do { _ = try await first.start(consent: consent, copy: true, cloud: false); fatalError("Lost receipt must interrupt") } catch PairingFailure.unavailable {}
        assert(journal.state?.pending?.sequence == 0 && journal.state?.observed == 0)
        journal.state = try JSONDecoder().decode(ScanState.self, from: NativeJSON.encode(journal.state!))
        let restarted = ScanCoordinator(store: journal, identities: identity, reader: reader, service: server)
        restarted.copier = copies
        let finished = try await restarted.resume()
        let stats = await server.stats()
        assert(finished.stage == .complete && finished.observed == 3 && finished.nextSequence == 2)
        assert(stats.0 == 3 && stats.1 == 1 && stats.2 == 1)
        assert(journal.pages[0]?.phase == "recent" && journal.pages[1]?.phase == "backfill")
        print("PASS_progressive_restart_replays_page_once_and_keeps_recent_backfill_order")
        assert(copies.calls == 2 && journal.pages[0]?.copyOutcome == "capacity" && journal.pages[1]?.copyOutcome == "ready")
        print("PASS_metadata_finishes_despite_media_capacity_and_preserves_deferred_receipt")

        await server.setOffline(true); await reader.deny()
        do { try await restarted.inspectChanges(); fatalError("Changed snapshot must revoke") } catch {}
        assert(journal.state?.stage == .revocationPending)
        do { _ = try await restarted.resume(); fatalError("Pending restriction resumed") } catch {}
        await server.setOffline(false); try await restarted.flushRevocation()
        assert(journal.state?.stage == .revoked)
        let after = await server.stats(); assert(after.0 == stats.0)
        print("PASS_snapshot_or_permission_change_persists_restriction_and_blocks_replay")

        let emptyJournal = Journal(), emptyReader = try Reader(empty: true), emptyServer = Server()
        let empty = try await ScanCoordinator(store: emptyJournal, identities: identity, reader: emptyReader, service: emptyServer).start(consent: consent, copy: false, cloud: false)
        let emptyStats = await emptyServer.stats()
        assert(empty.stage == .complete && empty.observed == 0 && empty.snapshot?.expectedCount == 0 && emptyStats.0 == 0)
        print("PASS_empty_authorized_scan_finishes_without_fake_percentage_or_batch")

        let copiedJournal = Journal(), copiedReader = try Reader(), copiedServer = Server(), exported = Exported()
        let copied = ScanCoordinator(store: copiedJournal, identities: identity, reader: copiedReader, service: copiedServer)
        let media = MediaServer { copiedJournal.state?.stage == .indexing }
        let adapter = ScanPageCopies(coordinator: copied, exporter: exported, files: exported, service: media)
        copied.copier = adapter
        do { _ = try await copied.start(consent: consent, copy: true, cloud: false) } catch PairingFailure.unavailable {}
        let indexed = try await copied.resume(), count = await media.count()
        assert(indexed.stage == .complete && count == 3 && copiedJournal.pages.values.allSatisfy { $0.copyOutcome == "ready" && $0.media != nil })
        print("PASS_confirmed_page_adapter_reuses_uploader_without_faking_index_completion")
        try await copiedReader.alterFirstMetadata()
        do { _ = try await adapter.copy(sequence: 0); fatalError("Changed page wrapper reused for media") } catch {}
        let unchangedCopies = await media.count()
        assert(copiedJournal.state?.stage == .revoked && unchangedCopies == 3)
        print("PASS_compact_receipt_digest_refuses_changed_page_before_media_retry")

        var unorderedState = finished
        unorderedState.phase = "backfill"
        let originalRows = await reader.assets
        do { _ = try ScanPage.make([originalRows[2], originalRows[1]], state: unorderedState); fatalError("Known date after unknown date admitted") }
        catch ScanFailure.snapshotChanged {}
        unorderedState.unknownStarted = false; unorderedState.lastInstant = nil
        do { _ = try ScanPage.make([originalRows[1], originalRows[0]], state: unorderedState); fatalError("Backfill returned to recent") }
        catch ScanFailure.snapshotChanged {}
        print("PASS_descending_capture_order_and_unknown_last_are_checked_before_send")
    }
}
