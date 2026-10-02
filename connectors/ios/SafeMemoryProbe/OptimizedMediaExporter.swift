import Foundation
@preconcurrency import Photos
@preconcurrency import UIKit
@preconcurrency import AVFoundation
import CryptoKit

private struct ExportImage: @unchecked Sendable { let value: UIImage }
private struct ExportVideo: @unchecked Sendable { let asset: AVAsset; let audioMix: AVAudioMix? }
// Only cancelExport crosses isolation; export-session setup stays on MainActor.
private struct ExportCancellation: @unchecked Sendable { let session: AVAssetExportSession }

/// Local-only API. Callers retain the manifest privately and supply separately
/// recorded consent for the exact selected IDs. No authorization prompt occurs.
@MainActor
final class OptimizedMediaExporter {
    static let shared = OptimizedMediaExporter()
    private init() {}
    private var running = false
    private let componentLimit: Int64 = 64 * 1024 * 1024
    private let stagingLimit: Int64 = 512 * 1024 * 1024
    private let imageManager = PHImageManager.default()

    func export(selectedIDs: [String], manifest: ProbeManifest, consent: ExportConsent) async throws -> ExportBatchResult {
        guard !running else { throw ExportFailure.busy }
        guard (1...100).contains(selectedIDs.count), manifest.assets.count <= 100 else { throw ExportFailure.invalidSelection }
        guard ["full", "limited"].contains(manifest.authorization),
              PhotosReader.authorizationName(PHPhotoLibrary.authorizationStatus(for: .readWrite)) == manifest.authorization
        else { throw ExportFailure.restricted }
        let scopes = try manifest.assets.filter { selectedIDs.contains($0.localIdentifier) }.map { row -> ExportAssetScope in
            let media: ExportMedia
            if row.mediaType == PHAssetMediaType.video.rawValue { media = .video }
            else if row.mediaType == PHAssetMediaType.image.rawValue {
                media = row.mediaSubtypes & PHAssetMediaSubtype.photoLive.rawValue != 0 ? .live : .photo
            } else { throw ExportFailure.unsupported }
            return ExportAssetScope(id: row.localIdentifier, hidden: row.isHidden,
                sharedAlbum: row.sourceType & PHAssetSourceType.typeCloudShared.rawValue != 0,
                collection: row.collectionProvenance, media: media)
        }
        let plan = try ExportPlan(selectedIDs: selectedIDs, authorized: scopes, consent: consent)
        running = true
        defer { running = false }
        let stage = try ExportStaging(maximum: stagingLimit)
        var results: [ExportAssetResult] = []
        var stop: ExportFailure?
        for scope in plan.assets {
            if let stop {
                results.append(.init(localIdentifier: scope.id, state: stop.rawValue, components: [], reason: stop)); continue
            }
            do {
                try Task.checkCancellation()
                guard let row = manifest.assets.first(where: { $0.localIdentifier == scope.id }) else { throw ExportFailure.restricted }
                let asset = try currentAsset(row, authorization: manifest.authorization, consent: consent)
                let components = try await bounded {
                    try await self.exportOne(asset, scope: scope, consent: consent, stage: stage)
                }
                _ = try currentAsset(row, authorization: manifest.authorization, consent: consent)
                guard scope.media.isComplete(components.map(\.role)) else { throw ExportFailure.unsupported }
                results.append(.init(localIdentifier: scope.id, state: "ready", components: components, reason: nil))
            } catch {
                let failure = error is CancellationError ? ExportFailure.cancelled : (error as? ExportFailure ?? .failed)
                results.append(.init(localIdentifier: scope.id, state: failure.rawValue, components: [], reason: failure))
                if [.cancelled, .timedOut, .limitExceeded, .restricted].contains(failure) { stop = failure }
            }
        }
        // A permission/scope change during a later asset also restricts earlier
        // components. Bytes remain private; no stale ready filenames are returned.
        results = results.map { result in
            guard result.state == "ready" else { return result }
            do {
                guard let row = manifest.assets.first(where: { $0.localIdentifier == result.localIdentifier }) else { throw ExportFailure.restricted }
                _ = try currentAsset(row, authorization: manifest.authorization, consent: consent)
                return result
            } catch { return .init(localIdentifier: result.localIdentifier, state: "restricted", components: [], reason: .restricted) }
        }
        return ExportBatchResult(jobID: stage.jobID, assets: results)
    }

