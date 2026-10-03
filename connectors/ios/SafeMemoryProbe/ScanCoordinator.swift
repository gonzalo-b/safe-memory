import Foundation

@MainActor final class ScanCoordinator {
    let store: any ScanStoring
    let reader: any ScanReading
    private let identities: any PairingIdentityStore
    private let service: any ScanServicing
    var copier: (any ScanCopying)?
    var onProgress: (@MainActor () -> Void)?
    private var running = false
    private var revocation: Task<Void, Error>?
    init(store: any ScanStoring, identities: any PairingIdentityStore, reader: any ScanReading, service: any ScanServicing) {
        self.store = store; self.identities = identities; self.reader = reader; self.service = service
    }
    func identity(_ state: ScanState? = nil) throws -> PairingIdentity {
        guard let local = try identities.load(), let device = local.claimID else { throw PairingFailure.unauthorized }
        try local.validate()
        if let state { guard state.deviceID == device, state.libraryID == local.libraryID, state.fingerprint == local.fingerprint else { throw PairingFailure.relinkRequired } }
        return local
    }
    private func current(_ original: ScanState) throws -> ScanState {
        guard let state = try store.load(), state.id == original.id, ![.revocationPending, .revoked].contains(state.stage) else { throw ScanFailure.snapshotChanged }
        return state
    }
    func verified(full: Bool = false) async throws -> ScanState {
        guard let state = try store.load(), [.indexing, .complete].contains(state.stage), let snapshot = state.snapshot else { throw ScanFailure.snapshotUnavailable }
        _ = try identity(state)
        do {
            try Task.checkCancellation()
            try await reader.verify(snapshot, consent: state.consent, full: full)
        } catch is CancellationError { throw CancellationError() }
        catch { try await invalidate(); throw ScanFailure.snapshotChanged }
        try Task.checkCancellation(); return try current(state)
    }
    func readPage(_ state: ScanState, start: Int, count: Int) async throws -> [ImportAsset] {
        guard let snapshot = state.snapshot else { throw ScanFailure.snapshotUnavailable }
        do { return try await reader.page(snapshot, start: start, count: count, consent: state.consent) }
        catch ScanFailure.snapshotChanged { try await invalidate(); throw ScanFailure.snapshotChanged }
        catch ScanFailure.snapshotUnavailable { try await invalidate(); throw ScanFailure.snapshotChanged }
    }
    func start(consent: ImportConsent, copy: Bool, cloud: Bool) async throws -> ScanState {
        guard !running else { throw ImportFailure.busy }
        guard consent.includeSharedLibrary && consent.includeSharedAlbums, !cloud || copy else { throw ImportFailure.consentRequired }
        let local = try identity(), permission = await reader.permission()
        guard ["full", "limited"].contains(permission) else { throw ScanFailure.snapshotUnavailable }
        running = true; defer { running = false }
        if let old = try store.load(), old.stage != .revoked { try await invalidate() }
        var state = ScanState(id: UUID().uuidString, deviceID: local.claimID!, libraryID: local.libraryID, fingerprint: local.fingerprint,
            permission: permission, consent: consent, copy: copy, cloud: cloud, revokePermission: permission)
        try store.save(state)
        try await service.permission(local, value: permission)
        state = try current(state); state.stage = .freezing; try store.save(state)
        let snapshot = try await reader.freeze(consent: consent)
        try snapshot.validate(); try Task.checkCancellation()
        guard snapshot.permission == permission else { try await invalidate(); throw ScanFailure.snapshotChanged }
        state = try current(state); state.snapshot = snapshot; state.stage = .indexing; try store.save(state); onProgress?()
        running = false
        return try await resume()
    }
    private func begin(_ state: ScanState) async throws -> ScanState {
        let receipt = try await service.begin(identity(state), state: state)
        let pending = state.pending
        let sameCursor = receipt.next_sequence == state.nextSequence && receipt.observed == state.observed
        let replayCursor = pending.map { receipt.next_sequence == $0.sequence + 1 && receipt.observed == $0.start + $0.assets.count } ?? false
        guard PairingRequests.identifier(receipt.run_id), ["active", "complete"].contains(receipt.state), receipt.coverage == state.coverage,
              receipt.expected_count == state.snapshot?.expectedCount, sameCursor || replayCursor, ScanPage.date(receipt.recent_after) != nil,
              receipt.checkpoint == nil || receipt.checkpoint!.count <= 2000, state.runID == nil || state.runID == receipt.run_id,
              state.recentAfter == nil || state.recentAfter == receipt.recent_after else { throw ScanFailure.invalidReceipt }
        var saved = try current(state); saved.runID = receipt.run_id; saved.recentAfter = receipt.recent_after; try store.save(saved)
        return saved
    }
    private func accept(_ receipt: ScanReceipt, page: ScanPage, state: ScanState) throws -> ScanState {
        let count = page.assets.count, ids = receipt.assets.map(\.native_id)
        guard receipt.run_id == state.runID, receipt.sequence == page.sequence, receipt.next_sequence == page.sequence + 1,
              receipt.observed == page.start + count, receipt.expected_count == state.snapshot?.expectedCount, receipt.phase == page.phase,
              (0...count).contains(receipt.accepted), (0...count).contains(receipt.excluded), receipt.accepted + receipt.excluded == count,
              receipt.assets.count == receipt.accepted, Set(ids).count == ids.count, Set(ids).isSubset(of: Set(page.assets.map(\.nativeID))),
              Set(receipt.assets.map(\.asset_id)).count == ids.count, receipt.assets.allSatisfy({ PairingRequests.identifier($0.asset_id) }) else { throw ScanFailure.invalidReceipt }
        var record = try ScanPageRecord(page: page, receipt: receipt)
        if let old = try store.page(scanID: state.id, sequence: page.sequence) {
            guard old.id == record.id, old.payloadDigest == record.payloadDigest else { throw ScanFailure.invalidReceipt }
            record.media = old.media; record.copyOutcome = old.copyOutcome
        }
        try store.savePage(record, scanID: state.id)
        var saved = try current(state)
        saved.observed = receipt.observed; saved.nextSequence = receipt.next_sequence; saved.accepted += receipt.accepted; saved.excluded += receipt.excluded
        saved.phase = page.phase; saved.pending = nil; saved.copyPage = saved.copy && receipt.accepted > 0 ? page.sequence : nil
        for row in page.assets {
            if let instant = row.captureTime { saved.lastInstant = instant }
            else { saved.unknownStarted = true }
        }
        try store.save(saved); onProgress?()
        return saved
    }
    private func attemptCopy(_ original: ScanState) async throws -> ScanState {
        guard let sequence = original.copyPage else { return original }
        var outcome = "unavailable"
        do { if let copier { outcome = try await copier.copy(sequence: sequence) } }
        catch is CancellationError { throw CancellationError() }
        catch PairingFailure.cancelled { throw CancellationError() }
        catch PairingFailure.unauthorized { try await invalidate(); throw PairingFailure.unauthorized }
        catch PairingFailure.capacity { outcome = "capacity" }
        catch ExportFailure.limitExceeded { outcome = "capacity" }
        catch { outcome = "unavailable" }
        try Task.checkCancellation()
        var state = try current(original)
        if var record = try store.page(scanID: state.id, sequence: sequence) { record.copyOutcome = outcome; try store.savePage(record, scanID: state.id) }
        state.copyPage = nil; state.lastCopyOutcome = outcome; try store.save(state); onProgress?()
        return state
    }
    func resume() async throws -> ScanState {
        guard !running else { throw ImportFailure.busy }
        running = true; defer { running = false }
        if try store.load()?.stage == .revocationPending { try await flushRevocation(); throw ScanFailure.snapshotChanged }
        var state = try await verified(full: true)
        state = try await begin(state)
        state = try await attemptCopy(state)
        while state.observed < state.snapshot!.expectedCount {
            state = try await verified()
            // Renew the same run's lease after potentially long media work.
            state = try await begin(state)
            if state.pending == nil {
                guard state.nextSequence < 20_000 else { throw ScanFailure.capacity }
                let rows = try await readPage(state, start: state.observed, count: min(100, state.snapshot!.expectedCount - state.observed))
                let page: ScanPage
                do { page = try ScanPage.make(rows, state: state) }
                catch ScanFailure.snapshotChanged { try await invalidate(); throw ScanFailure.snapshotChanged }
                state = try await verified(); state.pending = page; try store.save(state)
            }
            let page = state.pending!
            let receipt = try await service.append(identity(state), state: state, page: page)
            state = try await verified()
            state = try accept(receipt, page: page, state: state)
            state = try await attemptCopy(state)
        }
        state = try await verified(full: true)
        let finish = try await service.finish(identity(state), state: state)
        guard finish.run_id == state.runID, finish.state == "complete", finish.coverage == state.coverage,
              finish.observed == state.observed, finish.expected_count == state.snapshot?.expectedCount,
              finish.observed == finish.expected_count, finish.media_ready >= 0 else { throw ScanFailure.invalidReceipt }
        state = try await verified(); state.stage = .complete; state.sourceMediaReady = finish.media_ready; try store.save(state); onProgress?()
        return state
    }
    func retryCopies() async throws -> ScanState {
        guard !running else { throw ImportFailure.busy }
        running = true; defer { running = false }
        var state = try await verified(full: true)
        guard state.copy else { throw ImportFailure.consentRequired }
        state = try await begin(state)
        for sequence in 0..<state.nextSequence {
            guard let record = try store.page(scanID: state.id, sequence: sequence), !record.accepted.isEmpty, record.copyOutcome != "ready" else { continue }
            state = try await verified(); state.copyPage = sequence; try store.save(state)
            state = try await attemptCopy(state)
        }
        return state
    }
    func invalidate() async throws {
        guard var state = try store.load(), state.stage != .revoked else { return }
        let permission = await reader.permission()
        state.revokePermission = ["full", "limited", "denied"].contains(permission) ? permission : "revoked"
        state.stage = .revocationPending; try store.save(state); onProgress?()
        try await flushRevocation()
    }
    func flushRevocation() async throws {
        if let revocation { try await revocation.value; return }
        let task = Task { @MainActor in
            defer { self.revocation = nil }
            while var state = try self.store.load(), state.stage == .revocationPending {
                try await self.service.permission(self.identity(state), value: state.revokePermission)
                guard let latest = try self.store.load(), latest.id == state.id, latest.stage == .revocationPending else { throw ScanFailure.snapshotChanged }
                if latest.revokePermission != state.revokePermission { continue }
                state = latest; state.stage = .revoked; try self.store.save(state)
            }
        }
        revocation = task; try await task.value
    }
    func inspectChanges() async throws {
        guard let state = try store.load(), state.stage != .revoked else { return }
        if state.stage == .revocationPending { try await flushRevocation(); return }
        if state.snapshot == nil { try await invalidate(); throw ScanFailure.snapshotChanged }
        _ = try await verified()
    }
}
