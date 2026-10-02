import Foundation

// Local probe format only. This does not change Safe Memory's Record contract.
struct ProbeManifest: Codable, Sendable {
    let schemaVersion: Int
    let probeInstallationID: String
    let authorization: String
    let coverage: String
    let requestedLimit: Int
    let assets: [ProbeAsset]

    init(probeInstallationID: String, authorization: String, requestedLimit: Int, assets: [ProbeAsset]) {
        self.schemaVersion = 1
        self.probeInstallationID = probeInstallationID
        self.authorization = authorization
        self.coverage = "bounded_authorized_sample"
        self.requestedLimit = requestedLimit
        self.assets = assets
    }

    func serialized() throws -> Data {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys, .prettyPrinted, .withoutEscapingSlashes]
        return try encoder.encode(self)
    }
}

struct ProbeLocation: Codable, Sendable {
    let latitude: Double
    let longitude: Double
    let altitude: Double
    let horizontalAccuracy: Double
    let verticalAccuracy: Double
    let timestampInstant: String
    let speed: Double
    let course: Double
    let speedAccuracy: Double
    let courseAccuracy: Double
    let ellipsoidalAltitude: Double
    let isSimulatedBySoftware: Bool?
    let isProducedByAccessory: Bool?
}

struct ProbeResource: Codable, Sendable {
    let role: Int
    let assetLocalIdentifier: String
    let originalFilename: String
    let uniformTypeIdentifier: String
    let pixelWidth: Int
    let pixelHeight: Int
}

struct ProbeAsset: Codable, Sendable {
    let localIdentifier: String
    let creationInstant: String?
    let modificationInstant: String?
    let addedInstant: String?
    // PHAsset NSDate is an instant; UTC serialization is not the capture offset.
    var captureOffset: String? = nil
    var collectionProvenance: String = "unknown"
    var disclosure: String = "restricted_probe_only"
    let mediaType: Int
    let mediaSubtypes: UInt
    let pixelWidth: Int
    let pixelHeight: Int
    let duration: Double
    let isHidden: Bool
    let isFavorite: Bool
    let sourceType: UInt
    let location: ProbeLocation?
    let burstIdentifier: String?
    let burstSelectionTypes: UInt
    let representsBurst: Bool
    let hasAdjustments: Bool
    let adjustmentFormatIdentifier: String?
    let resources: [ProbeResource]
    let unavailable: [String: String]

    enum CodingKeys: String, CodingKey {
        case localIdentifier, creationInstant, modificationInstant, addedInstant
        case captureOffset, collectionProvenance, disclosure
        case mediaType, mediaSubtypes, pixelWidth, pixelHeight, duration
        case isHidden, isFavorite, sourceType, location, burstIdentifier
        case burstSelectionTypes, representsBurst, hasAdjustments
        case adjustmentFormatIdentifier, resources, unavailable
    }
}
