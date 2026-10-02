import Foundation

@main
struct ManifestTests {
    static func main() throws {
        let reasons = ["capture_offset": "not_exposed_by_phasset", "people": "not_exposed_by_public_api"]
        let asset = ProbeAsset(localIdentifier: "synthetic-asset", creationInstant: "2026-10-02T12:00:00.000Z", modificationInstant: nil, addedInstant: nil, mediaType: 1, mediaSubtypes: 8, pixelWidth: 100, pixelHeight: 80, duration: 0, isHidden: false, isFavorite: false, sourceType: 1, location: nil, burstIdentifier: nil, burstSelectionTypes: 0, representsBurst: false, hasAdjustments: false, adjustmentFormatIdentifier: nil, resources: [], unavailable: reasons)
        let manifest = ProbeManifest(probeInstallationID: "synthetic-install", authorization: "limited", requestedLimit: 50, assets: [asset])
        let encoded = try manifest.serialized()
        let decoded = try JSONDecoder().decode(ProbeManifest.self, from: encoded)
        let reencoded = try decoded.serialized()
        assert(reencoded == encoded, "serialization must round-trip stably")
        assert(decoded.assets[0].unavailable["capture_offset"] == "not_exposed_by_phasset")
        assert(decoded.assets[0].captureOffset == nil, "UTC instant must not fabricate capture offset")
        assert(decoded.coverage == "bounded_authorized_sample")
        assert(decoded.assets[0].collectionProvenance == "unknown")
        assert(decoded.assets[0].disclosure == "restricted_probe_only")
        assert(decoded.requestedLimit == 50)
        assert(decoded.schemaVersion == 1)
        print("PASS manifest_round_trip_stable")
        print("PASS missing_capture_offset_explicit")
        print("PASS unknown_provenance_restricted")
        print("PASS bounded_sample_not_whole_library")
    }
}
