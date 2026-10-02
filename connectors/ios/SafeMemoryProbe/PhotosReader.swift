import Foundation
import Photos

enum ProbeFailure: Error { case permissionRequired, permissionChanged, hiddenResult, invalidLimit }

// Shared metadata adapter. No resource downloads or Photo Library writes.
struct PhotosReader {
    static func authorizationName(_ status: PHAuthorizationStatus) -> String {
        switch status {
        case .notDetermined: return "not_determined"
        case .restricted: return "restricted"
        case .denied: return "denied"
        case .authorized: return "full"
        case .limited: return "limited"
        @unknown default: return "unknown"
        }
    }

    static func snapshot(installationID: String, limit: Int = 50) throws -> ProbeManifest {
        guard (1...100).contains(limit) else { throw ProbeFailure.invalidLimit }
        try Task.checkCancellation()
        let permission = PHPhotoLibrary.authorizationStatus(for: .readWrite)
        guard permission == .authorized || permission == .limited else {
            throw ProbeFailure.permissionRequired
        }
        let options = PHFetchOptions()
        options.fetchLimit = limit
        options.includeHiddenAssets = false
        // userLibrary does NOT prove personal vs iCloud Shared Library origin.
        options.includeAssetSourceTypes = [.typeUserLibrary]
        options.sortDescriptors = [NSSortDescriptor(key: "creationDate", ascending: false)]
        options.predicate = NSPredicate(format: "mediaType == %d OR mediaType == %d", PHAssetMediaType.image.rawValue, PHAssetMediaType.video.rawValue)
        let fetched = PHAsset.fetchAssets(with: options)
        var assets: [ProbeAsset] = []
        for index in 0..<min(fetched.count, limit) {
            try Task.checkCancellation()
            guard PHPhotoLibrary.authorizationStatus(for: .readWrite) == permission else {
                throw ProbeFailure.permissionChanged
            }
            let asset = fetched.object(at: index)
            guard !asset.isHidden else { throw ProbeFailure.hiddenResult }
            assets.append(describe(asset))
        }
        guard PHPhotoLibrary.authorizationStatus(for: .readWrite) == permission else {
            throw ProbeFailure.permissionChanged
        }
        return ProbeManifest(probeInstallationID: installationID,
            authorization: authorizationName(permission), requestedLimit: limit, assets: assets)
    }

    static func selected(installationID: String, ids: [String], consent: ImportConsent) throws -> ProbeManifest {
        guard (1...100).contains(ids.count), Set(ids).count == ids.count else { throw ProbeFailure.invalidLimit }
        guard consent.includeSharedLibrary && consent.includeSharedAlbums else { throw ImportFailure.consentRequired }
        try Task.checkCancellation()
        let permission = PHPhotoLibrary.authorizationStatus(for: .readWrite)
        guard permission == .authorized || permission == .limited else { throw ProbeFailure.permissionRequired }
        let options = PHFetchOptions(); options.includeHiddenAssets = consent.includeHidden
        options.includeAllBurstAssets = true
        options.includeAssetSourceTypes = consent.includeSharedAlbums ? [.typeUserLibrary, .typeCloudShared, .typeiTunesSynced] : [.typeUserLibrary, .typeiTunesSynced]
        options.fetchLimit = ids.count
        let fetched = PHAsset.fetchAssets(withLocalIdentifiers: ids, options: options)
        guard fetched.count == ids.count else { throw ProbeFailure.permissionChanged }
        var rows: [ProbeAsset] = []
        for index in 0..<fetched.count {
            try Task.checkCancellation()
            guard PHPhotoLibrary.authorizationStatus(for: .readWrite) == permission else { throw ProbeFailure.permissionChanged }
            let asset = fetched.object(at: index)
            guard !asset.isHidden || consent.includeHidden else { throw ProbeFailure.hiddenResult }
            rows.append(describe(asset))
        }
        guard PHPhotoLibrary.authorizationStatus(for: .readWrite) == permission else { throw ProbeFailure.permissionChanged }
        return ProbeManifest(probeInstallationID: installationID, authorization: authorizationName(permission), requestedLimit: ids.count, assets: rows)
    }

    static func describe(_ asset: PHAsset) -> ProbeAsset {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        func instant(_ value: Date?) -> String? { value.map { formatter.string(from: $0) } }
        var unavailable = [
            "capture_offset": "not_exposed_by_phasset",
            "capture_local_date": "requires_source_timezone_evidence",
            "cloud_identifier": "not_requested_by_metadata_probe",
            "people": "not_exposed_by_public_api",
            "collection_provenance": "shared_library_separation_unverified",
            "media_bytes": "not_requested_by_metadata_probe",
            "captureOffset": "unknown_not_encoded_as_capture_timezone"
        ]
        if asset.creationDate == nil { unavailable["creationInstant"] = "not_exposed_for_asset" }
        if asset.modificationDate == nil { unavailable["modificationInstant"] = "not_exposed_for_asset" }
        if asset.location == nil { unavailable["location"] = "not_exposed_for_asset" }
        var addedInstant: String?
        if #available(iOS 26.0, *) { addedInstant = instant(asset.addedDate) }
        else { unavailable["addedInstant"] = "not_available_on_this_os" }
        let location = asset.location.map { point in
            ProbeLocation(latitude: point.coordinate.latitude, longitude: point.coordinate.longitude,
                altitude: point.altitude, horizontalAccuracy: point.horizontalAccuracy,
                verticalAccuracy: point.verticalAccuracy, timestampInstant: formatter.string(from: point.timestamp),
                speed: point.speed, course: point.course, speedAccuracy: point.speedAccuracy,
                courseAccuracy: point.courseAccuracy, ellipsoidalAltitude: point.ellipsoidalAltitude,
                isSimulatedBySoftware: point.sourceInformation?.isSimulatedBySoftware,
                isProducedByAccessory: point.sourceInformation?.isProducedByAccessory)
        }
        let resources = PHAssetResource.assetResources(for: asset).map { resource in
            ProbeResource(role: resource.type.rawValue, assetLocalIdentifier: resource.assetLocalIdentifier,
                originalFilename: resource.originalFilename, uniformTypeIdentifier: resource.uniformTypeIdentifier,
                pixelWidth: resource.pixelWidth, pixelHeight: resource.pixelHeight)
        }.sorted {
            ($0.role, $0.assetLocalIdentifier, $0.originalFilename, $0.uniformTypeIdentifier, $0.pixelWidth, $0.pixelHeight) <
            ($1.role, $1.assetLocalIdentifier, $1.originalFilename, $1.uniformTypeIdentifier, $1.pixelWidth, $1.pixelHeight)
        }
        return ProbeAsset(localIdentifier: asset.localIdentifier,
            creationInstant: instant(asset.creationDate), modificationInstant: instant(asset.modificationDate),
            addedInstant: addedInstant, mediaType: asset.mediaType.rawValue,
            mediaSubtypes: asset.mediaSubtypes.rawValue, pixelWidth: asset.pixelWidth,
            pixelHeight: asset.pixelHeight, duration: asset.duration,
            isHidden: asset.isHidden, isFavorite: asset.isFavorite, sourceType: asset.sourceType.rawValue,
            location: location, burstIdentifier: asset.burstIdentifier,
            burstSelectionTypes: asset.burstSelectionTypes.rawValue, representsBurst: asset.representsBurst,
            hasAdjustments: asset.hasAdjustments, adjustmentFormatIdentifier: asset.adjustmentFormatIdentifier,
            resources: resources, unavailable: unavailable)
    }
}
