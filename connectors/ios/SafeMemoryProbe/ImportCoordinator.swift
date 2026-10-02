import Foundation

@MainActor
final class ImportCoordinator: MediaSelectionSource {
    let store: any ImportCheckpointStore
    private let identities: any PairingIdentityStore
    private let reader: any ImportReading
    private let service: any ImportServicing
    private var running = false
    private var revocationTask: Task<Void, Error>?
    init(store: any ImportCheckpointStore, identities: any PairingIdentityStore, reader: any ImportReading, service: any ImportServicing) {
        self.store = store; self.identities = identities; self.reader = reader; self.service = service
    }
    private func identity(for checkpoint: ImportCheckpoint? = nil) throws -> PairingIdentity {
        guard let local = try identities.load(), let device = local.claimID else { throw PairingFailure.unauthorized }
        try local.validate()
        if let checkpoint {
            guard checkpoint.deviceID == device, checkpoint.libraryID == local.libraryID, checkpoint.fingerprint == local.fingerprint else { throw PairingFailure.relinkRequired }
        }
        return local
    }
    private func current(_ original: ImportCheckpoint) throws -> ImportCheckpoint {
        guard let saved = try store.load(), saved.jobID == original.jobID,
              saved.stage != .revocationPending && saved.stage != .revoked else { throw ImportFailure.selectionChanged }
        return saved
    }
    private func verify(_ checkpoint: ImportCheckpoint) async throws {
        _ = try current(checkpoint)
        do {
            guard reader.permission() == checkpoint.selection.permission else { throw ImportFailure.selectionChanged }
            let now = try await reader.selection(ids: checkpoint.selection.ids, consent: checkpoint.selection.consent)
            guard checkpoint.selection.matches(now) else { throw ImportFailure.selectionChanged }
        } catch is CancellationError { throw CancellationError() }
        catch {
            try await invalidate()
            throw ImportFailure.selectionChanged
        }
        _ = try current(checkpoint)
        try Task.checkCancellation()
    }
    func start(ids: [String], consent: ImportConsent) async throws -> ImportCheckpoint {
        guard !running else { throw ImportFailure.busy }
        guard (1...100).contains(ids.count), Set(ids).count == ids.count,
              ids.allSatisfy({ PairingRequests.text($0, maximum: 256) }) else { throw ImportFailure.invalidSelection }
        guard consent.includeSharedLibrary && consent.includeSharedAlbums else { throw ImportFailure.consentRequired }
        running = true
        defer { running = false }
        // A previous selection is cleared before reading or submitting a new one.
        if let old = try store.load(), old.stage != .revoked { try await invalidate() }
        let local = try identity()
        try await service.authenticate(local)
        let selection = try await reader.selection(ids: ids, consent: consent)
        try Task.checkCancellation()
        let checkpoint = ImportCheckpoint(jobID: UUID().uuidString, deviceID: local.claimID!, libraryID: local.libraryID,
            fingerprint: local.fingerprint, batchKey: UUID().uuidString, selection: selection, revokePermission: selection.permission)
        try store.save(checkpoint) // frozen payload and idempotency keys before the first ingest request
        running = false
        return try await resume()
    }
    func resume() async throws -> ImportCheckpoint {
        guard !running else { throw ImportFailure.busy }
        running = true; defer { running = false }
        guard var checkpoint = try store.load() else { throw ImportFailure.invalidSelection }
        if checkpoint.stage == .revocationPending { try await flushRevocation(); throw ImportFailure.selectionChanged }
        guard checkpoint.stage != .revoked else { throw ImportFailure.selectionChanged }
        let local = try identity(for: checkpoint)
        try await service.authenticate(local)
        try await verify(checkpoint)
        if checkpoint.stage == .clearOldScope {
            try await service.permission(local, value: checkpoint.selection.permission)
            checkpoint = try current(checkpoint); checkpoint.stage = .ready; try store.save(checkpoint)
        }
        try await verify(checkpoint)
        let begin = try await service.begin(local, checkpoint: checkpoint)
        guard PairingRequests.identifier(begin.run_id), [0, 1].contains(begin.next_sequence), ["active", "complete"].contains(begin.state), begin.coverage == "bounded_authorized_sample",
              checkpoint.runID == nil || checkpoint.runID == begin.run_id else { throw ImportFailure.invalidReceipt }
        checkpoint = try current(checkpoint); checkpoint.runID = begin.run_id; try store.save(checkpoint)
        try await verify(checkpoint)
        // Always replay the exact sequence-zero batch. A begin cursor alone does
        // not reveal accepted/excluded counts after a lost response.
        let receipt = try await service.append(local, checkpoint: checkpoint, runID: begin.run_id)
        let returned = receipt.assets.map(\.native_id)
        guard receipt.run_id == begin.run_id, receipt.sequence == 0, receipt.next_sequence == 1,
              (0...checkpoint.selection.assets.count).contains(receipt.accepted), (0...checkpoint.selection.assets.count).contains(receipt.excluded),
              receipt.accepted + receipt.excluded == checkpoint.selection.assets.count,
              receipt.assets.count == receipt.accepted, Set(returned).count == returned.count,
              Set(receipt.assets.map(\.asset_id)).count == receipt.assets.count,
              Set(returned).isSubset(of: Set(checkpoint.selection.ids)), receipt.assets.allSatisfy({ PairingRequests.identifier($0.asset_id) }) else { throw ImportFailure.invalidReceipt }
        checkpoint = try current(checkpoint); checkpoint.accepted = receipt.accepted; checkpoint.excluded = receipt.excluded
        checkpoint.acceptedAssets = receipt.assets; try store.save(checkpoint)
        try await verify(checkpoint)
        let finish = try await service.finish(local, runID: begin.run_id)
        // The server reports Source-wide current readiness, including prior
        // optimized uploads. Int decoding bounds the value; it is not limited
        // to this selected sample and a completed run may be replayed later.
        guard finish.run_id == begin.run_id, finish.state == "complete", finish.coverage == "bounded_authorized_sample", finish.media_ready >= 0 else { throw ImportFailure.invalidReceipt }
        try await verify(checkpoint)
        checkpoint = try current(checkpoint); checkpoint.stage = .complete; try store.save(checkpoint)
        return checkpoint
    }
    // Security-only revocation may run while an import is suspended in a request.
    // Pending state is durable first; late responses cannot overwrite it.
    func invalidate() async throws {
        guard var checkpoint = try store.load(), checkpoint.stage != .revoked else { return }
        let permission = reader.permission()
        checkpoint.revokePermission = ["full", "limited", "denied"].contains(permission) ? permission : "revoked"
        checkpoint.stage = .revocationPending; try store.save(checkpoint)
        try await flushRevocation()
    }
    func flushRevocation() async throws {
        if let revocationTask { try await revocationTask.value; return }
        let work = Task { @MainActor in
            defer { self.revocationTask = nil }
            while var checkpoint = try self.store.load(), checkpoint.stage == .revocationPending {
                let local = try self.identity(for: checkpoint)
                try await self.service.permission(local, value: checkpoint.revokePermission)
                guard let saved = try self.store.load(), saved.jobID == checkpoint.jobID, saved.stage == .revocationPending else { throw ImportFailure.selectionChanged }
                // A second callback may have tightened permission while this
                // request was in flight. Acknowledge the latest value first.
                if saved.revokePermission != checkpoint.revokePermission { continue }
                checkpoint = saved; checkpoint.stage = .revoked; try self.store.save(checkpoint)
            }
        }
        revocationTask = work
        try await work.value
    }
    func inspectChanges() async throws {
        guard let checkpoint = try store.load(), checkpoint.stage != .revoked else { return }
        if checkpoint.stage == .revocationPending { try await flushRevocation(); return }
        try await verify(checkpoint)
    }
    func mediaSelection() async throws -> ImportCheckpoint {
        guard var checkpoint = try store.load(), checkpoint.stage == .complete else { throw ImportFailure.selectionChanged }
        try await verify(checkpoint)
        if checkpoint.acceptedAssets == nil {
            guard let run = checkpoint.runID else { throw ImportFailure.invalidReceipt }
            let local = try identity(for: checkpoint)
            let receipt = try await service.append(local, checkpoint: checkpoint, runID: run)
            guard receipt.run_id == run, receipt.sequence == 0, receipt.next_sequence == 1,
                  receipt.accepted == checkpoint.accepted, receipt.excluded == checkpoint.excluded,
                  receipt.assets.count == receipt.accepted, Set(receipt.assets.map(\.native_id)).count == receipt.assets.count,
                  Set(receipt.assets.map(\.asset_id)).count == receipt.assets.count,
                  Set(receipt.assets.map(\.native_id)).isSubset(of: Set(checkpoint.selection.ids)),
                  receipt.assets.allSatisfy({ PairingRequests.identifier($0.asset_id) }) else { throw ImportFailure.invalidReceipt }
            try await verify(checkpoint)
            checkpoint = try current(checkpoint); checkpoint.acceptedAssets = receipt.assets; try store.save(checkpoint)
        }
        return try current(checkpoint)
    }
    func mediaIdentity(_ checkpoint: ImportCheckpoint) throws -> PairingIdentity { try identity(for: checkpoint) }
    func saveMedia(_ media: MediaJob, jobID: String) throws {
        guard var checkpoint = try store.load(), checkpoint.jobID == jobID, checkpoint.stage == .complete else { throw ImportFailure.selectionChanged }
        try media.validate(checkpoint); checkpoint.media = media; try store.save(checkpoint)
    }
}
