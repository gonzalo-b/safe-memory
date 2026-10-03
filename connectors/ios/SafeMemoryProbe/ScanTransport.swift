import Foundation

struct ScanTransport: ScanServicing {
    struct Begin: Encodable {
        let device_id: String; let request_key: String; let permission: String; let expected_count: Int
        let include_hidden: Bool; let include_shared_library: Bool; let include_shared_albums: Bool
    }
    struct Append: Encodable {
        let device_id: String; let run_id: String; let batch_key: String; let sequence: Int
        let checkpoint: String; let phase: String; let assets: [ImportAsset]
    }
    private func send<T: Encodable, R: Decodable>(_ path: String, body: T, local: PairingIdentity, result: R.Type) async throws -> R {
        let request = try NativeRequests.make(path, body: body, credential: local.credential)
        return try JSONDecoder().decode(R.self, from: await PairingTransfer().perform(request, mode: .metadata))
    }
    func permission(_ local: PairingIdentity, value: String) async throws { try await ImportTransport().permission(local, value: value) }
    func begin(_ local: PairingIdentity, state: ScanState) async throws -> ScanBegin {
        guard let snapshot = state.snapshot else { throw ScanFailure.snapshotUnavailable }
        return try await send("/api/device/scan/begin", body: Begin(device_id: state.deviceID, request_key: state.id, permission: state.permission,
            expected_count: snapshot.expectedCount, include_hidden: state.consent.includeHidden, include_shared_library: state.consent.includeSharedLibrary,
            include_shared_albums: state.consent.includeSharedAlbums), local: local, result: ScanBegin.self)
    }
    func append(_ local: PairingIdentity, state: ScanState, page: ScanPage) async throws -> ScanReceipt {
        guard let run = state.runID else { throw ScanFailure.invalidReceipt }
        return try await send("/api/device/scan/append", body: Append(device_id: state.deviceID, run_id: run, batch_key: page.id, sequence: page.sequence,
            checkpoint: page.checkpoint, phase: page.phase, assets: page.assets), local: local, result: ScanReceipt.self)
    }
    func finish(_ local: PairingIdentity, state: ScanState) async throws -> ScanFinish {
        guard let run = state.runID else { throw ScanFailure.invalidReceipt }
        return try await send("/api/device/scan/finish", body: ImportTransport.Finish(device_id: state.deviceID, run_id: run), local: local, result: ScanFinish.self)
    }
}
