import Foundation
import CryptoKit

/// A committed page grants media eligibility only, never full-scan completion.
@MainActor final class ScanPageCopies: ScanCopying {
    private weak var coordinator: ScanCoordinator?
    private let exporter: any MediaExporting
    private let files: any MediaFileReading
    private let service: any MediaServicing
    init(coordinator: ScanCoordinator, exporter: any MediaExporting, files: any MediaFileReading, service: any MediaServicing) {
        self.coordinator = coordinator; self.exporter = exporter; self.files = files; self.service = service
    }
    func copy(sequence: Int) async throws -> String {
        guard let coordinator else { throw ScanFailure.snapshotUnavailable }
        let adapter = ScanPageSelection(coordinator: coordinator, sequence: sequence)
        let sample = try await adapter.mediaSelection(), state = try await coordinator.verified()
        guard state.copy else { throw ImportFailure.consentRequired }
        let worker = MediaCoordinator(selection: adapter, exporter: exporter, files: files, service: service)
        let job = try await (sample.media == nil ? worker.start(allowICloud: state.cloud) : worker.resume())
        return job.readyCount(sample) == sample.accepted ? "ready" : "partial"
    }
}

@MainActor private final class ScanPageSelection: MediaSelectionSource {
    private let coordinator: ScanCoordinator
    private let sequence: Int
    private var cached: ImportCheckpoint?
    init(coordinator: ScanCoordinator, sequence: Int) { self.coordinator = coordinator; self.sequence = sequence }
    func mediaSelection() async throws -> ImportCheckpoint {
        let state = try await coordinator.verified()
        guard state.snapshot != nil, let record = try coordinator.store.page(scanID: state.id, sequence: sequence),
              sequence < state.nextSequence else { throw ScanFailure.invalidReceipt }
        let rows = try await coordinator.readPage(state, start: record.start, count: record.count)
        let digest = SHA256.hash(data: try NativeJSON.encode(rows)).map { String(format: "%02x", $0) }.joined()
        guard digest == record.payloadDigest, record.accepted.allSatisfy({ mapping in
            rows.contains { $0.nativeID == mapping.nativeID && $0.sourceRevision == mapping.sourceRevision }
        }) else { try await coordinator.invalidate(); throw ScanFailure.snapshotChanged }
        let selection = try ImportSelection(ids: rows.map(\.nativeID), manifest: ProbeManifest(probeInstallationID: "authorized-scan-page", authorization: state.permission,
            requestedLimit: rows.count, assets: rows.map(\.metadata)), consent: state.consent)
        let current = try await coordinator.verified()
        guard current.id == state.id else { throw ScanFailure.snapshotChanged }
        let sample = ImportCheckpoint(jobID: record.id, deviceID: state.deviceID, libraryID: state.libraryID, fingerprint: state.fingerprint,
            batchKey: record.id, selection: selection, stage: .complete, revokePermission: state.permission, runID: state.runID,
            accepted: record.accepted.count, excluded: record.count - record.accepted.count,
            acceptedAssets: record.accepted.map { .init(native_id: $0.nativeID, asset_id: $0.assetID) }, media: record.media)
        cached = sample; return sample
    }
    func mediaIdentity(_ checkpoint: ImportCheckpoint) throws -> PairingIdentity {
        guard let state = try coordinator.store.load(), checkpoint.jobID == cached?.jobID,
              state.deviceID == checkpoint.deviceID, state.libraryID == checkpoint.libraryID, state.fingerprint == checkpoint.fingerprint else { throw PairingFailure.relinkRequired }
        return try coordinator.identity(state)
    }
    func saveMedia(_ media: MediaJob, jobID: String) throws {
        guard let state = try coordinator.store.load(), [.indexing, .complete].contains(state.stage),
              var record = try coordinator.store.page(scanID: state.id, sequence: sequence), record.id == jobID,
              let cached, cached.jobID == jobID else { throw ScanFailure.snapshotChanged }
        try media.validate(cached); record.media = media; try coordinator.store.savePage(record, scanID: state.id)
    }
}
