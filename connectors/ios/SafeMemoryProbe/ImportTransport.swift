import Foundation

struct ImportTransport: ImportServicing {
    struct Permission: Encodable { let device_id: String; let permission: String }
    struct Begin: Encodable { let device_id: String; let request_key: String; let permission: String; let phase: String; let selected_ids: [String] }
    struct Append: Encodable { let device_id: String; let run_id: String; let batch_key: String; let sequence: Int; let checkpoint: String; let assets: [ImportAsset] }
    struct Finish: Encodable { let device_id: String; let run_id: String }
    struct OK: Decodable { let ok: Bool }
    func authenticate(_ identity: PairingIdentity) async throws {
        guard let id = identity.claimID else { throw PairingFailure.unauthorized }
        _ = try await PairingTransport().status(deviceID: id, credential: identity.credential)
    }
    private func send<T: Encodable, R: Decodable>(_ path: String, body: T, identity: PairingIdentity, result: R.Type) async throws -> R {
        let request = try NativeRequests.make(path, body: body, credential: identity.credential)
        let data = try await PairingTransfer().perform(request, mode: .metadata)
        return try JSONDecoder().decode(R.self, from: data)
    }
    func permission(_ identity: PairingIdentity, value: String) async throws {
        guard let id = identity.claimID, ["full", "limited", "denied", "revoked"].contains(value) else { throw PairingFailure.invalidInput }
        let result = try await send("/api/device/permission", body: Permission(device_id: id, permission: value), identity: identity, result: OK.self)
        guard result.ok else { throw ImportFailure.invalidReceipt }
    }
    func begin(_ identity: PairingIdentity, checkpoint: ImportCheckpoint) async throws -> ImportBegin {
        try await send("/api/device/ingest/begin", body: Begin(device_id: checkpoint.deviceID, request_key: checkpoint.jobID,
            permission: checkpoint.selection.permission, phase: "recent", selected_ids: checkpoint.selection.ids), identity: identity, result: ImportBegin.self)
    }
    func append(_ identity: PairingIdentity, checkpoint: ImportCheckpoint, runID: String) async throws -> ImportReceipt {
        try await send("/api/device/ingest/append", body: Append(device_id: checkpoint.deviceID, run_id: runID, batch_key: checkpoint.batchKey,
            sequence: 0, checkpoint: "bounded-sample:" + checkpoint.jobID, assets: checkpoint.selection.assets), identity: identity, result: ImportReceipt.self)
    }
    func finish(_ identity: PairingIdentity, runID: String) async throws -> ImportFinish {
        guard let id = identity.claimID else { throw PairingFailure.unauthorized }
        return try await send("/api/device/ingest/finish", body: Finish(device_id: id, run_id: runID), identity: identity, result: ImportFinish.self)
    }
}
