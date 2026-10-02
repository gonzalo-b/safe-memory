import Foundation
import CryptoKit

@main struct ImportModelTests {
    static func row(hidden: Bool = false, date: String? = "2026-10-02T12:00:00.000Z", favorite: Bool = false) -> ProbeAsset {
        ProbeAsset(localIdentifier: "synthetic-selected", creationInstant: date, modificationInstant: nil, addedInstant: nil,
            mediaType: 1, mediaSubtypes: 0, pixelWidth: 20, pixelHeight: 10, duration: 0, isHidden: hidden, isFavorite: favorite,
            sourceType: 1, location: nil, burstIdentifier: nil, burstSelectionTypes: 0, representsBurst: false,
            hasAdjustments: false, adjustmentFormatIdentifier: nil, resources: [], unavailable: ["capture_offset": "not_exposed_by_phasset"])
    }
    static func main() throws {
        let original = try ImportAsset(row())
        let repeatValue = try ImportAsset(row())
        assert(original.sourceRevision == repeatValue.sourceRevision)
        let hidden = try ImportAsset(row(hidden: true))
        let favorite = try ImportAsset(row(favorite: true))
        assert(original.sourceRevision != hidden.sourceRevision && original.sourceRevision != favorite.sourceRevision)
        let raw = try JSONSerialization.jsonObject(with: NativeJSON.encode(original)) as! [String: Any]
        assert(raw["collection"] as? String == "unknown" && raw["owner_presence"] as? String == "unknown")
        assert(raw["time_basis"] as? String == "instant_only")
        assert(raw["source_modified"] is NSNull)
        var excludingRevision = raw; excludingRevision.removeValue(forKey: "source_revision")
        let external = try JSONSerialization.data(withJSONObject: excludingRevision, options: [.sortedKeys, .withoutEscapingSlashes])
        assert(SHA256.hash(data: external).map { String(format: "%02x", $0) }.joined() == original.sourceRevision)
        let unicode = try NativeJSON.encode(["key": "é😀"])
        assert(String(decoding: unicode, as: UTF8.self) == "{\"key\":\"\\u00e9\\ud83d\\ude00\"}")
        let missing = try ImportAsset(row(date: nil))
        let absent = try JSONSerialization.jsonObject(with: NativeJSON.encode(missing)) as! [String: Any]
        assert(absent["capture_time"] is NSNull && absent["time_basis"] as? String == "unknown")
        print("PASS full_wrapper_revision_tracks_metadata_and_restriction")
        print("PASS date_instant_does_not_invent_offset_or_presence")
        let manifest = ProbeManifest(probeInstallationID: "installation", authorization: "limited", requestedLimit: 1, assets: [row()])
        do { _ = try ImportSelection(ids: ["synthetic-selected"], manifest: manifest, consent: ImportConsent()); fatalError("Unknown source admitted") } catch {}
        let consent = ImportConsent(includeHidden: false, includeSharedLibrary: true, includeSharedAlbums: true)
        let selected = try ImportSelection(ids: ["synthetic-selected"], manifest: manifest, consent: consent)
        assert(selected.assets.count == 1)
        for ids in [[], ["other"], ["synthetic-selected", "synthetic-selected"], Array(repeating: "id", count: 101)] {
            do { _ = try ImportSelection(ids: ids, manifest: manifest, consent: consent); fatalError("Invalid selection admitted") } catch {}
        }
        print("PASS exact_selected_scope_and_both_unknown_opt_ins")
    }
}