    private func currentAsset(_ expected: ProbeAsset, authorization: String, consent: ExportConsent) throws -> PHAsset {
        guard PhotosReader.authorizationName(PHPhotoLibrary.authorizationStatus(for: .readWrite)) == authorization else { throw ExportFailure.restricted }
        let options = PHFetchOptions()
        options.includeHiddenAssets = consent.includeHidden
        options.includeAssetSourceTypes = consent.includeSharedAlbums ? [.typeUserLibrary, .typeCloudShared] : [.typeUserLibrary]
        options.fetchLimit = 1
        // Never enumerate a library or expand the caller's selected-ID scope.
        guard let asset = PHAsset.fetchAssets(withLocalIdentifiers: [expected.localIdentifier], options: options).firstObject else {
            throw ExportFailure.unavailable // absent and permission-limited are indistinguishable here
        }
        let format = ISO8601DateFormatter(); format.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        guard !asset.isHidden || consent.includeHidden,
              asset.isHidden == expected.isHidden, asset.sourceType.rawValue == expected.sourceType,
              asset.mediaType.rawValue == expected.mediaType, asset.mediaSubtypes.rawValue == expected.mediaSubtypes,
              asset.modificationDate.map({ format.string(from: $0) }) == expected.modificationInstant
        else { throw ExportFailure.restricted }
        return asset
    }

    private func bounded<T: Sendable>(_ operation: @escaping @Sendable () async throws -> T) async throws -> T {
        try await withThrowingTaskGroup(of: T.self) { group in
            group.addTask { try await operation() }
            group.addTask { try await Task.sleep(for: .seconds(90)); throw ExportFailure.timedOut }
            defer { group.cancelAll() }
            guard let first = try await group.next() else { throw ExportFailure.failed }
            return first
        }
    }

    private func exportOne(_ asset: PHAsset, scope: ExportAssetScope, consent: ExportConsent, stage: ExportStaging) async throws -> [ExportComponent] {
        var components: [ExportComponent] = []
        if scope.media == .video {
            guard asset.duration.isFinite, asset.duration > 0, asset.duration <= 300 else { throw ExportFailure.limitExceeded }
        }
        if scope.media != .video {
            let image = try await requestImage(asset, network: consent.allowICloud)
            try Task.checkCancellation()
            guard let dimensions = ExportDimensions.fit(width: Int(image.value.size.width * image.value.scale), height: Int(image.value.size.height * image.value.scale)) else { throw ExportFailure.unsupported }
            let format = UIGraphicsImageRendererFormat(); format.scale = 1; format.opaque = true; format.preferredRange = .standard
            let rendered = UIGraphicsImageRenderer(size: CGSize(width: dimensions.width, height: dimensions.height), format: format).image { _ in
                image.value.draw(in: CGRect(x: 0, y: 0, width: dimensions.width, height: dimensions.height))
            }
            guard let data = rendered.jpegData(compressionQuality: 0.85) else { throw ExportFailure.unsupported }
            let limit = try stage.allowance(componentLimit)
            guard data.count <= limit else { throw ExportFailure.limitExceeded }
            let output = stage.newFile(extension: "jpg")
            try data.write(to: output, options: [.atomic, .completeFileProtection])
            try stage.protect(output)
            components.append(try component(output, role: scope.media == .live ? .cover : .photo,
                type: "image/jpeg", width: dimensions.width, height: dimensions.height, duration: nil, audio: false))
        }
        if scope.media == .video {
            let source = try await requestVideo(asset, network: consent.allowICloud)
            components.append(try await transcode(source, role: .video, stage: stage))
        } else if scope.media == .live {
            let resources = PHAssetResource.assetResources(for: asset)
            // Edited stills must not be paired with an unrelated original motion.
            let kind: PHAssetResourceType = asset.hasAdjustments ? .fullSizePairedVideo : .pairedVideo
            guard let motion = resources.first(where: { $0.type == kind }) else { throw ExportFailure.unsupported }
            let input = stage.newFile(extension: "source-motion")
            try await requestResource(motion, output: input, maximum: stage.allowance(componentLimit), network: consent.allowICloud)
            try stage.protect(input)
            components.append(try await transcode(ExportVideo(asset: AVURLAsset(url: input), audioMix: nil), role: .motion, stage: stage))
        }
        return components
    }

