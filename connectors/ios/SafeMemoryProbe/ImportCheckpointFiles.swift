import Foundation
import Darwin

@MainActor
final class ImportCheckpointFiles: ImportCheckpointStore {
    private let root: URL
    private let manager = FileManager.default
    init(directory: URL) throws {
        for candidate in [directory.deletingLastPathComponent().deletingLastPathComponent(), directory.deletingLastPathComponent(), directory] {
            if let attributes = try? FileManager.default.attributesOfItem(atPath: candidate.path) {
                guard attributes[.type] as? FileAttributeType == .typeDirectory else { throw ImportFailure.storage }
            }
        }
        root = directory.standardizedFileURL.resolvingSymlinksInPath()
        try manager.createDirectory(at: root, withIntermediateDirectories: true, attributes: [.posixPermissions: 0o700])
        try protect(root, directory: true)
    }
    private func protect(_ url: URL, directory: Bool = false) throws {
        let attributes = try manager.attributesOfItem(atPath: url.path)
        guard attributes[.type] as? FileAttributeType == (directory ? .typeDirectory : .typeRegular) else { throw ImportFailure.storage }
        var desired: [FileAttributeKey: Any] = [.posixPermissions: directory ? 0o700 : 0o600]
        #if os(iOS)
        desired[.protectionKey] = FileProtectionType.complete
        #endif
        try manager.setAttributes(desired, ofItemAtPath: url.path)
        var values = URLResourceValues(); values.isExcludedFromBackup = true
        var target = url; try target.setResourceValues(values)
    }
    private func read(_ file: URL, maximum: Int) throws -> Data {
        let attributes = try manager.attributesOfItem(atPath: file.path)
        guard attributes[.type] as? FileAttributeType == .typeRegular,
              let bytes = attributes[.size] as? NSNumber, bytes.intValue <= maximum else { throw ImportFailure.storage }
        return try Data(contentsOf: file, options: [.uncached])
    }
    func load() throws -> ImportCheckpoint? {
        try protect(root, directory: true)
        let pointer = root.appendingPathComponent("current.json")
        guard (try? manager.attributesOfItem(atPath: pointer.path)) != nil else { return nil }
        let id = try JSONDecoder().decode(String.self, from: read(pointer, maximum: 256))
        guard UUID(uuidString: id) != nil else { throw ImportFailure.storage }
        let checkpoint = try JSONDecoder().decode(ImportCheckpoint.self, from: read(root.appendingPathComponent(id + ".json"), maximum: 2 * 1024 * 1024))
        try validate(checkpoint)
        guard checkpoint.jobID == id else { throw ImportFailure.storage }
        return checkpoint
    }
    private func validate(_ checkpoint: ImportCheckpoint) throws {
        guard UUID(uuidString: checkpoint.jobID) != nil, UUID(uuidString: checkpoint.batchKey) != nil,
              PairingRequests.identifier(checkpoint.deviceID), PairingRequests.identifier(checkpoint.libraryID), checkpoint.fingerprint.count == 64,
              ["full", "limited", "denied", "revoked"].contains(checkpoint.revokePermission) else { throw ImportFailure.storage }
        let old = checkpoint.selection
        let rebuilt = try ImportSelection(ids: old.ids, manifest: ProbeManifest(probeInstallationID: "checkpoint-validation", authorization: old.permission,
            requestedLimit: old.ids.count, assets: old.assets.map(\.metadata)), consent: old.consent)
        guard try NativeJSON.encode(rebuilt) == NativeJSON.encode(old) else { throw ImportFailure.storage }
    }
    private func write(_ data: Data, to url: URL) throws {
        if manager.fileExists(atPath: url.path) { try protect(url) }
        #if os(iOS)
        try data.write(to: url, options: [.atomic, .completeFileProtection])
        #else
        try data.write(to: url, options: [.atomic])
        #endif
        try protect(url)
        let handle = try FileHandle(forWritingTo: url); defer { try? handle.close() }
        try handle.synchronize()
        let directory = open(root.path, O_RDONLY | O_DIRECTORY | O_NOFOLLOW)
        guard directory >= 0 else { throw ImportFailure.storage }
        defer { close(directory) }
        guard fsync(directory) == 0 else { throw ImportFailure.storage }
    }
    func save(_ checkpoint: ImportCheckpoint) throws {
        try validate(checkpoint); try protect(root, directory: true)
        let entries = try manager.contentsOfDirectory(at: root, includingPropertiesForKeys: nil)
        var size: Int64 = 0
        for file in entries {
            let attributes = try manager.attributesOfItem(atPath: file.path)
            guard attributes[.type] as? FileAttributeType == .typeRegular else { throw ImportFailure.storage }
            size += (attributes[.size] as? NSNumber)?.int64Value ?? 0
        }
        let file = root.appendingPathComponent(checkpoint.jobID + ".json")
        guard size <= 64 * 1024 * 1024, manager.fileExists(atPath: file.path) || entries.count < 65 else { throw ImportFailure.storage }
        let encoded = try NativeJSON.encode(checkpoint)
        guard encoded.count <= 2 * 1024 * 1024 else { throw ImportFailure.storage }
        let previous = (try? manager.attributesOfItem(atPath: file.path)[.size] as? NSNumber)?.int64Value ?? 0
        guard size - previous + Int64(encoded.count) + 256 <= 64 * 1024 * 1024 else { throw ImportFailure.storage }
        try write(encoded, to: file)
        try write(NativeJSON.encode(checkpoint.jobID), to: root.appendingPathComponent("current.json"))
    }
}
