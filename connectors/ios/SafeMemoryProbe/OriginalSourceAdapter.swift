import Foundation

/// Existing accepted metadata is authority for device-local scope, never a
/// filename heuristic or the unverified contents of a pending HTTP request.
@MainActor final class OriginalSourceAdapter: OriginalSource {
    private let sample: ImportCoordinator
    private let scan: ScanCoordinator
    private let identities: any PairingIdentityStore
    private var pageCache: (scan: String, request: String, sequence: Int)?
    init(sample: ImportCoordinator, scan: ScanCoordinator, identities: any PairingIdentityStore) {
        self.sample = sample; self.scan = scan; self.identities = identities
    }
    func identity() throws -> PairingIdentity {
        guard let identity = try identities.load(), identity.claimID != nil else { throw PairingFailure.unauthorized }
        try identity.validate(); return identity
    }
    func revoke() async throws {
        // Each coordinator persists its own pending security operation first.
        // Failure keeps the original job quarantined until all scopes clear.
        try await sample.invalidate(); try await scan.invalidate()
    }
    func scope(_ request: OriginalRequest) async throws -> OriginalScope {
        try request.validate()
        if let state = try scan.store.load(), [.indexing, .complete, .revocationPending].contains(state.stage) {
            let verified = try await scan.verified()
            var record: ScanPageRecord?
            if let cached = pageCache, cached.scan == state.id, cached.request == request.request_id {
                record = try scan.store.page(scanID: state.id, sequence: cached.sequence)
            } else {
                for sequence in 0..<verified.nextSequence {
                    try Task.checkCancellation()
                    if let candidate = try scan.store.page(scanID: state.id, sequence: sequence), candidate.accepted.contains(where: { $0.nativeID == request.native_id && $0.assetID == request.asset_id }) {
                        record = candidate; pageCache = (state.id, request.request_id, sequence); break
                    }
                }
            }
            guard let record, record.sequence < verified.nextSequence,
                  record.accepted.contains(where: { $0.nativeID == request.native_id && $0.assetID == request.asset_id && $0.sourceRevision == request.source_revision }) else { throw OriginalFailure.restricted }
            let rows = try await scan.readPage(verified, start: record.start, count: record.count)
            guard let row = rows.first(where: { $0.nativeID == request.native_id }), row.sourceRevision == request.source_revision,
                  row.mediaType == request.media_type else { throw OriginalFailure.revision_changed }
            let current = try await scan.verified()
            guard current.id == state.id else { throw OriginalFailure.restricted }
            return OriginalScope(deviceID: verified.deviceID, libraryID: verified.libraryID, fingerprint: verified.fingerprint,
                scopeID: verified.id, permission: verified.permission, consent: verified.consent, asset: row)
        }
        let checkpoint = try await sample.mediaSelection()
        guard checkpoint.acceptedAssets?.contains(where: { $0.native_id == request.native_id && $0.asset_id == request.asset_id }) == true,
              let row = checkpoint.selection.assets.first(where: { $0.nativeID == request.native_id }), row.sourceRevision == request.source_revision,
              row.mediaType == request.media_type else { throw OriginalFailure.restricted }
        _ = try sample.mediaIdentity(checkpoint)
        return OriginalScope(deviceID: checkpoint.deviceID, libraryID: checkpoint.libraryID, fingerprint: checkpoint.fingerprint,
            scopeID: checkpoint.jobID, permission: checkpoint.selection.permission, consent: checkpoint.selection.consent, asset: row)
    }
}