    private func requestImage(_ asset: PHAsset, network: Bool) async throws -> ExportImage {
        try Task.checkCancellation()
        let bridge = ExportRequestBridge<ExportImage>()
        let manager = imageManager
        return try await withTaskCancellationHandler {
            try await withCheckedThrowingContinuation { continuation in
                bridge.install(continuation)
                let options = PHImageRequestOptions()
                options.version = .current; options.deliveryMode = .highQualityFormat
                options.resizeMode = .exact; options.isNetworkAccessAllowed = network
                let request = manager.requestImage(for: asset, targetSize: CGSize(width: 2048, height: 2048), contentMode: .aspectFit, options: options) { image, info in
                    if (info?[PHImageResultIsDegradedKey] as? Bool) == true { return }
                    if let image { bridge.finish(.success(ExportImage(value: image))) }
                    else { bridge.finish(.failure(Self.photoFailure(info, network: network))) }
                }
                bridge.onCancel { manager.cancelImageRequest(request) }
            }
        } onCancel: { bridge.cancel() }
    }

    private func requestVideo(_ asset: PHAsset, network: Bool) async throws -> ExportVideo {
        try Task.checkCancellation()
        let bridge = ExportRequestBridge<ExportVideo>()
        let manager = imageManager
        return try await withTaskCancellationHandler {
            try await withCheckedThrowingContinuation { continuation in
                bridge.install(continuation)
                let options = PHVideoRequestOptions()
                options.version = .current; options.deliveryMode = .highQualityFormat; options.isNetworkAccessAllowed = network
                let request = manager.requestAVAsset(forVideo: asset, options: options) { source, mix, info in
                    if let source { bridge.finish(.success(ExportVideo(asset: source, audioMix: mix))) }
                    else { bridge.finish(.failure(Self.photoFailure(info, network: network))) }
                }
                bridge.onCancel { manager.cancelImageRequest(request) }
            }
        } onCancel: { bridge.cancel() }
    }

    private func requestResource(_ resource: PHAssetResource, output: URL, maximum: Int64, network: Bool) async throws {
        try Task.checkCancellation()
        let bridge = ExportRequestBridge<Bool>()
        let spool = try ExportSpool(output: output, maximum: maximum)
        let manager = PHAssetResourceManager.default()
        _ = try await withTaskCancellationHandler {
            try await withCheckedThrowingContinuation { continuation in
                bridge.install(continuation)
                let options = PHAssetResourceRequestOptions(); options.isNetworkAccessAllowed = network
                let request = manager.requestData(for: resource, options: options) { data in
                    do { try spool.append(data) } catch { bridge.cancel(error) }
                } completionHandler: { error in
                    spool.close()
                    if let error {
                        let native = error as NSError
                        let reason: ExportFailure = !network && native.domain == PHPhotosErrorDomain && native.code == PHPhotosError.Code.networkAccessRequired.rawValue ? .cloudRequired : .unavailable
                        bridge.finish(.failure(reason))
                    } else { bridge.finish(.success(true)) }
                }
                bridge.onCancel { spool.close(); manager.cancelDataRequest(request) }
            }
        } onCancel: { bridge.cancel(); spool.close() }
    }

