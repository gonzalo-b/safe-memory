import Foundation

struct MediaTransport: MediaServicing {
    struct Begin: Encodable {
        let device_id: String; let asset_id: String; let source_revision: String
        let role: String; let mime: String; let size: Int; let sha256: String; let request_key: String
    }
    struct Chunk: Encodable { let device_id: String; let upload_id: String; let offset: Int; let data_base64: String }
    struct Complete: Encodable { let device_id: String; let upload_id: String }
    private func send<T: Encodable, R: Decodable>(_ path: String, body: T, identity: PairingIdentity, result: R.Type) async throws -> R {
        let request = try NativeRequests.make(path, body: body, credential: identity.credential)
        let data = try await PairingTransfer().perform(request, mode: .metadata)
        return try JSONDecoder().decode(R.self, from: data)
    }
    func begin(_ local: PairingIdentity, upload: MediaUpload) async throws -> MediaBegin {
        guard let device = local.claimID else { throw PairingFailure.unauthorized }
        return try await send("/api/device/media/begin", body: Begin(device_id: device, asset_id: upload.assetID, source_revision: upload.sourceRevision,
            role: upload.role, mime: upload.mime, size: upload.size, sha256: upload.sha256, request_key: upload.requestKey), identity: local, result: MediaBegin.self)
    }
    func chunk(_ local: PairingIdentity, uploadID: String, offset: Int, data: Data) async throws -> MediaChunk {
        guard let device = local.claimID, (1...MediaJob.chunkSize).contains(data.count), offset >= 0 else { throw PairingFailure.invalidInput }
        return try await send("/api/device/media/chunk", body: Chunk(device_id: device, upload_id: uploadID, offset: offset,
            data_base64: data.base64EncodedString()), identity: local, result: MediaChunk.self)
    }
    func complete(_ local: PairingIdentity, upload: MediaUpload) async throws -> MediaComplete {
        guard let device = local.claimID, let uploadID = upload.uploadID else { throw PairingFailure.unauthorized }
        return try await send("/api/device/media/complete", body: Complete(device_id: device, upload_id: uploadID), identity: local, result: MediaComplete.self)
    }
}
