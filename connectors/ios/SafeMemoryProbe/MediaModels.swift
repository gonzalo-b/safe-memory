import Foundation

enum MediaFailure: Error { case invalidDescriptor, changedSample, integrity, incomplete, storage }
struct MediaUpload: Codable, Sendable {
    let nativeID: String
    let assetID: String
    let sourceRevision: String
    let role: String
    let mime: String
    let size: Int
    let sha256: String
    let exportJobID: String
    let filename: String
    let requestKey: String
    let hasAudio: Bool
    var uploadID: String?
    var offset = 0
    var componentID: String?
}
struct MediaJob: Codable, Sendable {
    let id: String
    let allowICloud: Bool
    var exported = false
    var components: [MediaUpload] = []
    var unavailable: [String: ExportFailure] = [:]
    var failureSummary: String {
        let counts = Dictionary(grouping: unavailable.values) { reason -> String in
            switch reason {
            case .cloudRequired: return "iCloud download required"
            case .unsupported: return "incompatible or incomplete"
            case .unavailable: return "not accessible"
            case .limitExceeded: return "export limit reached"
            case .restricted: return "source restricted"
            case .cancelled: return "cancelled"
            case .timedOut: return "export timed out"
            default: return "export unavailable"
            }
        }
        return counts.keys.sorted().map { "\($0): \(counts[$0]!.count)" }.joined(separator: "; ")
    }
    static let chunkSize = 1024 * 1024
    static let maximumComponent = 64 * 1024 * 1024
    static func roles(_ type: String) -> Set<String> {
        switch type { case "photo": return ["still"]; case "video": return ["video"]; case "live": return ["still", "motion"]; default: return [] }
    }
    func readyCount(_ sample: ImportCheckpoint) -> Int {
        (sample.acceptedAssets ?? []).filter { accepted in
            guard let asset = sample.selection.assets.first(where: { $0.nativeID == accepted.native_id }) else { return false }
            let ready = Set(components.filter { $0.assetID == accepted.asset_id && $0.componentID != nil }.map(\.role))
            return !Self.roles(asset.mediaType).isEmpty && Self.roles(asset.mediaType).isSubset(of: ready)
        }.count
    }
    func validate(_ sample: ImportCheckpoint) throws {
        guard UUID(uuidString: id) != nil, components.count <= 200, unavailable.count <= 100,
              exported || components.isEmpty, let accepted = sample.acceptedAssets else { throw MediaFailure.invalidDescriptor }
        var roles = Set<String>(), keys = Set<String>()
        for c in components {
            guard let row = sample.selection.assets.first(where: { $0.nativeID == c.nativeID }),
                  accepted.contains(where: { $0.native_id == c.nativeID && $0.asset_id == c.assetID }),
                  row.sourceRevision == c.sourceRevision, Self.roles(row.mediaType).contains(c.role),
                  c.mime == (c.role == "still" ? "image/jpeg" : "video/mp4"), (1...Self.maximumComponent).contains(c.size),
                  c.sha256.range(of: "^[a-f0-9]{64}$", options: .regularExpression) != nil,
                  UUID(uuidString: c.exportJobID) != nil, UUID(uuidString: c.requestKey) != nil,
                  UUID(uuidString: String(c.filename.dropLast(4))) != nil, c.filename.hasSuffix(c.role == "still" ? ".jpg" : ".mp4"),
                  !c.filename.contains("/"), (0...c.size).contains(c.offset),
                  c.uploadID == nil || PairingRequests.identifier(c.uploadID!),
                  c.offset == 0 || c.uploadID != nil,
                  c.componentID == nil || (PairingRequests.identifier(c.componentID!) && c.offset == c.size),
                  roles.insert(c.nativeID + ":" + c.role).inserted, keys.insert(c.requestKey).inserted else { throw MediaFailure.invalidDescriptor }
        }
        guard Set(unavailable.keys).isSubset(of: Set(accepted.map(\.native_id))) else { throw MediaFailure.invalidDescriptor }
    }
    mutating func retain(_ batch: ExportBatchResult, sample: ImportCheckpoint) throws {
        guard !exported, components.isEmpty, UUID(uuidString: batch.jobID) != nil, let accepted = sample.acceptedAssets,
              Set(batch.assets.map(\.localIdentifier)) == Set(accepted.map(\.native_id)), batch.assets.count == accepted.count else { throw MediaFailure.invalidDescriptor }
        for result in batch.assets {
            guard let mapping = accepted.first(where: { $0.native_id == result.localIdentifier }),
                  let asset = sample.selection.assets.first(where: { $0.nativeID == result.localIdentifier }) else { throw MediaFailure.invalidDescriptor }
            for c in result.components {
                guard c.byteCount > 0 && c.byteCount <= Self.maximumComponent else { throw MediaFailure.invalidDescriptor }
                let role = c.role == .photo || c.role == .cover ? "still" : c.role.rawValue
                components.append(MediaUpload(nativeID: asset.nativeID, assetID: mapping.asset_id, sourceRevision: asset.sourceRevision,
                    role: role, mime: c.contentType, size: Int(c.byteCount), sha256: c.sha256, exportJobID: batch.jobID,
                    filename: c.filename, requestKey: UUID().uuidString, hasAudio: c.hasAudio))
            }
            if result.state != "ready" || Set(components.filter { $0.nativeID == asset.nativeID }.map(\.role)) != Self.roles(asset.mediaType) {
                unavailable[asset.nativeID] = result.reason ?? .unsupported
            }
        }
        exported = true
        try validate(sample)
    }
}
struct MediaBegin: Codable, Sendable { let upload_id: String; let next_offset: Int; let state: String }
struct MediaChunk: Codable, Sendable { let upload_id: String; let next_offset: Int }
struct MediaComplete: Codable, Sendable { let component_id: String; let state: String; let size: Int; let mime: String }

@MainActor protocol MediaSelectionSource {
    func mediaSelection() async throws -> ImportCheckpoint
    func mediaIdentity(_ checkpoint: ImportCheckpoint) throws -> PairingIdentity
    func saveMedia(_ media: MediaJob, jobID: String) throws
}
@MainActor protocol MediaExporting { func export(_ sample: ImportCheckpoint, allowICloud: Bool) async throws -> ExportBatchResult }
@MainActor protocol MediaFileReading {
    func validate(_ upload: MediaUpload) throws
    func read(_ upload: MediaUpload, offset: Int, count: Int) throws -> Data
}
protocol MediaServicing: Sendable {
    func begin(_ local: PairingIdentity, upload: MediaUpload) async throws -> MediaBegin
    func chunk(_ local: PairingIdentity, uploadID: String, offset: Int, data: Data) async throws -> MediaChunk
    func complete(_ local: PairingIdentity, upload: MediaUpload) async throws -> MediaComplete
}
