import Foundation
@preconcurrency import Photos
import CryptoKit

/// Explicit scan only. Public persistent history plus a streamed membership
/// fingerprint establish continuity; any unverifiable change requires restart.
actor ScanPhotosReader: ScanReading {
    private var frozen: PHFetchResult<PHAsset>?
    private var fingerprint: String?
    func permission() async -> String { PhotosReader.authorizationName(PHPhotoLibrary.authorizationStatus(for: .readWrite)) }
    private func fetch(_ consent: ImportConsent) throws -> PHFetchResult<PHAsset> {
        guard consent.includeSharedLibrary && consent.includeSharedAlbums else { throw ImportFailure.consentRequired }
        let options = PHFetchOptions()
        options.includeHiddenAssets = consent.includeHidden; options.includeAllBurstAssets = true
        options.includeAssetSourceTypes = [.typeUserLibrary, .typeCloudShared, .typeiTunesSynced]
        options.sortDescriptors = [NSSortDescriptor(key: "creationDate", ascending: false)]
        // No media predicate: an unsupported type must stop coverage rather
        // than silently disappear from an allegedly complete enumeration.
        let result = PHAsset.fetchAssets(with: options)
        guard result.count <= 1_000_000 else { throw ScanFailure.capacity }
        return result
    }
    private func hash(_ result: PHFetchResult<PHAsset>) throws -> String {
        var digest = SHA256()
        for index in 0..<result.count {
            try Task.checkCancellation()
            autoreleasepool {
                let id = Data(result.object(at: index).localIdentifier.utf8)
                var size = UInt64(id.count).bigEndian
                withUnsafeBytes(of: &size) { digest.update(data: Data($0)) }
                digest.update(data: id)
            }
        }
        return digest.finalize().map { String(format: "%02x", $0) }.joined()
    }
    private func unchanged(_ token: PHPersistentChangeToken) throws {
        do {
            let changes = try PHPhotoLibrary.shared().fetchPersistentChanges(since: token)
            if changes.makeIterator().next() != nil { throw ScanFailure.snapshotChanged }
        } catch { throw ScanFailure.snapshotChanged }
    }
    func freeze(consent: ImportConsent) async throws -> ScanSnapshot {
        let permission = PhotosReader.authorizationName(PHPhotoLibrary.authorizationStatus(for: .readWrite))
        guard ["full", "limited"].contains(permission) else { throw ScanFailure.snapshotUnavailable }
        let token = PHPhotoLibrary.shared().currentChangeToken
        let result = try fetch(consent), digest = try hash(result)
        try unchanged(token)
        guard PhotosReader.authorizationName(PHPhotoLibrary.authorizationStatus(for: .readWrite)) == permission else { throw ScanFailure.snapshotChanged }
        let archived = try NSKeyedArchiver.archivedData(withRootObject: token, requiringSecureCoding: true)
        let snapshot = ScanSnapshot(permission: permission, expectedCount: result.count, orderedIDHash: digest, changeToken: archived)
        try snapshot.validate(); frozen = result; fingerprint = digest; return snapshot
    }
    func verify(_ snapshot: ScanSnapshot, consent: ImportConsent, full: Bool) async throws {
        try Task.checkCancellation(); try snapshot.validate()
        guard PhotosReader.authorizationName(PHPhotoLibrary.authorizationStatus(for: .readWrite)) == snapshot.permission,
              let token = try? NSKeyedUnarchiver.unarchivedObject(ofClass: PHPersistentChangeToken.self, from: snapshot.changeToken) else { throw ScanFailure.snapshotChanged }
        try unchanged(token)
        if full || frozen == nil || fingerprint != snapshot.orderedIDHash {
            let result = try fetch(consent)
            guard result.count == snapshot.expectedCount, try hash(result) == snapshot.orderedIDHash else { throw ScanFailure.snapshotChanged }
            try unchanged(token); frozen = result; fingerprint = snapshot.orderedIDHash
        }
        guard PhotosReader.authorizationName(PHPhotoLibrary.authorizationStatus(for: .readWrite)) == snapshot.permission else { throw ScanFailure.snapshotChanged }
    }
    func page(_ snapshot: ScanSnapshot, start: Int, count: Int, consent: ImportConsent) async throws -> [ImportAsset] {
        try await verify(snapshot, consent: consent, full: false)
        guard let frozen, start >= 0, (1...100).contains(count), start <= frozen.count - count else { throw ScanFailure.snapshotChanged }
        var rows: [ImportAsset] = []
        for index in start..<start + count {
            try Task.checkCancellation()
            let asset = frozen.object(at: index)
            guard !asset.isHidden || consent.includeHidden else { throw ScanFailure.snapshotChanged }
            rows.append(try ImportAsset(PhotosReader.describe(asset)))
        }
        try await verify(snapshot, consent: consent, full: false)
        return rows
    }
}
