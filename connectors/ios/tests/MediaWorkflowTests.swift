import Foundation
import CryptoKit

@MainActor private final class Sample: MediaSelectionSource {
    var value: ImportCheckpoint
    var changed = false
    let local = PairingIdentity(installationID: "synthetic-install", libraryID: "library", deviceName: "Synthetic", credential: String(repeating: "A", count: 43), claimID: "device", expiresAt: 999999)
    init(live: Bool = false) throws {
        let row = ProbeAsset(localIdentifier: "selected", creationInstant: nil, modificationInstant: nil, addedInstant: nil, mediaType: 1, mediaSubtypes: live ? 8 : 0,
            pixelWidth: 1, pixelHeight: 1, duration: 0, isHidden: false, isFavorite: false, sourceType: 1, location: nil, burstIdentifier: nil,
            burstSelectionTypes: 0, representsBurst: false, hasAdjustments: false, adjustmentFormatIdentifier: nil, resources: [], unavailable: [:])
        let selection = try ImportSelection(ids: ["selected"], manifest: ProbeManifest(probeInstallationID: "synthetic", authorization: "limited", requestedLimit: 1, assets: [row]),
            consent: ImportConsent(includeHidden: false, includeSharedLibrary: true, includeSharedAlbums: true))
        value = ImportCheckpoint(jobID: UUID().uuidString, deviceID: "device", libraryID: "library", fingerprint: local.fingerprint,
            batchKey: UUID().uuidString, selection: selection, stage: .complete, revokePermission: "limited", accepted: 1, excluded: 0,
            acceptedAssets: [.init(native_id: "selected", asset_id: "asset")])
    }
    func mediaSelection() async throws -> ImportCheckpoint {
        if changed { value.stage = .revocationPending; throw ImportFailure.selectionChanged }
        guard value.stage == .complete else { throw ImportFailure.selectionChanged }; return value
    }
    func mediaIdentity(_ checkpoint: ImportCheckpoint) throws -> PairingIdentity { local }
    func saveMedia(_ media: MediaJob, jobID: String) throws {
        guard value.stage == .complete && value.jobID == jobID else { throw ImportFailure.selectionChanged }
        value.media = media
    }
}
@MainActor private final class Copies: MediaExporting, MediaFileReading {
    let bytes = Data(repeating: 0x61, count: 1024 * 1024 + 17)
    var exported = 0
    var changedDuringExport: (() -> Void)?
    var missingMotion = false
    func export(_ sample: ImportCheckpoint, allowICloud: Bool) async throws -> ExportBatchResult {
        exported += 1; changedDuringExport?()
        let live = sample.selection.assets[0].mediaType == "live"
        let still = ExportComponent(role: live ? .cover : .photo, filename: UUID().uuidString + ".jpg", byteCount: Int64(bytes.count), sha256: sha,
            contentType: "image/jpeg", pixelWidth: 1, pixelHeight: 1, duration: nil, hasAudio: false)
        let motion = ExportComponent(role: .motion, filename: UUID().uuidString + ".mp4", byteCount: Int64(bytes.count), sha256: sha,
            contentType: "video/mp4", pixelWidth: 1, pixelHeight: 1, duration: 1, hasAudio: true)
        return ExportBatchResult(jobID: UUID().uuidString, assets: [.init(localIdentifier: "selected", state: "ready", components: live && !missingMotion ? [still, motion] : [still], reason: nil)])
    }
    var sha: String { SHA256.hash(data: bytes).map { String(format: "%02x", $0) }.joined() }
    func validate(_ upload: MediaUpload) throws { assert(upload.sha256 == sha && upload.size == bytes.count) }
    func read(_ upload: MediaUpload, offset: Int, count: Int) throws -> Data { bytes.subdata(in: offset..<offset + count) }
}
private actor Server: MediaServicing {
    var content: [String: Data] = [:]
    var lostChunk = true
    var received = 0
    var completed = 0
    var loseCompletion = false
    var completeUploads = Set<String>()
    var afterChunk: (@MainActor @Sendable () -> Void)?
    func revokeAfterChunk(_ hook: @escaping @MainActor @Sendable () -> Void) { lostChunk = false; afterChunk = hook }
    func interruptCompletion() { loseCompletion = true }
    var deny = false
    func setDeny() { deny = true }
    func stats() -> (Int, Int) { (received, completed) }
    func begin(_ local: PairingIdentity, upload: MediaUpload) async throws -> MediaBegin {
        if deny { throw PairingFailure.unauthorized }
        return MediaBegin(upload_id: upload.requestKey, next_offset: content[upload.requestKey]?.count ?? 0, state: completeUploads.contains(upload.requestKey) ? "complete" : "active")
    }
    func chunk(_ local: PairingIdentity, uploadID: String, offset: Int, data: Data) async throws -> MediaChunk {
        received += 1
        let previous = content[uploadID] ?? Data()
        if offset < previous.count { assert(previous.subdata(in: offset..<offset + data.count) == data) }
        else { assert(offset == previous.count); content[uploadID] = previous + data }
        if let afterChunk { await afterChunk() }
        if lostChunk { lostChunk = false; throw PairingFailure.unavailable }
        return MediaChunk(upload_id: uploadID, next_offset: offset + data.count)
    }
    func complete(_ local: PairingIdentity, upload: MediaUpload) async throws -> MediaComplete {
        completed += 1
        completeUploads.insert(upload.requestKey)
        if loseCompletion { loseCompletion = false; throw PairingFailure.unavailable }
        return MediaComplete(component_id: "component-" + upload.requestKey, state: "ready", size: upload.size, mime: upload.mime)
    }
}

