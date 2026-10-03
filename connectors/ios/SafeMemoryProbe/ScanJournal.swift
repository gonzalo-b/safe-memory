import Foundation
import Darwin

/// Bounded private journal: one current raw page, compact committed receipts.
@MainActor final class ScanJournal: ScanStoring {
    private let root: URL
    private let manager = FileManager.default
    private var retainedBytes: Int64 = 0
    private let budget: Int64
    init(directory: URL, budget: Int64 = 512 * 1024 * 1024) throws {
        self.budget = budget
        for folder in [directory.deletingLastPathComponent().deletingLastPathComponent(), directory.deletingLastPathComponent(), directory] {
            if let info = try? FileManager.default.attributesOfItem(atPath: folder.path) {
                guard info[.type] as? FileAttributeType == .typeDirectory else { throw ScanFailure.storage }
            }
        }
        root = directory.standardizedFileURL.resolvingSymlinksInPath()
        try manager.createDirectory(at: root, withIntermediateDirectories: true, attributes: [.posixPermissions: 0o700])
        try protect(root, directory: true)
        guard let entries = manager.enumerator(at: root, includingPropertiesForKeys: nil) else { throw ScanFailure.storage }
        for case let entry as URL in entries {
            let info = try manager.attributesOfItem(atPath: entry.path)
            let type = info[.type] as? FileAttributeType
            guard type == .typeDirectory || type == .typeRegular else { throw ScanFailure.storage }
            if type == .typeRegular { retainedBytes += (info[.size] as? NSNumber)?.int64Value ?? 0 }
            guard retainedBytes <= budget else { throw ScanFailure.capacity }
        }
    }
    private func protect(_ url: URL, directory: Bool = false) throws {
        guard try manager.attributesOfItem(atPath: url.path)[.type] as? FileAttributeType == (directory ? .typeDirectory : .typeRegular) else { throw ScanFailure.storage }
        var attributes: [FileAttributeKey: Any] = [.posixPermissions: directory ? 0o700 : 0o600]
        #if os(iOS)
        attributes[.protectionKey] = FileProtectionType.complete
        #endif
        try manager.setAttributes(attributes, ofItemAtPath: url.path)
        var values = URLResourceValues(); values.isExcludedFromBackup = true
        var mutable = url; try mutable.setResourceValues(values)
    }
    private func folder(_ id: String, create: Bool = false) throws -> URL {
        guard UUID(uuidString: id) != nil else { throw ScanFailure.storage }
        try protect(root, directory: true)
        let directory = root.appendingPathComponent(id, isDirectory: true)
        if (try? manager.attributesOfItem(atPath: directory.path)) == nil {
            guard create else { throw ScanFailure.storage }
            let entries = try manager.contentsOfDirectory(at: root, includingPropertiesForKeys: nil)
            guard entries.filter({ $0.lastPathComponent != "current.json" }).count < 64 else { throw ScanFailure.capacity }
            try manager.createDirectory(at: directory, withIntermediateDirectories: false, attributes: [.posixPermissions: 0o700])
        }
        try protect(directory, directory: true); return directory
    }
    private func read<T: Decodable>(_ type: T.Type, from url: URL, maximum: Int = 2 * 1024 * 1024) throws -> T {
        let info = try manager.attributesOfItem(atPath: url.path)
        guard info[.type] as? FileAttributeType == .typeRegular, let size = info[.size] as? NSNumber, size.intValue <= maximum else { throw ScanFailure.storage }
        return try JSONDecoder().decode(type, from: Data(contentsOf: url, options: [.uncached]))
    }
    private func write<T: Encodable>(_ value: T, to url: URL) throws {
        let data = try NativeJSON.encode(value)
        guard data.count <= 2 * 1024 * 1024 else { throw ScanFailure.capacity }
        var oldBytes: Int64 = 0
        if let attributes = try? manager.attributesOfItem(atPath: url.path) {
            guard attributes[.type] as? FileAttributeType == .typeRegular else { throw ScanFailure.storage }
            oldBytes = (attributes[.size] as? NSNumber)?.int64Value ?? 0
        }
        // Reserve transient atomic replacement as well as retained content.
        guard retainedBytes + Int64(data.count) <= budget else { throw ScanFailure.capacity }
        #if os(iOS)
        try data.write(to: url, options: [.atomic, .completeFileProtection])
        #else
        try data.write(to: url, options: [.atomic])
        #endif
        retainedBytes += Int64(data.count) - oldBytes
        try protect(url)
        let file = try FileHandle(forWritingTo: url); defer { try? file.close() }; try file.synchronize()
        let descriptor = open(url.deletingLastPathComponent().path, O_RDONLY | O_DIRECTORY | O_NOFOLLOW)
        guard descriptor >= 0 else { throw ScanFailure.storage }
        defer { close(descriptor) }
        guard fsync(descriptor) == 0 else { throw ScanFailure.storage }
    }
    func load() throws -> ScanState? {
        try protect(root, directory: true)
        let pointer = root.appendingPathComponent("current.json")
        guard (try? manager.attributesOfItem(atPath: pointer.path)) != nil else { return nil }
        let id = try read(String.self, from: pointer, maximum: 256)
        let state = try read(ScanState.self, from: folder(id).appendingPathComponent("state.json"))
        guard state.id == id else { throw ScanFailure.storage }; try validate(state); return state
    }
    func save(_ state: ScanState) throws {
        try validate(state)
        try write(state, to: folder(state.id, create: true).appendingPathComponent("state.json"))
        try write(state.id, to: root.appendingPathComponent("current.json"))
    }
    func page(scanID: String, sequence: Int) throws -> ScanPageRecord? {
        guard (0..<20_000).contains(sequence) else { throw ScanFailure.capacity }
        let path = try folder(scanID).appendingPathComponent("page-\(sequence).json")
        guard (try? manager.attributesOfItem(atPath: path.path)) != nil else { return nil }
        let record = try read(ScanPageRecord.self, from: path)
        try validate(record); guard record.sequence == sequence else { throw ScanFailure.storage }; return record
    }
    func savePage(_ value: ScanPageRecord, scanID: String) throws {
        try validate(value)
        try write(value, to: folder(scanID).appendingPathComponent("page-\(value.sequence).json"))
    }
    private func validate(_ state: ScanState) throws {
        guard UUID(uuidString: state.id) != nil, PairingRequests.identifier(state.deviceID), PairingRequests.identifier(state.libraryID),
              state.fingerprint.range(of: "^[a-f0-9]{64}$", options: .regularExpression) != nil, ["full", "limited"].contains(state.permission),
              state.consent.includeSharedLibrary && state.consent.includeSharedAlbums, !state.cloud || state.copy,
              ["full", "limited", "denied", "revoked"].contains(state.revokePermission), (0...20_000).contains(state.nextSequence),
              (0...1_000_000).contains(state.observed), (0...state.observed).contains(state.accepted), (0...state.observed).contains(state.excluded),
              state.accepted + state.excluded == state.observed, ["recent", "backfill"].contains(state.phase),
              state.sourceMediaReady == nil || state.sourceMediaReady! >= 0,
              state.runID == nil || PairingRequests.identifier(state.runID!), state.recentAfter == nil || ScanPage.date(state.recentAfter!) != nil,
              state.lastInstant == nil || ScanPage.date(state.lastInstant!) != nil,
              state.copyPage == nil || (state.copy && (0..<state.nextSequence).contains(state.copyPage!)) else { throw ScanFailure.storage }
        if let snapshot = state.snapshot { try snapshot.validate(); guard snapshot.permission == state.permission && state.observed <= snapshot.expectedCount else { throw ScanFailure.storage } }
        if [.indexing, .complete].contains(state.stage) { guard state.snapshot != nil else { throw ScanFailure.storage } }
        if state.stage == .complete { guard state.pending == nil && state.observed == state.snapshot?.expectedCount else { throw ScanFailure.storage } }
        if let page = state.pending {
            guard UUID(uuidString: page.id) != nil, page.sequence == state.nextSequence, page.start == state.observed,
                  (1...100).contains(page.assets.count), page.start + page.assets.count <= (state.snapshot?.expectedCount ?? 0),
                  page.checkpoint.count <= 2000, ["recent", "backfill"].contains(page.phase),
                  Set(page.assets.map(\.nativeID)).count == page.assets.count else { throw ScanFailure.storage }
            for row in page.assets { guard try NativeJSON.encode(ImportAsset(row.metadata)) == NativeJSON.encode(row) else { throw ScanFailure.storage } }
        }
    }
    private func validate(_ record: ScanPageRecord) throws {
        guard UUID(uuidString: record.id) != nil, (0..<20_000).contains(record.sequence), (0..<1_000_000).contains(record.start),
              (1...100).contains(record.count), record.start + record.count <= 1_000_000, ["recent", "backfill"].contains(record.phase),
              record.payloadDigest.range(of: "^[a-f0-9]{64}$", options: .regularExpression) != nil, record.accepted.count <= record.count,
              Set(record.accepted.map(\.nativeID)).count == record.accepted.count, Set(record.accepted.map(\.assetID)).count == record.accepted.count,
              record.accepted.allSatisfy({ PairingRequests.text($0.nativeID, maximum: 256) && PairingRequests.identifier($0.assetID) && $0.sourceRevision.range(of: "^[a-f0-9]{64}$", options: .regularExpression) != nil }),
              (record.media?.components.count ?? 0) <= 200, (record.media?.unavailable.count ?? 0) <= 100 else { throw ScanFailure.storage }
    }
}
