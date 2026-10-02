import Foundation
import CryptoKit

@main struct MediaFilesTests {
    @MainActor static func main() throws {
        let temporary = FileManager.default.temporaryDirectory.appendingPathComponent("memory-media-fixture-" + UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: temporary) }
        let root = temporary.appendingPathComponent("private/exports"), exportID = UUID().uuidString, filename = UUID().uuidString + ".jpg"
        let folder = root.appendingPathComponent(exportID), path = folder.appendingPathComponent(filename)
        try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
        let bytes = Data("synthetic component bytes".utf8)
        try bytes.write(to: path)
        let digest = SHA256.hash(data: bytes).map { String(format: "%02x", $0) }.joined()
        let row = ProbeAsset(localIdentifier: "selected", creationInstant: nil, modificationInstant: nil, addedInstant: nil, mediaType: 1, mediaSubtypes: 0,
            pixelWidth: 1, pixelHeight: 1, duration: 0, isHidden: false, isFavorite: false, sourceType: 1, location: nil, burstIdentifier: nil,
            burstSelectionTypes: 0, representsBurst: false, hasAdjustments: false, adjustmentFormatIdentifier: nil, resources: [], unavailable: [:])
        let selection = try ImportSelection(ids: ["selected"], manifest: ProbeManifest(probeInstallationID: "synthetic", authorization: "limited", requestedLimit: 1, assets: [row]),
            consent: ImportConsent(includeHidden: false, includeSharedLibrary: true, includeSharedAlbums: true))
        let upload = MediaUpload(nativeID: "selected", assetID: "asset", sourceRevision: selection.assets[0].sourceRevision, role: "still", mime: "image/jpeg", size: bytes.count,
            sha256: digest, exportJobID: exportID, filename: filename, requestKey: UUID().uuidString, hasAudio: false, uploadID: "upload", offset: bytes.count)
        var checkpoint = ImportCheckpoint(jobID: UUID().uuidString, deviceID: "device", libraryID: "library", fingerprint: String(repeating: "a", count: 64), batchKey: UUID().uuidString,
            selection: selection, stage: .complete, revokePermission: "limited", accepted: 1, excluded: 0, acceptedAssets: [.init(native_id: "selected", asset_id: "asset")])
        checkpoint.media = MediaJob(id: UUID().uuidString, allowICloud: false, exported: true, components: [upload])
        let directory = temporary.appendingPathComponent("private/checkpoints")
        try ImportCheckpointFiles(directory: directory).save(checkpoint)
        let reopened = try ImportCheckpointFiles(directory: directory).load()!
        let before = try NativeJSON.encode(checkpoint), after = try NativeJSON.encode(reopened)
        assert(before == after)
        let files = MediaFiles(root: root)
        try files.validate(upload)
        let read = try files.read(upload, offset: 0, count: bytes.count)
        assert(read == bytes)
        print("PASS_on_disk_checkpoint_keeps_mapping_digest_request_key_and_offset")

        try Data(repeating: 0x62, count: bytes.count).write(to: path)
        do { try files.validate(upload); fatalError("Changed staged bytes accepted") } catch {}
        try bytes.write(to: path)
        do { _ = try files.read(upload, offset: bytes.count, count: 1); fatalError("Out-of-range read accepted") } catch {}
        print("PASS_staged_integrity_and_chunk_bounds_are_checked")

        try FileManager.default.removeItem(at: path)
        let sentinel = temporary.appendingPathComponent("outside")
        try bytes.write(to: sentinel)
        try FileManager.default.createSymbolicLink(at: path, withDestinationURL: sentinel)
        do { try files.validate(upload); fatalError("Symlink staging accepted") } catch {}
        let unchanged = try Data(contentsOf: sentinel)
        assert(unchanged == bytes)
        print("PASS_opaque_staging_symlink_refused_without_reading_outside")
    }
}