@main struct MediaWorkflowTests {
    @MainActor static func main() async throws {
        let sample = try Sample(), copies = Copies(), server = Server()
        let first = MediaCoordinator(selection: sample, exporter: copies, files: copies, service: server)
        do { _ = try await first.start(allowICloud: false); fatalError("Lost chunk should interrupt") } catch PairingFailure.unavailable {}
        assert(sample.value.media?.components[0].offset == 0 && copies.exported == 1)
        // A restart reloads a serialized checkpoint, never re-exports uploaded bytes.
        sample.value = try JSONDecoder().decode(ImportCheckpoint.self, from: NativeJSON.encode(sample.value))
        let restarted = MediaCoordinator(selection: sample, exporter: copies, files: copies, service: server)
        let finished = try await restarted.resume()
        let stats = await server.stats()
        assert(finished.readyCount(sample.value) == 1 && stats.0 == 3 && stats.1 == 1 && copies.exported == 1)
        print("PASS_interrupted_chunk_restart_replays_identical_bytes_and_stable_keys")

        let changed = try Sample(), changedCopies = Copies(), changedServer = Server()
        changedCopies.changedDuringExport = { changed.changed = true }
        do { _ = try await MediaCoordinator(selection: changed, exporter: changedCopies, files: changedCopies, service: changedServer).start(allowICloud: false); fatalError("Changed revision must fail") } catch {}
        let changedStats = await changedServer.stats()
        assert(changed.value.stage == .revocationPending && changedStats.0 == 0)
        print("PASS_revision_change_after_export_never_assigns_frozen_revision")

        sample.changed = true
        do { _ = try await restarted.resume(); fatalError("Revoked selection must fail") } catch {}
        let revokedStats = await server.stats()
        assert(revokedStats.0 == stats.0 && sample.value.stage == .revocationPending)
        print("PASS_revocation_blocks_retained_file_retry")

        let live = try Sample(live: true), liveCopies = Copies(), liveServer = Server()
        liveCopies.missingMotion = true
        let liveWorker = MediaCoordinator(selection: live, exporter: liveCopies, files: liveCopies, service: liveServer)
        do { _ = try await liveWorker.start(allowICloud: false) } catch PairingFailure.unavailable {}
        let partial = try await liveWorker.resume()
        assert(partial.components.count == 1 && partial.components[0].componentID != nil && partial.readyCount(live.value) == 0)
        print("PASS_live_still_alone_is_partial_never_ready")

        let paired = try Sample(live: true), pairedCopies = Copies(), pairedServer = Server()
        let pairedWorker = MediaCoordinator(selection: paired, exporter: pairedCopies, files: pairedCopies, service: pairedServer)
        do { _ = try await pairedWorker.start(allowICloud: false) } catch PairingFailure.unavailable {}
        let complete = try await pairedWorker.resume()
        assert(complete.readyCount(paired.value) == 1 && complete.components.count == 2 && complete.components.contains { $0.role == "motion" && $0.hasAudio })
        print("PASS_live_components_checkpoint_independently_and_retain_audio_descriptor")

        let finalSample = try Sample(), finalCopies = Copies(), finalServer = Server()
        let finalWorker = MediaCoordinator(selection: finalSample, exporter: finalCopies, files: finalCopies, service: finalServer)
        do { _ = try await finalWorker.start(allowICloud: false) } catch PairingFailure.unavailable {}
        await finalServer.interruptCompletion()
        do { _ = try await finalWorker.resume(); fatalError("Lost completion should interrupt") } catch PairingFailure.unavailable {}
        assert(finalSample.value.media?.components[0].offset == finalCopies.bytes.count && finalSample.value.media?.components[0].componentID == nil)
        let finalJob = try await MediaCoordinator(selection: finalSample, exporter: finalCopies, files: finalCopies, service: finalServer).resume()
        let finalStats = await finalServer.stats()
        assert(finalJob.readyCount(finalSample.value) == 1 && finalStats.0 == 3 && finalStats.1 == 2 && finalCopies.exported == 1)
        print("PASS_lost_complete_response_retries_without_reexport_or_new_chunks")

        let restricted = try Sample(), restrictedCopies = Copies(), restrictedServer = Server()
        await restrictedServer.revokeAfterChunk { restricted.changed = true; restricted.value.stage = .revocationPending }
        let restrictedWorker = MediaCoordinator(selection: restricted, exporter: restrictedCopies, files: restrictedCopies, service: restrictedServer)
        do { _ = try await restrictedWorker.start(allowICloud: false); fatalError("Late receipt overwrote revocation") } catch {}
        let restrictedStats = await restrictedServer.stats()
        assert(restricted.value.stage == .revocationPending && restricted.value.media?.components[0].offset == 0 && restrictedStats.0 == 1 && restrictedStats.1 == 0)
        do { _ = try await restrictedWorker.resume(); fatalError("Pending restriction resumed") } catch {}
        let retriedStats = await restrictedServer.stats()
        assert(retriedStats.0 == 1 && retriedStats.1 == 0)
        print("PASS_mid_chunk_revocation_keeps_pending_state_and_stops_late_receipts")
    }
}
