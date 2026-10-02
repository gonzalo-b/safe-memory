import Foundation

enum ExportFailure: String, Error, Codable, Sendable {
    case invalidSelection, restricted, unavailable, cloudRequired, unsupported
    case limitExceeded, cancelled, timedOut, failed, busy
}

enum ExportRole: String, Codable, Sendable { case photo, video, cover, motion }
enum ExportMedia: String, Codable, Sendable {
    case photo, video, live
    var requiredRoles: [ExportRole] {
        switch self { case .photo: return [.photo]; case .video: return [.video]; case .live: return [.cover, .motion] }
    }
    func isComplete(_ roles: [ExportRole]) -> Bool {
        roles.count == requiredRoles.count && Set(roles) == Set(requiredRoles)
    }
}

struct ExportConsent: Sendable {
    var includeHidden = false
    var includeSharedAlbums = false
    var includeSharedLibrary = false
    var allowICloud = false
}

struct ExportAssetScope: Sendable {
    let id: String
    let hidden: Bool
    let sharedAlbum: Bool
    let collection: String
    let media: ExportMedia
}

struct ExportPlan: Sendable {
    let assets: [ExportAssetScope]
    init(selectedIDs: [String], authorized: [ExportAssetScope], consent: ExportConsent) throws {
        guard (1...100).contains(selectedIDs.count), Set(selectedIDs).count == selectedIDs.count,
              selectedIDs.allSatisfy({ !$0.isEmpty }) else { throw ExportFailure.invalidSelection }
        var selected: [ExportAssetScope] = []
        for id in selectedIDs {
            let matches = authorized.filter { $0.id == id }
            guard matches.count == 1, let asset = matches.first else { throw ExportFailure.restricted }
            guard !asset.hidden || consent.includeHidden,
                  !asset.sharedAlbum || consent.includeSharedAlbums else { throw ExportFailure.restricted }
            // Unknown can include Shared Library. It is never silently personal.
            guard asset.collection == "personal" ||
                  (["shared_library", "unknown"].contains(asset.collection) && consent.includeSharedLibrary) ||
                  (asset.collection == "shared_album" && asset.sharedAlbum && consent.includeSharedAlbums)
            else { throw ExportFailure.restricted }
            selected.append(asset)
        }
        assets = selected
    }
}

struct ExportDimensions: Equatable, Sendable {
    let width: Int
    let height: Int
    static func fit(width: Int, height: Int) -> Self? {
        guard width > 0, height > 0 else { return nil }
        let scale = min(1.0, 2048.0 / Double(max(width, height)))
        return Self(width: max(1, Int(Double(width) * scale)), height: max(1, Int(Double(height) * scale)))
    }
}

struct ExportBudget: Sendable {
    let limit: Int64
    private(set) var used: Int64 = 0
    var remaining: Int64 { limit - used }
    mutating func reserve(_ bytes: Int64) throws {
        guard bytes >= 0, bytes <= remaining else { throw ExportFailure.limitExceeded }
        used += bytes
    }
}

struct ExportComponent: Codable, Sendable {
    let role: ExportRole
    let filename: String
    let byteCount: Int64
    let sha256: String
    let contentType: String
    let pixelWidth: Int
    let pixelHeight: Int
    let duration: Double?
    let hasAudio: Bool
}

struct ExportAssetResult: Codable, Sendable {
    let localIdentifier: String
    let state: String
    let components: [ExportComponent]
    let reason: ExportFailure?
}

struct ExportBatchResult: Encodable, Sendable {
    let jobID: String
    let assets: [ExportAssetResult]
    // Filenames are opaque, app-relative, never source paths or upload URLs.
    let disclosure: String = "private_staging_only"
}
