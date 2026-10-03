import Foundation
@preconcurrency import Photos

/// Exact public resource bytes; never an image request or AV transcode.
@MainActor struct OriginalPhotoExporter: OriginalExporting {
    let files: OriginalFiles
    private func current(_ job: OriginalJob) throws -> PHAsset {
        let permission = PhotosReader.authorizationName(PHPhotoLibrary.authorizationStatus(for: .readWrite))
        guard permission == job.scope.permission else { throw OriginalFailure.permission_changed }
        let options = PHFetchOptions(); options.includeHiddenAssets = job.scope.consent.includeHidden
        options.includeAllBurstAssets = true; options.includeAssetSourceTypes = [.typeUserLibrary, .typeCloudShared, .typeiTunesSynced]
        let result = PHAsset.fetchAssets(withLocalIdentifiers: [job.request.native_id], options: options)
        guard result.count == 1, let asset = result.firstObject else { throw OriginalFailure.source_unavailable }
        let row = try ImportAsset(PhotosReader.describe(asset))
        guard row.sourceRevision == job.request.source_revision, !row.hidden || job.scope.consent.includeHidden,
              job.scope.consent.includeSharedLibrary && job.scope.consent.includeSharedAlbums else { throw OriginalFailure.revision_changed }
        return asset
    }
    func export(_ job: OriginalJob) async throws -> [OriginalComponent] {
        try job.validate(); try Task.checkCancellation()
        let selected = try OriginalPolicy.select(job.scope.asset.metadata.resources, media: job.request.media_type)
        var result: [OriginalComponent] = [], remaining = OriginalPolicy.maximum
        for descriptor in selected {
            try Task.checkCancellation()
            let asset = try current(job)
            let matches = PHAssetResource.assetResources(for: asset).filter {
                $0.type.rawValue == descriptor.role && $0.originalFilename == descriptor.originalFilename &&
                $0.uniformTypeIdentifier == descriptor.uniformTypeIdentifier && $0.assetLocalIdentifier == descriptor.assetLocalIdentifier &&
                $0.pixelWidth == descriptor.pixelWidth && $0.pixelHeight == descriptor.pixelHeight
            }
            guard matches.count == 1, let resource = matches.first else { throw OriginalFailure.unsupported_resource }
            let spool = try files.newSpool(jobID: job.id, limit: remaining)
            do {
                try await stream(resource, spool: spool, cloud: job.allowICloud)
                let component = try spool.finish(descriptor)
                _ = try current(job); try Task.checkCancellation()
                try files.validate(component, jobID: job.id)
                result.append(component); remaining -= component.descriptor.size
            } catch { spool.cancel(); throw error }
        }
        _ = try current(job)
        try OriginalPolicy.validate(result.map(\.descriptor), media: job.request.media_type)
        return result
    }
    private func stream(_ resource: PHAssetResource, spool: OriginalSpool, cloud: Bool) async throws {
        let bridge = ExportRequestBridge<Bool>(), manager = PHAssetResourceManager.default()
        let deadline = Task {
            do { try await Task.sleep(for: .seconds(300)); bridge.cancel(OriginalFailure.source_unavailable) }
            catch { /* Normal completion cancels the bounded resource timer. */ }
        }
        defer { deadline.cancel() }
        _ = try await withTaskCancellationHandler {
            try await withCheckedThrowingContinuation { continuation in
                bridge.install(continuation)
                let options = PHAssetResourceRequestOptions(); options.isNetworkAccessAllowed = cloud
                let request = manager.requestData(for: resource, options: options) { bytes in
                    do { try spool.append(bytes) } catch { bridge.cancel(error) }
                } completionHandler: { error in
                    if let error {
                        let native = error as NSError
                        let unavailable: OriginalFailure = !cloud && native.domain == PHPhotosErrorDomain && native.code == PHPhotosError.Code.networkAccessRequired.rawValue ? .icloud_unavailable : .source_unavailable
                        bridge.finish(.failure(unavailable))
                    } else { bridge.finish(.success(true)) }
                }
                bridge.onCancel { spool.cancel(); manager.cancelDataRequest(request) }
            }
        } onCancel: { bridge.cancel(); spool.cancel() }
    }
}
