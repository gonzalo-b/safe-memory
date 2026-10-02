import Foundation
import CryptoKit

enum ImportFailure: Error, Sendable { case invalidSelection, consentRequired, selectionChanged, pendingRevocation, invalidReceipt, storage, busy }

struct ImportConsent: Codable, Equatable, Sendable {
    var includeHidden = false
    var includeSharedLibrary = false
    var includeSharedAlbums = false
}

struct ImportAsset: Codable, Sendable {
    let nativeID: String
    let sourceRevision: String
    let mediaType: String
    let hidden: Bool
    let collection: String
    let captureTime: String?
    let timeBasis: String
    let ownerPresence: String
    let sourceModified: String?
    let metadata: ProbeAsset
    enum CodingKeys: String, CodingKey {
        case nativeID = "native_id", sourceRevision = "source_revision", mediaType = "media_type", hidden, collection
        case captureTime = "capture_time", timeBasis = "time_basis", ownerPresence = "owner_presence", sourceModified = "source_modified", metadata
    }
    init(_ row: ProbeAsset) throws {
        guard [1, 2].contains(row.mediaType), PairingRequests.text(row.localIdentifier, maximum: 256) else { throw ImportFailure.invalidSelection }
        nativeID = row.localIdentifier; mediaType = row.mediaType == 2 ? "video" : row.mediaSubtypes & 8 != 0 ? "live" : "photo"
        hidden = row.isHidden; collection = "unknown"; ownerPresence = "unknown"
        captureTime = row.creationInstant; timeBasis = row.creationInstant == nil ? "unknown" : "instant_only"
        sourceModified = row.modificationInstant; metadata = row
        let payload = RevisionPayload(nativeID: nativeID, mediaType: mediaType, hidden: hidden, collection: collection,
            captureTime: captureTime, timeBasis: timeBasis, ownerPresence: ownerPresence, sourceModified: sourceModified, metadata: metadata)
        sourceRevision = SHA256.hash(data: try NativeJSON.encode(payload)).map { String(format: "%02x", $0) }.joined()
    }
    // Exactly the full wire wrapper without source_revision, including nulls.
    private struct RevisionPayload: Encodable {
        let nativeID: String; let mediaType: String; let hidden: Bool; let collection: String
        let captureTime: String?; let timeBasis: String; let ownerPresence: String; let sourceModified: String?; let metadata: ProbeAsset
        func encode(to encoder: Encoder) throws {
            var c = encoder.container(keyedBy: CodingKeys.self)
            try c.encode(nativeID, forKey: .nativeID); try c.encode(mediaType, forKey: .mediaType); try c.encode(hidden, forKey: .hidden)
            try c.encode(collection, forKey: .collection); try c.encode(captureTime, forKey: .captureTime); try c.encode(timeBasis, forKey: .timeBasis)
            try c.encode(ownerPresence, forKey: .ownerPresence); try c.encode(sourceModified, forKey: .sourceModified); try c.encode(metadata, forKey: .metadata)
        }
    }
    func encode(to encoder: Encoder) throws {
        var c = encoder.container(keyedBy: CodingKeys.self)
        try c.encode(nativeID, forKey: .nativeID); try c.encode(sourceRevision, forKey: .sourceRevision); try c.encode(mediaType, forKey: .mediaType)
        try c.encode(hidden, forKey: .hidden); try c.encode(collection, forKey: .collection); try c.encode(captureTime, forKey: .captureTime)
        try c.encode(timeBasis, forKey: .timeBasis); try c.encode(ownerPresence, forKey: .ownerPresence)
        try c.encode(sourceModified, forKey: .sourceModified); try c.encode(metadata, forKey: .metadata)
    }
}

struct ImportSelection: Codable, Sendable {
    let ids: [String]
    let permission: String
    let consent: ImportConsent
    let assets: [ImportAsset]
    init(ids: [String], manifest: ProbeManifest, consent: ImportConsent) throws {
        guard (1...100).contains(ids.count), Set(ids).count == ids.count, manifest.assets.count == ids.count,
              Set(manifest.assets.map(\.localIdentifier)) == Set(ids), ["full", "limited"].contains(manifest.authorization) else { throw ImportFailure.invalidSelection }
        guard consent.includeSharedLibrary && consent.includeSharedAlbums,
              consent.includeHidden || !manifest.assets.contains(where: \.isHidden) else { throw ImportFailure.consentRequired }
        self.ids = ids.sorted(); permission = manifest.authorization; self.consent = consent
        assets = try manifest.assets.sorted {
            if $0.creationInstant != $1.creationInstant { return ($0.creationInstant ?? "") > ($1.creationInstant ?? "") }
            return $0.localIdentifier < $1.localIdentifier
        }.map(ImportAsset.init)
        guard try NativeJSON.encode(assets).count < NativeRequests.appendLimit - 4096 else { throw PairingFailure.bodyLimit }
    }
    func matches(_ other: ImportSelection) -> Bool {
        ids == other.ids && permission == other.permission && consent == other.consent &&
            Dictionary(uniqueKeysWithValues: assets.map { ($0.nativeID, $0.sourceRevision) }) == Dictionary(uniqueKeysWithValues: other.assets.map { ($0.nativeID, $0.sourceRevision) })
    }
}

enum ImportStage: String, Codable, Sendable { case clearOldScope, ready, complete, revocationPending, revoked }
struct ImportCheckpoint: Codable, Sendable {
    let jobID: String
    let deviceID: String
    let libraryID: String
    let fingerprint: String
    let batchKey: String
    let selection: ImportSelection
    var stage: ImportStage = .clearOldScope
    var revokePermission: String
    var runID: String?
    var accepted: Int?
    var excluded: Int?
}

struct ImportBegin: Codable, Sendable {
    let run_id: String; let next_sequence: Int; let state: String; let coverage: String
}
struct ImportReceipt: Codable, Sendable {
    struct Asset: Codable, Sendable { let native_id: String; let asset_id: String }
    let run_id: String; let sequence: Int; let next_sequence: Int; let accepted: Int; let excluded: Int; let assets: [Asset]
}
struct ImportFinish: Codable, Sendable { let run_id: String; let state: String; let coverage: String; let media_ready: Int }

@MainActor protocol ImportCheckpointStore { func load() throws -> ImportCheckpoint?; func save(_ checkpoint: ImportCheckpoint) throws }
@MainActor protocol ImportReading { func permission() -> String; func selection(ids: [String], consent: ImportConsent) async throws -> ImportSelection }
protocol ImportServicing: Sendable {
    func authenticate(_ identity: PairingIdentity) async throws
    func permission(_ identity: PairingIdentity, value: String) async throws
    func begin(_ identity: PairingIdentity, checkpoint: ImportCheckpoint) async throws -> ImportBegin
    func append(_ identity: PairingIdentity, checkpoint: ImportCheckpoint, runID: String) async throws -> ImportReceipt
    func finish(_ identity: PairingIdentity, runID: String) async throws -> ImportFinish
}
