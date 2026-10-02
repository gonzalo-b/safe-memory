import Foundation
import CryptoKit
import Darwin

/// Opens only opaque files inside app-owned optimized export staging.
@MainActor struct MediaFiles: MediaFileReading {
    let root: URL
    private func openFile(_ upload: MediaUpload) throws -> FileHandle {
        guard UUID(uuidString: upload.exportJobID) != nil, !upload.filename.contains("/"),
              UUID(uuidString: String(upload.filename.dropLast(4))) != nil,
              ["jpg", "mp4"].contains(URL(fileURLWithPath: upload.filename).pathExtension) else { throw MediaFailure.storage }
        let job = root.appendingPathComponent(upload.exportJobID, isDirectory: true)
        for folder in [root.deletingLastPathComponent(), root, job] {
            guard try FileManager.default.attributesOfItem(atPath: folder.path)[.type] as? FileAttributeType == .typeDirectory else { throw MediaFailure.storage }
        }
        let path = job.appendingPathComponent(upload.filename)
        let descriptor = open(path.path, O_RDONLY | O_NOFOLLOW)
        guard descriptor >= 0 else { throw MediaFailure.storage }
        let handle = FileHandle(fileDescriptor: descriptor, closeOnDealloc: true)
        var info = stat()
        guard fstat(descriptor, &info) == 0, info.st_mode & S_IFMT == S_IFREG,
              info.st_size == upload.size, (1...MediaJob.maximumComponent).contains(upload.size) else { try? handle.close(); throw MediaFailure.integrity }
        return handle
    }
    func validate(_ upload: MediaUpload) throws {
        let handle = try openFile(upload); defer { try? handle.close() }
        var hash = SHA256(), bytes = 0
        while let chunk = try handle.read(upToCount: MediaJob.chunkSize), !chunk.isEmpty {
            try Task.checkCancellation(); bytes += chunk.count
            guard bytes <= upload.size else { throw MediaFailure.integrity }; hash.update(data: chunk)
        }
        guard bytes == upload.size, hash.finalize().map({ String(format: "%02x", $0) }).joined() == upload.sha256 else { throw MediaFailure.integrity }
        // Ensure retained export bytes precede the durable upload checkpoint.
        guard fsync(handle.fileDescriptor) == 0 else { throw MediaFailure.storage }
        let job = root.appendingPathComponent(upload.exportJobID)
        let directory = open(job.path, O_RDONLY | O_DIRECTORY | O_NOFOLLOW)
        guard directory >= 0 else { throw MediaFailure.storage }
        defer { close(directory) }
        guard fsync(directory) == 0 else { throw MediaFailure.storage }
    }
    func read(_ upload: MediaUpload, offset: Int, count: Int) throws -> Data {
        guard offset >= 0, (1...MediaJob.chunkSize).contains(count), offset <= upload.size - count else { throw MediaFailure.integrity }
        let handle = try openFile(upload); defer { try? handle.close() }
        try handle.seek(toOffset: UInt64(offset))
        let data = try handle.read(upToCount: count) ?? Data()
        guard data.count == count else { throw MediaFailure.integrity }
        return data
    }
}
