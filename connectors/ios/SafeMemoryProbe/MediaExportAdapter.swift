import Foundation

@MainActor struct MediaExportAdapter: MediaExporting {
    func export(_ sample: ImportCheckpoint, allowICloud: Bool) async throws -> ExportBatchResult {
        guard sample.stage == .complete, let accepted = sample.acceptedAssets, !accepted.isEmpty else { throw ImportFailure.selectionChanged }
        let ids = accepted.map(\.native_id)
        let rows = sample.selection.assets.filter { ids.contains($0.nativeID) }.map(\.metadata)
        let manifest = ProbeManifest(probeInstallationID: "paired-selected-sample", authorization: sample.selection.permission,
            requestedLimit: ids.count, assets: rows)
        let consent = sample.selection.consent
        guard consent.includeSharedLibrary && consent.includeSharedAlbums else { throw ImportFailure.consentRequired }
        return try await OptimizedMediaExporter.shared.export(selectedIDs: ids, manifest: manifest,
            consent: ExportConsent(includeHidden: consent.includeHidden, includeSharedAlbums: consent.includeSharedAlbums,
                includeSharedLibrary: consent.includeSharedLibrary, allowICloud: allowICloud))
    }
}
