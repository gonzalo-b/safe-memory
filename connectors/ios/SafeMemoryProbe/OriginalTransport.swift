import Foundation

struct OriginalTransport: OriginalServicing {
    struct Pending: Encodable { let device_id: String }
    struct Begin: Encodable { let device_id: String; let request_id: String; let resources: [OriginalDescriptor] }
    struct Chunk: Encodable { let device_id: String; let upload_id: String; let offset: Int; let data: String }
    struct Complete: Encodable { let device_id: String; let upload_id: String }
    struct Fail: Encodable { let device_id: String; let request_id: String; let reason: String }
    private func send<T: Encodable>(_ path: String, body: T, identity: PairingIdentity) async throws -> Data {
        let request = try NativeRequests.make("/api/device/originals/" + path, body: body, credential: identity.credential)
        return try await PairingTransfer().perform(request, mode: .metadata)
    }
    private func device(_ identity: PairingIdentity) throws -> String {
        try identity.validate(); guard let device = identity.claimID else { throw PairingFailure.unauthorized }; return device
    }
    func pending(_ identity: PairingIdentity) async throws -> OriginalPending {
        try await JSONDecoder().decode(OriginalPending.self, from: send("pending", body: Pending(device_id: device(identity)), identity: identity))
    }
    func begin(_ identity: PairingIdentity, job: OriginalJob) async throws -> OriginalBegin {
        try await JSONDecoder().decode(OriginalBegin.self, from: send("begin", body: Begin(device_id: device(identity), request_id: job.request.request_id, resources: job.components.map(\.descriptor)), identity: identity))
    }
    func chunk(_ identity: PairingIdentity, uploadID: String, offset: Int, data: Data) async throws -> OriginalChunk {
        guard (1...OriginalPolicy.chunkSize).contains(data.count) else { throw PairingFailure.bodyLimit }
        return try await JSONDecoder().decode(OriginalChunk.self, from: send("chunk", body: Chunk(device_id: device(identity), upload_id: uploadID, offset: offset, data: data.base64EncodedString()), identity: identity))
    }
    func complete(_ identity: PairingIdentity, uploadID: String) async throws -> OriginalComplete {
        try await JSONDecoder().decode(OriginalComplete.self, from: send("complete", body: Complete(device_id: device(identity), upload_id: uploadID), identity: identity))
    }
    func fail(_ identity: PairingIdentity, requestID: String, reason: String) async throws {
        guard OriginalFailure(rawValue: reason)?.serverReason != nil else { throw PairingFailure.invalidInput }
        _ = try await send("fail", body: Fail(device_id: device(identity), request_id: requestID, reason: reason), identity: identity)
    }
}
