import Foundation
import CryptoKit
import Darwin

/// One current checkpoint, retained job directories and opaque original bytes.
@MainActor final class OriginalFiles: OriginalStoring, OriginalFileReading {
    let root: URL
    private let manager = FileManager.default
    private let maximum: Int
    init(directory: URL, maximum: Int = 512 * 1024 * 1024) throws {
        self.maximum = maximum
        for path in [directory.deletingLastPathComponent().deletingLastPathComponent(), directory.deletingLastPathComponent(), directory] {
            if let info = try? FileManager.default.attributesOfItem(atPath: path.path) {
                guard info[.type] as? FileAttributeType == .typeDirectory else { throw OriginalFailure.storage }
            }
        }
        root = directory.standardizedFileURL.resolvingSymlinksInPath()
        try manager.createDirectory(at: root, withIntermediateDirectories: true, attributes: [.posixPermissions: 0o700])
        try protect(root, directory: true); _ = try allowance(0)
    }
    func protect(_ path: URL, directory: Bool = false) throws {
        guard try manager.attributesOfItem(atPath: path.path)[.type] as? FileAttributeType == (directory ? .typeDirectory : .typeRegular) else { throw OriginalFailure.storage }
        var attributes: [FileAttributeKey: Any] = [.posixPermissions: directory ? 0o700 : 0o600]
        #if os(iOS)
        attributes[.protectionKey] = FileProtectionType.complete
        #endif
        try manager.setAttributes(attributes, ofItemAtPath: path.path)
        var values = URLResourceValues(); values.isExcludedFromBackup = true
        var mutable = path; try mutable.setResourceValues(values)
    }
    func allowance(_ requested: Int) throws -> Int {
        try protect(root, directory: true)
        guard let files = manager.enumerator(at: root, includingPropertiesForKeys: nil) else { throw OriginalFailure.storage }
        var used = 0
        for case let file as URL in files {
            let info = try manager.attributesOfItem(atPath: file.path), type = info[.type] as? FileAttributeType
            guard type == .typeDirectory || type == .typeRegular else { throw OriginalFailure.storage }
            if type == .typeRegular {
                let size = (info[.size] as? NSNumber)?.intValue ?? maximum
                guard size <= maximum - used else { throw OriginalFailure.capacity }; used += size
            }
        }
        guard requested == 0 || used < maximum else { throw OriginalFailure.capacity }
        return min(requested, maximum - used)
    }
    func folder(_ id: String, create: Bool = false) throws -> URL {
        guard UUID(uuidString: id) != nil else { throw OriginalFailure.storage }
        try protect(root, directory: true)
        let path = root.appendingPathComponent(id, isDirectory: true)
        if (try? manager.attributesOfItem(atPath: path.path)) == nil {
            guard create else { throw OriginalFailure.storage }
            guard try manager.contentsOfDirectory(atPath: root.path).filter({ $0 != "current.json" }).count < 64 else { throw OriginalFailure.capacity }
            try manager.createDirectory(at: path, withIntermediateDirectories: false, attributes: [.posixPermissions: 0o700])
        }
        try protect(path, directory: true); return path
    }
    private func readJSON<T: Decodable>(_ type: T.Type, from path: URL) throws -> T {
        let fd = open(path.path, O_RDONLY | O_NOFOLLOW)
        guard fd >= 0 else { throw OriginalFailure.storage }
        let file = FileHandle(fileDescriptor: fd, closeOnDealloc: true); defer { try? file.close() }
        var info = stat()
        guard fstat(fd, &info) == 0, info.st_mode & S_IFMT == S_IFREG, info.st_size <= 2 * 1024 * 1024 else { throw OriginalFailure.storage }
        return try JSONDecoder().decode(type, from: file.readToEnd() ?? Data())
    }
    private func writeJSON<T: Encodable>(_ value: T, to path: URL) throws {
        if let info = try? manager.attributesOfItem(atPath: path.path) { guard info[.type] as? FileAttributeType == .typeRegular else { throw OriginalFailure.storage } }
        let bytes = try NativeJSON.encode(value)
        guard bytes.count <= 2 * 1024 * 1024, try allowance(bytes.count) == bytes.count else { throw OriginalFailure.capacity }
        #if os(iOS)
        try bytes.write(to: path, options: [.atomic, .completeFileProtection])
        #else
        try bytes.write(to: path, options: .atomic)
        #endif
        try protect(path)
        let file = try FileHandle(forWritingTo: path); defer { try? file.close() }; try file.synchronize()
        try syncDirectory(path.deletingLastPathComponent())
    }
    private func syncDirectory(_ directory: URL) throws {
        let fd = open(directory.path, O_RDONLY | O_DIRECTORY | O_NOFOLLOW)
        guard fd >= 0 else { throw OriginalFailure.storage }; defer { close(fd) }
        guard fsync(fd) == 0 else { throw OriginalFailure.storage }
    }
    func load() throws -> OriginalJob? {
        try protect(root, directory: true)
        let pointer = root.appendingPathComponent("current.json")
        guard (try? manager.attributesOfItem(atPath: pointer.path)) != nil else { return nil }
        let id = try readJSON(String.self, from: pointer)
        let job = try readJSON(OriginalJob.self, from: folder(id).appendingPathComponent("checkpoint.json"))
        guard job.id == id else { throw OriginalFailure.storage }; try job.validate(); return job
    }
    func save(_ job: OriginalJob) throws {
        try job.validate()
        try writeJSON(job, to: folder(job.id, create: true).appendingPathComponent("checkpoint.json"))
        try writeJSON(job.id, to: root.appendingPathComponent("current.json"))
    }
    func newSpool(jobID: String, limit: Int) throws -> OriginalSpool {
        let path = try folder(jobID).appendingPathComponent(UUID().uuidString)
        let retained = try manager.contentsOfDirectory(atPath: folder(jobID).path).count
        guard retained < 65 else { throw OriginalFailure.capacity }
        // Keep space for atomic checkpoint and security-revocation writes even
        // when retained partial resources reach their media allowance.
        let allowance = min(limit, try self.allowance(maximum) - 4 * 1024 * 1024)
        guard allowance > 0 else { throw OriginalFailure.capacity }
        let spool = try OriginalSpool(path: path, limit: allowance)
        try protect(path); return spool
    }
    private func openComponent(_ component: OriginalComponent, jobID: String) throws -> FileHandle {
        guard UUID(uuidString: component.filename) != nil else { throw OriginalFailure.storage }
        let path = try folder(jobID).appendingPathComponent(component.filename)
        let fd = open(path.path, O_RDONLY | O_NOFOLLOW)
        guard fd >= 0 else { throw OriginalFailure.storage }
        let file = FileHandle(fileDescriptor: fd, closeOnDealloc: true)
        var info = stat()
        guard fstat(fd, &info) == 0, info.st_mode & S_IFMT == S_IFREG, info.st_size == component.descriptor.size,
              (1...OriginalPolicy.maximum).contains(component.descriptor.size) else { try? file.close(); throw OriginalFailure.integrity }
        return file
    }
    func validate(_ component: OriginalComponent, jobID: String) throws {
        let file = try openComponent(component, jobID: jobID); defer { try? file.close() }
        var hash = SHA256(), count = 0
        while let data = try file.read(upToCount: OriginalPolicy.chunkSize), !data.isEmpty {
            try Task.checkCancellation(); count += data.count; guard count <= component.descriptor.size else { throw OriginalFailure.integrity }; hash.update(data: data)
        }
        guard count == component.descriptor.size, hash.finalize().map({ String(format:"%02x",$0) }).joined() == component.descriptor.sha256,
              fsync(file.fileDescriptor) == 0 else { throw OriginalFailure.integrity }
        try syncDirectory(folder(jobID))
    }
    func read(_ component: OriginalComponent, jobID: String, offset: Int, count: Int) throws -> Data {
        guard offset >= 0, (1...OriginalPolicy.chunkSize).contains(count), offset <= component.descriptor.size - count else { throw OriginalFailure.integrity }
        let file = try openComponent(component, jobID: jobID); defer { try? file.close() }; try file.seek(toOffset: UInt64(offset))
        let bytes = try file.read(upToCount: count) ?? Data(); guard bytes.count == count else { throw OriginalFailure.integrity }; return bytes
    }
}

