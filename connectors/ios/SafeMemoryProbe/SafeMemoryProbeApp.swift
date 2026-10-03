import SwiftUI
import Photos

@main
struct SafeMemoryProbeApp: App {
    var body: some Scene { WindowGroup { ProbeView() } }
}

@MainActor
struct ProbeView: View {
    @Environment(\.scenePhase) private var scenePhase
    @State private var authorization = "not_determined"
    @State private var consent = false
    @State private var running = false
    @State private var status = "No Photos data read."
    @State private var sampleCount: Int?
    @State private var inspection: Task<Int, Error>?

    var body: some View {
        NavigationStack {
            Form {
                Section("Read-only engineering probe") {
                    Text("This development probe supports local inspection, selected or progressive metadata import and optimized copies. Pairing, importing metadata and sending copies each require explicit consent.")
                    Text("iCloud downloads require separate consent. Apple Photos is never changed. Physical-device acceptance remains pending.")
                }
                PairingSection()
                MetadataImportSection()
                Section("Permission") {
                    LabeledContent("Current permission", value: authorization)
                    Button("Request Photos permission") {
                        Task {
                            _ = await PHPhotoLibrary.requestAuthorization(for: .readWrite)
                            refreshPermission()
                        }
                    }.disabled(running)
                    Text("Apple calls this read/write permission. This probe uses only read APIs. Choose limited access for an owner-selected sample.")
                }
                Section("Sample consent") {
                    Text("Hidden assets and Shared Albums are excluded. iCloud Shared Library origin cannot yet be separated reliably: all sample metadata remains restricted to this probe. Use limited permission to choose exactly which items may be inspected.")
                    Toggle("I authorize this bounded metadata sample", isOn: $consent).disabled(running)
                    Button(running ? "Reading sample…" : "Read up to 50 recent assets") { inspect() }
                        .disabled(running || !consent || !["full", "limited"].contains(authorization))
                }
                Section("Sanitized diagnostics") {
                    Text(status)
                    if let count = sampleCount { LabeledContent("Sample records", value: String(count)) }
                    Text("Media availability, cloud identity, Shared Library provenance, Hidden lifecycle and playback: not verified.")
                    Text("No timestamps, coordinates, filenames, identifiers or credentials appear in these diagnostics. This local inspection action does not persist or share its manifest.")
                }
            }
            .navigationTitle("Safe Memory Probe")
            .task { refreshPermission() }
            .onChange(of: scenePhase) { _, phase in
                if phase == .active { refreshPermission() }
                else { inspection?.cancel(); consent = false; sampleCount = nil; status = "Sample diagnostics cleared while inactive." }
            }
        }
    }

    private func refreshPermission() {
        authorization = PhotosReader.authorizationName(PHPhotoLibrary.authorizationStatus(for: .readWrite))
        if !["full", "limited"].contains(authorization) {
            consent = false
            sampleCount = nil
            status = "Photos permission is required; no sample is displayed."
        }
    }

    private func inspect() {
        running = true
        sampleCount = nil
        status = "Reading bounded metadata sample."
        Task {
            do {
                // No installation/source identity is claimed until approved pairing exists.
                let work = Task.detached(priority: .userInitiated) {
                    let manifest = try PhotosReader.snapshot(installationID: "unpaired-local-probe")
                    _ = try manifest.serialized()
                    return manifest.assets.count
                }
                inspection = work
                let count = try await work.value
                inspection = nil
                refreshPermission()
                guard consent && scenePhase == .active && ["full", "limited"].contains(authorization) else {
                    running = false
                    return
                }
                sampleCount = count
                status = "Metadata sample serialized in memory. No data uploaded or saved. Device acceptance remains pending."
            } catch {
                inspection = nil
                // Intentionally do not print NSError descriptions or Photos content.
                status = "Sample could not be read safely. Check permission and retry."
            }
            running = false
        }
    }
}
