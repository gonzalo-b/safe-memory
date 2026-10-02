import Foundation

@main struct ImportFilesTests {
    @MainActor static func main() throws {
        let temporary = FileManager.default.temporaryDirectory.appendingPathComponent("memory-import-fixture-" + UUID().uuidString, isDirectory: true)
        defer { try? FileManager.default.removeItem(at: temporary) }
        let directory = temporary.appendingPathComponent("private/checkpoints", isDirectory: true)
        let files = try ImportCheckpointFiles(directory: directory)
        let row = ProbeAsset(localIdentifier: "synthetic-selected", creationInstant: nil, modificationInstant: nil, addedInstant: nil, mediaType: 1, mediaSubtypes: 0,
            pixelWidth: 1, pixelHeight: 1, duration: 0, isHidden: false, isFavorite: false, sourceType: 1, location: nil, burstIdentifier: nil,
            burstSelectionTypes: 0, representsBurst: false, hasAdjustments: false, adjustmentFormatIdentifier: nil, resources: [], unavailable: [:])
        let selection = try ImportSelection(ids: [row.localIdentifier], manifest: ProbeManifest(probeInstallationID: "synthetic", authorization: "limited", requestedLimit: 1, assets: [row]),
            consent: ImportConsent(includeHidden: false, includeSharedLibrary: true, includeSharedAlbums: true))
        let checkpoint = ImportCheckpoint(jobID: UUID().uuidString, deviceID: "synthetic-device", libraryID: "local-library", fingerprint: String(repeating: "a", count: 64),
            batchKey: UUID().uuidString, selection: selection, revokePermission: "limited")
        try files.save(checkpoint)
        let restarted = try ImportCheckpointFiles(directory: directory)
        let restored = try restarted.load()!
        assert(tryData(restored) == tryData(checkpoint))
        let payload = directory.appendingPathComponent(checkpoint.jobID + ".json")
        let mode = try FileManager.default.attributesOfItem(atPath: payload.path)[.posixPermissions] as! NSNumber
        assert(mode.intValue == 0o600)
        let encoded = try Data(contentsOf: payload)
        assert(!String(decoding: encoded, as: UTF8.self).contains("\"credential\""))
        print("PASS private_checkpoint_survives_reopen_without_credentials")

        let changed = String(decoding: encoded, as: UTF8.self).replacingOccurrences(of: checkpoint.selection.assets[0].sourceRevision, with: String(repeating: "0", count: 64))
        try Data(changed.utf8).write(to: payload)
        do { _ = try restarted.load(); fatalError("Tampered revision must fail closed") } catch {}
        try files.save(checkpoint)
        print("PASS_checkpoint_revalidates_full_wrapper_digest")

        let pointer = directory.appendingPathComponent("current.json")
        try FileManager.default.removeItem(at: pointer)
        let sentinel = temporary.appendingPathComponent("outside-fixture")
        let original = Data("synthetic sentinel".utf8); try original.write(to: sentinel)
        try FileManager.default.createSymbolicLink(at: pointer, withDestinationURL: sentinel)
        do { _ = try restarted.load(); fatalError("Symlink must be refused") } catch {}
        do { try files.save(checkpoint); fatalError("Symlink must not be overwritten or followed") } catch {}
        let unchanged = try Data(contentsOf: sentinel)
        assert(unchanged == original)
        print("PASS_checkpoint_symlink_refused_without_touching_target")
    }
    static func tryData(_ value: ImportCheckpoint) -> Data { try! NativeJSON.encode(value) }
}