/// PhotoKit callback data is consumed immediately on its serial callback queue.
final class OriginalSpool: @unchecked Sendable {
    let path: URL
    private let lock = NSLock()
    private var file: FileHandle?
    private let limit: Int
    private var size = 0
    private var digest = SHA256()
    init(path: URL, limit: Int) throws {
        self.path = path; self.limit = limit
        let fd = open(path.path, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW, 0o600)
        guard fd >= 0 else { throw OriginalFailure.storage }; file = FileHandle(fileDescriptor: fd, closeOnDealloc: true)
    }
    func append(_ bytes: Data) throws {
        lock.lock(); defer { lock.unlock() }
        guard let file else { throw CancellationError() }
        guard bytes.count <= limit - size else { throw OriginalFailure.capacity }
        try file.write(contentsOf: bytes); digest.update(data: bytes); size += bytes.count
    }
    func finish(_ resource: ProbeResource) throws -> OriginalComponent {
        lock.lock(); defer { lock.unlock() }
        guard let file, size > 0, let role = OriginalPolicy.roles[resource.role] else { throw OriginalFailure.source_unavailable }
        try file.synchronize(); try file.close(); self.file = nil
        return OriginalComponent(descriptor: .init(resource_type: role, original_filename: resource.originalFilename,
            uniform_type_identifier: resource.uniformTypeIdentifier, size: size, sha256: digest.finalize().map { String(format:"%02x",$0) }.joined()), filename: path.lastPathComponent)
    }
    func cancel() { lock.lock(); defer { lock.unlock() }; try? file?.close(); file = nil }
    deinit { try? file?.close() }
}
