import Foundation

@main struct ScanJournalTests {
    @MainActor static func main() throws {
        let temporary = FileManager.default.temporaryDirectory.appendingPathComponent("memory-scan-fixture-" + UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: temporary) }
        let root = temporary.appendingPathComponent("private/journal")
        let journal = try ScanJournal(directory: root)
        let row = try ImportAsset(ProbeAsset(localIdentifier: "selected", creationInstant: "2026-09-01T00:00:00.000Z", modificationInstant: nil, addedInstant: nil, mediaType: 1, mediaSubtypes: 0,
            pixelWidth: 1, pixelHeight: 1, duration: 0, isHidden: false, isFavorite: false, sourceType: 1, location: nil, burstIdentifier: nil,
            burstSelectionTypes: 0, representsBurst: false, hasAdjustments: false, adjustmentFormatIdentifier: nil, resources: [], unavailable: [:]))
        var state = ScanState(id: UUID().uuidString, deviceID: "device", libraryID: "library", fingerprint: String(repeating: "a", count: 64), permission: "limited",
            consent: ImportConsent(includeHidden: false, includeSharedLibrary: true, includeSharedAlbums: true), copy: false, cloud: false, revokePermission: "limited")
        state.snapshot = ScanSnapshot(permission: "limited", expectedCount: 1, orderedIDHash: String(repeating: "b", count: 64), changeToken: Data("opaque synthetic token".utf8))
        state.stage = .indexing; state.runID = "run"; state.recentAfter = "2026-07-01T00:00:00+00:00"
        state.pending = try ScanPage.make([row], state: state)
        try journal.save(state)
        let reopened = try ScanJournal(directory: root), restored = try reopened.load()!
        let before = try NativeJSON.encode(state), after = try NativeJSON.encode(restored)
        assert(before == after)
        let pending = state.pending!
        let receipt = ScanReceipt(run_id: "run", sequence: 0, next_sequence: 1, accepted: 1, excluded: 0,
            assets: [.init(native_id: "selected", asset_id: "asset")], observed: 1, expected_count: 1, phase: "recent")
        try reopened.savePage(ScanPageRecord(page: pending, receipt: receipt), scanID: state.id)
        state.pending = nil; state.observed = 1; state.accepted = 1; state.nextSequence = 1; state.stage = .complete
        try reopened.save(state)
        let compact = try Data(contentsOf: root.appendingPathComponent(state.id).appendingPathComponent("page-0.json"))
        let compactText = String(decoding: compact, as: UTF8.self)
        assert(!compactText.contains("\"metadata\"") && !compactText.contains("\"credential\"") && compactText.contains(row.sourceRevision))
        assert(tryLoad(reopened)?.pending == nil)
        print("PASS_scan_journal_restarts_and_compacts_confirmed_pages_without_raw_library")

        let statePath = root.appendingPathComponent(state.id).appendingPathComponent("state.json")
        let mode = try FileManager.default.attributesOfItem(atPath: statePath.path)[.posixPermissions] as! NSNumber
        assert(mode.intValue == 0o600)
        let unchanged = try Data(contentsOf: statePath)
        do { _ = try ScanJournal(directory: root, budget: 10); fatalError("Budget overflow accepted") } catch ScanFailure.capacity {}
        let still = try Data(contentsOf: statePath); assert(unchanged == still)
        print("PASS_scan_budget_failure_preserves_retained_private_state")

        let pointer = root.appendingPathComponent("current.json")
        try FileManager.default.removeItem(at: pointer)
        let sentinel = temporary.appendingPathComponent("outside")
        let sentinelBytes = Data("synthetic sentinel".utf8); try sentinelBytes.write(to: sentinel)
        try FileManager.default.createSymbolicLink(at: pointer, withDestinationURL: sentinel)
        do { _ = try reopened.load(); fatalError("Journal followed pointer symlink") } catch {}
        do { try reopened.save(state); fatalError("Journal replaced pointer symlink") } catch {}
        let final = try Data(contentsOf: sentinel); assert(final == sentinelBytes)
        print("PASS_scan_journal_symlink_refused_without_touching_target")
    }
    @MainActor static func tryLoad(_ store: ScanJournal) -> ScanState? { try! store.load() }
}