    nonisolated private static func photoFailure(_ info: [AnyHashable: Any]?, network: Bool) -> ExportFailure {
        if (info?[PHImageCancelledKey] as? Bool) == true { return .cancelled }
        if !network && (info?[PHImageResultIsInCloudKey] as? Bool) == true { return .cloudRequired }
        if !network, let error = info?[PHImageErrorKey] as? NSError,
           error.domain == PHPhotosErrorDomain, error.code == PHPhotosError.Code.networkAccessRequired.rawValue { return .cloudRequired }
        return .unavailable
    }

    private func transcode(_ source: ExportVideo, role: ExportRole, stage: ExportStaging) async throws -> ExportComponent {
        let seconds = try await source.asset.load(.duration).seconds
        guard seconds.isFinite, seconds > 0, seconds <= 300 else { throw ExportFailure.limitExceeded }
        let audio = try await source.asset.loadTracks(withMediaType: .audio)
        guard let exporter = AVAssetExportSession(asset: source.asset, presetName: AVAssetExportPreset1920x1080),
              exporter.supportedFileTypes.contains(.mp4) else { throw ExportFailure.unsupported }
        let output = stage.newFile(extension: "mp4")
        let limit = try stage.allowance(componentLimit)
        exporter.fileLengthLimit = limit
        exporter.audioMix = source.audioMix
        exporter.metadata = []
        exporter.shouldOptimizeForNetworkUse = true
        let cancellation = ExportCancellation(session: exporter)
        try await withTaskCancellationHandler {
            try await exporter.export(to: output, as: .mp4)
        } onCancel: { cancellation.session.cancelExport() }
        try Task.checkCancellation()
        try stage.protect(output)
        guard try stage.size(output) <= limit else { throw ExportFailure.limitExceeded }
        let final = AVURLAsset(url: output)
        let duration = try await final.load(.duration).seconds
        let tracks = try await final.loadTracks(withMediaType: .video)
        let finalAudio = try await final.loadTracks(withMediaType: .audio)
        guard let track = tracks.first, tracks.count == 1,
              duration.isFinite, abs(duration - seconds) <= 0.5,
              audio.isEmpty || !finalAudio.isEmpty else { throw ExportFailure.unsupported }
        let formats = try await track.load(.formatDescriptions)
        guard !formats.isEmpty, formats.allSatisfy({ CMFormatDescriptionGetMediaSubType($0) == kCMVideoCodecType_H264 }) else { throw ExportFailure.unsupported }
        let size = try await track.load(.naturalSize)
        guard size.width.isFinite, size.height.isFinite, abs(size.width) > 0,
              abs(size.height) > 0, max(abs(size.width), abs(size.height)) <= 1920 else { throw ExportFailure.unsupported }
        return try component(output, role: role, type: "video/mp4", width: Int(abs(size.width)), height: Int(abs(size.height)), duration: duration, audio: !finalAudio.isEmpty)
    }

    private func component(_ file: URL, role: ExportRole, type: String, width: Int, height: Int, duration: Double?, audio: Bool) throws -> ExportComponent {
        let handle = try FileHandle(forReadingFrom: file); defer { try? handle.close() }
        var hash = SHA256(); var bytes: Int64 = 0
        while let chunk = try handle.read(upToCount: 1024 * 1024), !chunk.isEmpty {
            try Task.checkCancellation(); bytes += Int64(chunk.count)
            guard bytes <= componentLimit else { throw ExportFailure.limitExceeded }; hash.update(data: chunk)
        }
        guard bytes > 0 else { throw ExportFailure.unavailable }
        return .init(role: role, filename: file.lastPathComponent, byteCount: bytes,
            sha256: hash.finalize().map { String(format: "%02x", $0) }.joined(), contentType: type,
            pixelWidth: width, pixelHeight: height, duration: duration, hasAudio: audio)
    }
}

