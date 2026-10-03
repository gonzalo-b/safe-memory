import Foundation
import CryptoKit

enum ScanFailure: Error { case snapshotChanged, snapshotUnavailable, invalidReceipt, capacity, storage }
struct ScanSnapshot: Codable, Sendable {
    let permission: String
    let expectedCount: Int
    let orderedIDHash: String
    let changeToken: Data
    func validate() throws {
        guard ["full", "limited"].contains(permission), (0...1_000_000).contains(expectedCount),
              orderedIDHash.range(of: "^[a-f0-9]{64}$", options: .regularExpression) != nil,
              (1...65536).contains(changeToken.count) else { throw ScanFailure.snapshotUnavailable }
    }
}
enum ScanStage: String, Codable, Sendable { case clearOldScope, freezing, indexing, complete, revocationPending, revoked }
struct ScanState: Codable, Sendable {
    let id: String
    let deviceID: String
    let libraryID: String
    let fingerprint: String
    let permission: String
    let consent: ImportConsent
    let copy: Bool
    let cloud: Bool
    var stage: ScanStage = .clearOldScope
    var snapshot: ScanSnapshot?
    var runID: String?
    var recentAfter: String?
    var nextSequence = 0
    var observed = 0
    var accepted = 0
    var excluded = 0
    var phase = "recent"
    var lastInstant: String?
    var unknownStarted = false
    var pending: ScanPage?
    var copyPage: Int?
    var lastCopyOutcome = "not_requested"
    var sourceMediaReady: Int?
    var revokePermission: String
    var coverage: String { "authorized_" + permission + "_scan" }
    var copyLabel: String {
        switch lastCopyOutcome {
        case "ready": return "last accepted page ready"
        case "partial": return "last page incomplete"
        case "capacity": return "paused by storage capacity"
        case "unavailable": return "last page unavailable; explicit retry possible"
        default: return "not requested"
        }
    }
}
struct ScanPage: Codable, Sendable {
    let id: String
    let sequence: Int
    let start: Int
    let phase: String
    let checkpoint: String
    let assets: [ImportAsset]
    static func date(_ text: String) -> Date? {
        let formatter = ISO8601DateFormatter(); formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        if let date = formatter.date(from: text) { return date }
        formatter.formatOptions = [.withInternetDateTime]; return formatter.date(from: text)
    }
    static func make(_ rows: [ImportAsset], state: ScanState) throws -> Self {
        guard let boundary = state.recentAfter.flatMap(date), !rows.isEmpty, rows.count <= 100 else { throw ScanFailure.invalidReceipt }
        var previous = state.lastInstant.flatMap(date), unknown = state.unknownStarted
        for row in rows {
            if let instant = row.captureTime {
                guard let parsed = date(instant), !unknown, previous == nil || parsed <= previous! else { throw ScanFailure.snapshotChanged }
                previous = parsed
            } else { unknown = true }
        }
        func phase(_ asset: ImportAsset) -> String {
            guard let date = asset.captureTime.flatMap(Self.date) else { return "backfill" }
            return date >= boundary ? "recent" : "backfill"
        }
        let firstPhase = phase(rows[0])
        guard state.phase != "backfill" || firstPhase == "backfill" else { throw ScanFailure.snapshotChanged }
        var selected = Array(rows.prefix { phase($0) == firstPhase })
        while try NativeJSON.encode(selected).count > NativeRequests.appendLimit - 4096 {
            guard selected.count > 1 else { throw PairingFailure.bodyLimit }; selected.removeLast()
        }
        guard Set(selected.map(\.nativeID)).count == selected.count else { throw ScanFailure.snapshotChanged }
        return Self(id: UUID().uuidString, sequence: state.nextSequence, start: state.observed, phase: firstPhase,
            checkpoint: "scan:" + state.id + ":" + String(state.observed + selected.count), assets: selected)
    }
    var payloadDigest: String { get throws { SHA256.hash(data: try NativeJSON.encode(assets)).map { String(format: "%02x", $0) }.joined() } }
}
struct ScanPageRecord: Codable, Sendable {
    struct Accepted: Codable, Sendable { let nativeID: String; let assetID: String; let sourceRevision: String }
    let id: String
    let sequence: Int
    let start: Int
    let count: Int
    let phase: String
    let payloadDigest: String
    let accepted: [Accepted]
    var media: MediaJob?
    var copyOutcome = "not_requested"
    init(page: ScanPage, receipt: ScanReceipt) throws {
        id = page.id; sequence = page.sequence; start = page.start; count = page.assets.count; phase = page.phase
        payloadDigest = try page.payloadDigest
        accepted = try receipt.assets.map { mapping in
            guard let row = page.assets.first(where: { $0.nativeID == mapping.native_id }) else { throw ScanFailure.invalidReceipt }
            return Accepted(nativeID: mapping.native_id, assetID: mapping.asset_id, sourceRevision: row.sourceRevision)
        }
    }
}
struct ScanBegin: Codable, Sendable {
    let run_id: String; let next_sequence: Int; let state: String; let coverage: String; let recent_after: String
    let observed: Int; let expected_count: Int; let checkpoint: String?
}
struct ScanReceipt: Codable, Sendable {
    let run_id: String; let sequence: Int; let next_sequence: Int; let accepted: Int; let excluded: Int
    let assets: [ImportReceipt.Asset]; let observed: Int; let expected_count: Int; let phase: String
}
struct ScanFinish: Codable, Sendable {
    let run_id: String; let state: String; let coverage: String; let observed: Int; let expected_count: Int; let media_ready: Int
}
@MainActor protocol ScanStoring {
    func load() throws -> ScanState?
    func save(_ state: ScanState) throws
    func page(scanID: String, sequence: Int) throws -> ScanPageRecord?
    func savePage(_ value: ScanPageRecord, scanID: String) throws
}
protocol ScanReading: Sendable {
    func permission() async -> String
    func freeze(consent: ImportConsent) async throws -> ScanSnapshot
    func verify(_ snapshot: ScanSnapshot, consent: ImportConsent, full: Bool) async throws
    func page(_ snapshot: ScanSnapshot, start: Int, count: Int, consent: ImportConsent) async throws -> [ImportAsset]
}
protocol ScanServicing: Sendable {
    func permission(_ local: PairingIdentity, value: String) async throws
    func begin(_ local: PairingIdentity, state: ScanState) async throws -> ScanBegin
    func append(_ local: PairingIdentity, state: ScanState, page: ScanPage) async throws -> ScanReceipt
    func finish(_ local: PairingIdentity, state: ScanState) async throws -> ScanFinish
}
@MainActor protocol ScanCopying { func copy(sequence: Int) async throws -> String }
