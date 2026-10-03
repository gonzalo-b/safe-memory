import Foundation

struct OriginalRequest: Codable, Sendable, Equatable {
    let request_id: String; let asset_id: String; let native_id: String; let source_revision: String; let media_type: String; let state: String
    func validate() throws {
        guard PairingRequests.identifier(request_id), PairingRequests.identifier(asset_id), PairingRequests.text(native_id, maximum: 256),
              source_revision.range(of: "^[a-f0-9]{64}$", options: .regularExpression) != nil,
              ["photo", "video", "live"].contains(media_type), ["waiting_for_device", "transferring"].contains(state) else { throw OriginalFailure.invalidReceipt }
    }
}
struct OriginalScope: Codable, Sendable {
    let deviceID: String; let libraryID: String; let fingerprint: String; let scopeID: String; let permission: String
    let consent: ImportConsent; let asset: ImportAsset
    func matches(_ other: Self) -> Bool {
        deviceID == other.deviceID && libraryID == other.libraryID && fingerprint == other.fingerprint && scopeID == other.scopeID &&
        permission == other.permission && consent == other.consent && asset.sourceRevision == other.asset.sourceRevision && asset.nativeID == other.asset.nativeID
    }
}
struct OriginalComponent: Codable, Sendable {
    let descriptor: OriginalDescriptor; let filename: String
    var uploadID: String?; var offset = 0; var componentID: String?
}
enum OriginalStage: String, Codable, Sendable { case staging, transferring, ready, failed, revocationPending, revoked }
struct OriginalJob: Codable, Sendable {
    let id: String; let request: OriginalRequest; let scope: OriginalScope; let allowICloud: Bool
    var stage: OriginalStage = .staging
    var components: [OriginalComponent] = []
    var error: String?
    func validate() throws {
        try request.validate()
        guard UUID(uuidString: id) != nil, UUID(uuidString: scope.scopeID) != nil,
              PairingRequests.identifier(scope.deviceID), PairingRequests.identifier(scope.libraryID),
              scope.fingerprint.range(of: "^[a-f0-9]{64}$", options: .regularExpression) != nil,
              ["full", "limited"].contains(scope.permission), scope.consent.includeSharedLibrary && scope.consent.includeSharedAlbums,
              !scope.asset.hidden || scope.consent.includeHidden,
              scope.asset.nativeID == request.native_id, scope.asset.sourceRevision == request.source_revision, scope.asset.mediaType == request.media_type,
              try ImportAsset(scope.asset.metadata).sourceRevision == request.source_revision else { throw OriginalFailure.integrity }
        if !components.isEmpty {
            try OriginalPolicy.validate(components.map(\.descriptor), media: request.media_type)
            let selected = try OriginalPolicy.select(scope.asset.metadata.resources, media: request.media_type)
            guard selected.count == components.count, Set(components.map(\.filename)).count == components.count else { throw OriginalFailure.integrity }
            for (row, component) in zip(selected, components) {
                guard component.descriptor.resource_type == OriginalPolicy.roles[row.role], component.descriptor.original_filename == row.originalFilename,
                      component.descriptor.uniform_type_identifier == row.uniformTypeIdentifier, UUID(uuidString: component.filename) != nil,
                      (0...component.descriptor.size).contains(component.offset),
                      component.uploadID == nil || PairingRequests.identifier(component.uploadID!),
                      component.componentID == nil || (PairingRequests.identifier(component.componentID!) && component.offset == component.descriptor.size && component.uploadID != nil)
                else { throw OriginalFailure.integrity }
            }
        }
        if [.transferring, .ready].contains(stage) { guard !components.isEmpty else { throw OriginalFailure.integrity } }
        if stage == .ready { guard components.allSatisfy({ $0.componentID != nil }) else { throw OriginalFailure.integrity } }
    }
}
struct OriginalPending: Codable, Sendable { let requests: [OriginalRequest] }
struct OriginalBegin: Codable, Sendable {
    struct Resource: Codable, Sendable { let ordinal: Int; let upload_id: String; let next_offset: Int; let state: String }
    let request_id: String; let state: String; let resources: [Resource]
}
struct OriginalChunk: Codable, Sendable { let upload_id: String; let next_offset: Int; let state: String }
struct OriginalComplete: Codable, Sendable { let request_id: String; let upload_id: String; let component_id: String; let state: String }
@MainActor protocol OriginalSource {
    func identity() throws -> PairingIdentity
    func scope(_ request: OriginalRequest) async throws -> OriginalScope
    func revoke() async throws
}
@MainActor protocol OriginalStoring {
    func load() throws -> OriginalJob?
    func save(_ job: OriginalJob) throws
}
@MainActor protocol OriginalFileReading {
    func validate(_ component: OriginalComponent, jobID: String) throws
    func read(_ component: OriginalComponent, jobID: String, offset: Int, count: Int) throws -> Data
}
@MainActor protocol OriginalExporting { func export(_ job: OriginalJob) async throws -> [OriginalComponent] }
protocol OriginalServicing: Sendable {
    func pending(_ identity: PairingIdentity) async throws -> OriginalPending
    func begin(_ identity: PairingIdentity, job: OriginalJob) async throws -> OriginalBegin
    func chunk(_ identity: PairingIdentity, uploadID: String, offset: Int, data: Data) async throws -> OriginalChunk
    func complete(_ identity: PairingIdentity, uploadID: String) async throws -> OriginalComplete
    func fail(_ identity: PairingIdentity, requestID: String, reason: String) async throws
}