@MainActor
private final class ExportStaging {
    let jobID = UUID().uuidString
    let root: URL
    let job: URL
    let maximum: Int64
    init(maximum: Int64) throws {
        self.maximum = maximum
        let manager = FileManager.default
        let home = URL(fileURLWithPath: NSHomeDirectory()).resolvingSymlinksInPath().path + "/"
        root = manager.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0].appendingPathComponent("SafeMemoryProbe/Exports", isDirectory: true)
        guard root.resolvingSymlinksInPath().path.hasPrefix(home) else { throw ExportFailure.restricted }
        // Reject existing app-owned path aliases before creating or protecting anything.
        for candidate in [root.deletingLastPathComponent().deletingLastPathComponent(), root.deletingLastPathComponent(), root] {
            if let attributes = try? manager.attributesOfItem(atPath: candidate.path) {
                guard attributes[.type] as? FileAttributeType == .typeDirectory else { throw ExportFailure.restricted }
            }
        }
        if manager.fileExists(atPath: root.path) {
            guard try manager.contentsOfDirectory(atPath: root.path).count < 64 else { throw ExportFailure.limitExceeded }
        }
        job = root.appendingPathComponent(jobID, isDirectory: true)
        try manager.createDirectory(at: job, withIntermediateDirectories: true, attributes: [.posixPermissions: 0o700, .protectionKey: FileProtectionType.complete])
        try protect(root); try protect(job)
        _ = try allowance(1)
    }
    func newFile(extension ext: String) -> URL { job.appendingPathComponent(UUID().uuidString).appendingPathExtension(ext) }
    func size(_ url: URL) throws -> Int64 { (try FileManager.default.attributesOfItem(atPath: url.path)[.size] as? NSNumber)?.int64Value ?? 0 }
    func protect(_ url: URL) throws {
        let directory = try url.resourceValues(forKeys: [.isDirectoryKey, .isSymbolicLinkKey])
        guard directory.isSymbolicLink != true else { throw ExportFailure.restricted }
        try FileManager.default.setAttributes([.posixPermissions: directory.isDirectory == true ? 0o700 : 0o600, .protectionKey: FileProtectionType.complete], ofItemAtPath: url.path)
        var resource = URLResourceValues(); resource.isExcludedFromBackup = true
        var mutable = url; try mutable.setResourceValues(resource)
    }
    func allowance(_ requested: Int64) throws -> Int64 {
        var budget = ExportBudget(limit: maximum)
        guard let files = FileManager.default.enumerator(at: root, includingPropertiesForKeys: [.isRegularFileKey, .isSymbolicLinkKey, .fileSizeKey]) else { throw ExportFailure.failed }
        for case let url as URL in files {
            let values = try url.resourceValues(forKeys: [.isRegularFileKey, .isSymbolicLinkKey, .fileSizeKey])
            guard values.isSymbolicLink != true else { throw ExportFailure.restricted }
            if values.isRegularFile == true { try budget.reserve(Int64(values.fileSize ?? 0)) }
        }
        guard budget.remaining > 0 else { throw ExportFailure.limitExceeded }
        return min(requested, budget.remaining)
    }
}

private final class ExportSpool: @unchecked Sendable {
    private let lock = NSLock()
    private var handle: FileHandle?
    private var budget: ExportBudget
    init(output: URL, maximum: Int64) throws {
        budget = ExportBudget(limit: maximum)
        guard FileManager.default.createFile(atPath: output.path, contents: nil, attributes: [.posixPermissions: 0o600, .protectionKey: FileProtectionType.complete]) else { throw ExportFailure.failed }
        handle = try FileHandle(forWritingTo: output)
    }
    func append(_ data: Data) throws {
        lock.lock(); defer { lock.unlock() }
        guard let handle else { throw ExportFailure.cancelled }
        try budget.reserve(Int64(data.count)); try handle.write(contentsOf: data)
    }
    func close() { lock.lock(); defer { lock.unlock() }; try? handle?.close(); handle = nil }
    deinit { try? handle?.close() }
}
