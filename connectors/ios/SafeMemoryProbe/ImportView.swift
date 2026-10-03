import SwiftUI
import PhotosUI
import Photos

@MainActor private struct SelectedImportReader: ImportReading {
    func permission() -> String { PhotosReader.authorizationName(PHPhotoLibrary.authorizationStatus(for: .readWrite)) }
    func selection(ids: [String], consent: ImportConsent) async throws -> ImportSelection {
        guard let identity = try PairingKeychain().load() else { throw PairingFailure.unauthorized }
        let task = Task.detached(priority: .userInitiated) {
            let manifest = try PhotosReader.selected(installationID: identity.installationID, ids: ids, consent: consent)
            return try ImportSelection(ids: ids, manifest: manifest, consent: consent)
        }
        return try await withTaskCancellationHandler { try await task.value } onCancel: { task.cancel() }
    }
}

private final class ImportPhotoObserver: NSObject, PHPhotoLibraryChangeObserver, @unchecked Sendable {
    private let changed: @MainActor @Sendable () -> Void
    init(changed: @escaping @MainActor @Sendable () -> Void) {
        self.changed = changed; super.init(); PHPhotoLibrary.shared().register(self)
    }
    deinit { PHPhotoLibrary.shared().unregisterChangeObserver(self) }
    func photoLibraryDidChange(_ changeInstance: PHChange) { Task { @MainActor in changed() } }
}

@MainActor
struct MetadataImportSection: View {
    @Environment(\.scenePhase) private var scenePhase
    @State private var controller: ImportCoordinator?
    @State private var mediaController: MediaCoordinator?
    @State private var scanController: ScanCoordinator?
    @State private var originalController: OriginalCoordinator?
    @State private var originalRequests: [OriginalRequest] = []
    @State private var originalIndex = 0
    @State private var originalCloud = false
    @State private var originalAcknowledged = false
    @State private var originalResumeAcknowledged = false
    @State private var originalResumable = false
    @State private var originalRestrictionPending = false
    @State private var originalStatus = "No original requests checked."
    @State private var observer: ImportPhotoObserver?
    @State private var picked: [PhotosPickerItem] = []
    @State private var consent = ImportConsent()
    @State private var acknowledged = false
    @State private var resumeAcknowledged = false
    @State private var copyAcknowledged = false
    @State private var allowICloud = false
    @State private var copyAvailable = false
    @State private var hasCopyJob = false
    @State private var copyStatus = "No optimized copies requested."
    @State private var scanAcknowledged = false
    @State private var scanResumeAcknowledged = false
    @State private var scanCopyChoice = false
    @State private var scanCloudChoice = false
    @State private var scanResumable = false
    @State private var scanCopyRetryAvailable = false
    @State private var scanRestrictionPending = false
    @State private var scanStatus = "No progressive scan requested."
    @State private var savedCount = 0
    @State private var savedConsent = ""
    @State private var permission = "not_determined"
    @State private var busy = false
    @State private var resumable = false
    @State private var pendingRestriction = false
    @State private var status = "No metadata import has been requested."
    @State private var operation: Task<Void, Never>?

    private var ids: [String] { picked.compactMap(\.itemIdentifier) }
    private var readable: Bool { ["full", "limited"].contains(permission) }
    var body: some View {
        let selectedCount = picked.count
        Section("Import selected metadata") {
            Text("Choose 1–100 items. This is a bounded sample, not a whole-library index. No image, video or Live Photo media bytes are sent.")
            Text("Metadata includes available dates, locations, filenames and resource descriptions. It is stored privately for retry and sent only to your paired Memory account.")
            PhotosPicker(selection: $picked, maxSelectionCount: 100, selectionBehavior: .ordered,
                matching: .any(of: [.images, .videos]), photoLibrary: .shared()) {
                Text("Choose sample (\(selectedCount) selected)")
            }.disabled(busy || !readable || controller == nil)
            Text("Only selected items still accessible through the current Photos permission can be imported. Choosing an item here does not expand limited Photos permission.")
            Toggle("Include selected Hidden items", isOn: $consent.includeHidden).disabled(busy)
            Toggle("Allow possible Shared Library origin", isOn: $consent.includeSharedLibrary).disabled(busy)
            Toggle("Allow possible Shared Album origin", isOn: $consent.includeSharedAlbums).disabled(busy)
            Text("Apple does not establish personal/Shared Library origin for this adapter. Both shared consents are required here and independently in Memory web source settings. Origin and owner presence stay unknown.")
            Toggle("Import metadata for this exact sample", isOn: $acknowledged).disabled(busy)
            Button(busy ? "Working…" : "Import selected metadata") { start() }
                .disabled(busy || !readable || !acknowledged || ids.isEmpty || ids.count != picked.count || !consent.includeSharedLibrary || !consent.includeSharedAlbums || controller == nil || pendingRestriction)
            if resumable {
                Text("Saved sample: \(savedCount) items. \(savedConsent)")
                Toggle("Resume this saved sample with its recorded consents", isOn: $resumeAcknowledged).disabled(busy)
            }
            Button("Resume saved sample") { resume() }
                .disabled(busy || !readable || !resumeAcknowledged || !resumable || pendingRestriction)
            Text("Resume uses the previously consented saved sample, not an unsubmitted picker selection. A changed selection, permission or asset requires a fresh import.")
            Button("Clear previous server selection / retry restriction") { clear() }.disabled(busy || controller == nil)
            Text(status)
            Divider()
            Text("Optimized copies for the confirmed sample")
            Text("Explicitly send JPEG photos and H.264 MP4 videos to your paired Memory account. Live Photos need both still and motion components; available audio is retained. No originals are sent.")
            Toggle("Allow iCloud downloads for this copy job", isOn: $allowICloud).disabled(busy || hasCopyJob)
            Toggle("Send optimized copies for the last confirmed sample", isOn: $copyAcknowledged).disabled(busy || !copyAvailable)
            Button(hasCopyJob ? "Resume optimized copies" : "Send optimized copies") { copy() }
                .disabled(busy || !copyAvailable || !copyAcknowledged || pendingRestriction || !readable || mediaController == nil)
            Text(copyStatus)
            Text("Limits: 64 MiB per component; local staging 512 MiB / 64 export jobs. The sample server retains at most 1 GiB and 256 upload jobs, with space reserved for staged and completed copies. Capacity failures stop the transfer. Missing motion is partial, never a complete Live Photo.")
            Text("Permission and selected-asset changes are checked while this app is active and before each import step. Offline or background detection cannot immediately restrict server copies; pending restrictions are shown and block further import.")
            scanControls
            originalControls
        }
        .task { prepare() }
        .onChange(of: picked) { _, _ in selectionChanged() }
        .onChange(of: consent) { _, _ in selectionChanged() }
        .onChange(of: allowICloud) { _, _ in copyAcknowledged = false }
        .onChange(of: scanCopyChoice) { _, choice in scanAcknowledged = false; if !choice { scanCloudChoice = false } }
        .onChange(of: scanCloudChoice) { _, _ in scanAcknowledged = false }
        .onChange(of: originalCloud) { _, _ in originalAcknowledged = false }
        .onChange(of: originalIndex) { _, _ in originalAcknowledged = false }
        .onChange(of: scenePhase) { _, phase in
            if phase == .active { inspect() }
            else { operation?.cancel(); acknowledged = false; resumeAcknowledged = false; copyAcknowledged = false; scanAcknowledged = false; scanResumeAcknowledged = false; originalAcknowledged = false; originalResumeAcknowledged = false }
        }
    }
    private var scanControls: some View {
        Group {
            Divider()
            Text("Progressive authorized index")
            Text("This separate action enumerates every item exposed by the current full or limited Photos permission and the Hidden/shared choices above. Limited means only the OS-selected subset. Recent items are indexed first, then older and undated items, in pages of at most 100.")
            Text("Options for a new scan:")
            Toggle("Also send optimized copies for accepted pages", isOn: $scanCopyChoice).disabled(busy)
            Toggle("Allow iCloud downloads for those copies", isOn: $scanCloudChoice).disabled(busy || !scanCopyChoice)
            Toggle("Index the entire currently authorized set", isOn: $scanAcknowledged).disabled(busy)
            Button("Start new authorized scan") { startScan() }
                .disabled(busy || !readable || !scanAcknowledged || !consent.includeSharedLibrary || !consent.includeSharedAlbums || scanController == nil || scanRestrictionPending || pendingRestriction)
            Toggle("Resume the saved scan using its recorded choices", isOn: $scanResumeAcknowledged).disabled(busy || (!scanResumable && !scanCopyRetryAvailable))
            Button("Resume saved index") { resumeScan(copiesOnly: false) }
                .disabled(busy || !readable || !scanResumeAcknowledged || !scanResumable || scanRestrictionPending)
            Button("Retry saved scan copies") { resumeScan(copiesOnly: true) }
                .disabled(busy || !readable || !scanResumeAcknowledged || !scanCopyRetryAvailable || scanRestrictionPending)
            Button("Pause active work") { operation?.cancel() }.disabled(!busy)
            Text(scanStatus)
            Text("Index completion is separate from media readiness. Capacity or unavailable media does not stop metadata indexing. Any changed or unverifiable library snapshot requires a new explicit scan. Retained journal: 512 MiB, 64 scans, 20,000 pages per scan; maximum reported set: 1,000,000 items. Nothing silently deletes older jobs.")
        }
    }
    private var originalControls: some View {
        Group {
            Divider()
            Text("Owner-requested originals")
            Text("Request an original for an item in Memory web first. Checking requests does not read or send Photos bytes. Send one request explicitly using its current accepted metadata scope. Original resources keep their original format, RAW alternatives and available audio; they are separate from optimized copies.")
            Button("Check owner requests") { checkOriginals() }.disabled(busy || originalController == nil || originalRestrictionPending)
            if !originalRequests.isEmpty {
                Picker("Pending request", selection: $originalIndex) {
                    ForEach(originalRequests.indices, id: \.self) { index in
                        Text("Request \(index + 1) · \(originalRequests[index].media_type == "live" ? "Live Photo" : originalRequests[index].media_type)").tag(index)
                    }
                }.disabled(busy)
            }
            Toggle("Allow iCloud download for this new original request", isOn: $originalCloud).disabled(busy)
            Toggle("Send the selected owner-requested original", isOn: $originalAcknowledged).disabled(busy || originalRequests.isEmpty)
            Button("Send selected original") { sendOriginal(resume: false) }
                .disabled(busy || !readable || !originalAcknowledged || originalRequests.isEmpty || originalRestrictionPending || pendingRestriction || scanRestrictionPending)
            Toggle("Resume the saved original using its recorded iCloud choice", isOn: $originalResumeAcknowledged).disabled(busy || !originalResumable)
            Button("Resume saved original") { sendOriginal(resume: true) }
                .disabled(busy || !readable || !originalResumeAcknowledged || !originalResumable || originalRestrictionPending)
            Text(originalStatus)
            Text("At most 8 exact resources and 256 MiB per request; local originals retain at most 512 MiB and 64 jobs. The server's combined optimized/original budget is 1 GiB. Nothing silently removes files. Missing or ambiguous resources remain incomplete. A failed server request needs an owner retry in Memory web.")
        }
    }
    private func prepare() {
        do {
            if controller == nil {
                let directory = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
                    .appendingPathComponent("SafeMemoryProbe/MetadataImport", isDirectory: true)
                controller = ImportCoordinator(store: try ImportCheckpointFiles(directory: directory), identities: PairingKeychain(), reader: SelectedImportReader(), service: ImportTransport())
                let exports = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
                    .appendingPathComponent("SafeMemoryProbe/Exports", isDirectory: true)
                mediaController = MediaCoordinator(selection: controller!, exporter: MediaExportAdapter(), files: MediaFiles(root: exports), service: MediaTransport())
                let journal = directory.deletingLastPathComponent().appendingPathComponent("ProgressiveScans", isDirectory: true)
                let scanner = ScanCoordinator(store: try ScanJournal(directory: journal), identities: PairingKeychain(), reader: ScanPhotosReader(), service: ScanTransport())
                scanner.copier = ScanPageCopies(coordinator: scanner, exporter: MediaExportAdapter(), files: MediaFiles(root: exports), service: MediaTransport())
                scanController = scanner
                scanner.onProgress = { try? refreshScan() }
                let originalFiles = try OriginalFiles(directory: directory.deletingLastPathComponent().appendingPathComponent("Originals", isDirectory: true))
                originalController = OriginalCoordinator(store: originalFiles,
                    source: OriginalSourceAdapter(sample: controller!, scan: scanner, identities: PairingKeychain()),
                    exporter: OriginalPhotoExporter(files: originalFiles), files: originalFiles, service: OriginalTransport())
            }
            permission = SelectedImportReader().permission()
            if readable && observer == nil { observer = ImportPhotoObserver { sourceChanged() } }
            try refresh()
            inspect()
        } catch { status = "Private import checkpoint is unavailable. No import can proceed." }
    }
    private func refresh() throws {
        let checkpoint = try controller?.store.load()
        savedCount = checkpoint?.selection.ids.count ?? 0
        if let recorded = checkpoint?.selection.consent {
            savedConsent = "Hidden: \(recorded.includeHidden ? "allowed" : "excluded"); possible Shared Library and Shared Albums: explicitly allowed."
        } else { savedConsent = "" }
        resumable = checkpoint?.stage == .ready || checkpoint?.stage == .clearOldScope
        pendingRestriction = checkpoint?.stage == .revocationPending
        copyAvailable = checkpoint?.stage == .complete && (checkpoint?.accepted ?? 0) > 0
        hasCopyJob = checkpoint?.media != nil
        if let checkpoint, let media = checkpoint.media {
            allowICloud = media.allowICloud
            let ready = media.readyCount(checkpoint)
            let components = media.components.filter { $0.componentID != nil }.count
            copyStatus = "Optimized copies: \(ready) of \(checkpoint.accepted ?? 0) accepted items ready; \(components) components confirmed; \(media.unavailable.count) export failures or incomplete items. Saved job iCloud access: \(media.allowICloud ? "allowed" : "disabled")."
            if !media.exported { copyStatus += " Export was interrupted; explicit resume may read the same authorized sample again." }
            if !media.unavailable.isEmpty { copyStatus += " " + media.failureSummary + ". Failed exports stay incomplete in this job; a fresh sample and explicit consent are required to attempt their export again." }
        } else { copyStatus = "No optimized copies requested for this sample." }
        if pendingRestriction { status = "Restriction pending. Server selection may remain visible until the request succeeds. Retry restriction or restrict this Source in Memory web." }
        else if let checkpoint, checkpoint.stage == .complete {
            status = "Metadata sample completed: \(checkpoint.accepted ?? 0) accepted, \(checkpoint.excluded ?? 0) excluded by server policy."
        } else if checkpoint?.stage == .revoked { status = "Previous server selection cleared. Choose and explicitly consent to a fresh sample." }
        else if resumable { status = "Interrupted sample retained privately. Resume sends the same saved batch after rechecking permission and selected metadata." }
        try refreshScan()
        try refreshOriginal()
    }
    private func refreshOriginal() throws {
        guard let job = try originalController?.store.load() else { return }
        originalRestrictionPending = job.stage == .revocationPending
        originalResumable = [.staging, .transferring, .failed].contains(job.stage)
        let completed = job.components.filter { $0.componentID != nil }.count
        originalStatus = "Saved original: \(completed) of \(job.components.count) resources confirmed. Recorded iCloud download: \(job.allowICloud ? "allowed" : "disabled"). "
        switch job.stage {
        case .staging: originalStatus += "Exact bytes have not finished staging; explicit resume may read this same authorized request again."
        case .transferring: originalStatus += "Transfer interrupted or in progress; saved chunks can be retried."
        case .ready: originalStatus += "All original resources acknowledged ready by the server. Current web policy remains authoritative."
        case .failed:
            if job.error == "capacity" { originalStatus += "Storage capacity reached; staged bytes remain retained. " }
            else if job.error == "icloud_unavailable" { originalStatus += "Original unavailable without iCloud. A new explicit download choice is possible after owner retry. " }
            else if job.error == "unsupported_resource" { originalStatus += "Required original resources are missing, ambiguous or unsupported. " }
            originalStatus += "Owner retry in Memory web is required before further transfer."
        case .revocationPending: originalStatus += "Restriction pending; retry Clear previous server selection or restrict the Source in Memory web."
        case .revoked: originalStatus += "Previous scope restricted. A fresh accepted import and owner request are required."
        }
    }
    private func checkOriginals() {
        guard let originalController else { return }; busy = true; originalAcknowledged = false
        operation = Task {
            do { originalRequests = try await originalController.pending(); originalIndex = 0; originalStatus = "\(originalRequests.count) pending owner requests. No Photos bytes read by this check." }
            catch { originalStatus = "Requests could not be checked. Verify pairing and Source access." }
            busy = false; operation = nil
        }
    }
    private func sendOriginal(resume: Bool) {
        guard let originalController else { return }
        let request = originalRequests.indices.contains(originalIndex) ? originalRequests[originalIndex] : nil
        let cloud = originalCloud
        guard resume || request != nil else { return }; busy = true
        originalStatus = "Verifying current scope and exact original resources."
        operation = Task {
            do {
                if resume { _ = try await originalController.resume() }
                else if let request { _ = try await originalController.start(request, allowICloud: cloud) }
                try refreshOriginal()
            } catch {
                try? refreshOriginal()
                if !originalRestrictionPending { originalStatus += " Original transfer not verified. Check current Photos access, owner retry, iCloud choice and capacity; no completion is inferred." }
            }
            originalAcknowledged = false; originalResumeAcknowledged = false; busy = false; operation = nil
        }
    }
    private func refreshScan() throws {
        guard let scan = try scanController?.store.load() else { return }
        scanRestrictionPending = scan.stage == .revocationPending
        scanResumable = scan.stage == .indexing
        scanCopyRetryAvailable = [.indexing, .complete].contains(scan.stage) && scan.copy && scan.nextSequence > 0
        let flags = "Saved choices: Hidden \(scan.consent.includeHidden ? "allowed" : "excluded"), both shared origins allowed, optimized copies \(scan.copy ? "requested" : "not requested"), iCloud \(scan.cloud ? "allowed" : "disabled")."
        if scanRestrictionPending { scanStatus = "Scan restriction pending; server copies may remain visible until cleared. Use Clear previous server selection / retry restriction or restrict the Source in Memory web." }
        else if scan.stage == .revoked { scanStatus = "Previous scan restricted. A new explicit authorized scan is required." }
        else if let snapshot = scan.snapshot {
            scanStatus = "\(snapshot.permission == "limited" ? "Limited authorized subset" : "Full authorized set"): \(scan.observed) of \(snapshot.expectedCount) items observed; \(scan.accepted) accepted, \(scan.excluded) excluded. Index \(scan.stage == .complete ? "complete" : "in progress"), \(scan.phase == "recent" ? "recent items" : "older or undated items"). Copies: \(scan.copyLabel). \(flags)"
            if let ready = scan.sourceMediaReady { scanStatus += " Last server receipt: \(ready) Source-wide media items ready; this is not this scan's copy count." }
        } else { scanStatus = "Snapshot was not frozen. Start a new explicit scan; no index completion is claimed. \(flags)" }
    }
    private func inspect() {
        permission = SelectedImportReader().permission()
        if readable && observer == nil { observer = ImportPhotoObserver { sourceChanged() } }
        guard let controller else { return }
        // Does not import. Only an existing consented checkpoint is examined;
        // detected changes can issue a security-only permission revocation.
        Task {
            do { try await controller.inspectChanges(); try refresh() }
            catch { try? refresh(); if !pendingRestriction { status = "The saved sample changed or cannot be verified. A fresh selection is required." } }
            do { try await scanController?.inspectChanges(); try refreshScan() }
            catch { scanFailure(error) }
            do { try await originalController?.inspect(); try refreshOriginal() }
            catch { try? refreshOriginal() }
        }
    }
    private func sourceChanged() {
        operation?.cancel(); scanAcknowledged = false; scanResumeAcknowledged = false; originalAcknowledged = false; originalResumeAcknowledged = false
        Task {
            do { try await originalController?.invalidate(); try refreshOriginal() } catch { try? refreshOriginal() }
            // A scan covers the whole consented set. Any PhotoKit callback
            // invalidates that frozen enumeration, even between pages.
            do { try await scanController?.invalidate(); try refreshScan() }
            catch { scanFailure(error) }
            inspect()
        }
    }
    private func selectionChanged() {
        acknowledged = false; resumeAcknowledged = false; copyAcknowledged = false; scanAcknowledged = false; scanResumeAcknowledged = false; originalAcknowledged = false; originalResumeAcknowledged = false; operation?.cancel()
        guard let controller else { return }
        Task {
            do { try await originalController?.invalidate(); try refreshOriginal() } catch { try? refreshOriginal() }
            do { try await controller.invalidate(); try refresh() }
            catch { try? refresh(); status = "Restriction could not be confirmed. Further import is blocked until the previous selection is cleared." }
            do { try await scanController?.invalidate(); try refreshScan() }
            catch { scanFailure(error) }
        }
    }
    private func start() {
        guard let controller else { return }
        let selected = ids, approved = consent
        busy = true; status = "Validating the selected sample and saving its retry checkpoint."
        operation = Task {
            do { try await originalController?.invalidate(); try await scanController?.invalidate(); _ = try await controller.start(ids: selected, consent: approved); try refresh() }
            catch { failure() }
            busy = false; operation = nil
        }
    }
    private func resume() {
        guard let controller else { return }
        busy = true; status = "Rechecking and resuming the saved sample."
        operation = Task {
            do { _ = try await controller.resume(); try refresh() }
            catch { failure() }
            busy = false; operation = nil
        }
    }
    private func clear() {
        guard let controller else { return }
        acknowledged = false; busy = true
        operation = Task {
            do { try await originalController?.invalidate(); try await controller.invalidate(); try await scanController?.invalidate(); try refresh() }
            catch { failure() }
            busy = false; operation = nil
        }
    }
    private func copy() {
        guard let mediaController else { return }
        let resumeExisting = hasCopyJob, cloudConsent = allowICloud
        busy = true; copyStatus = "Rechecking the confirmed sample before optimized export or transfer."
        operation = Task {
            do {
                if resumeExisting { _ = try await mediaController.resume() }
                else { _ = try await mediaController.start(allowICloud: cloudConsent) }
                try refresh()
            } catch {
                try? refresh()
                if pendingRestriction { copyStatus = "Transfer stopped. Restriction remains pending; retry restriction or restrict the Source in Memory web." }
                else if case PairingFailure.capacity = error { copyStatus = "Server media capacity reached (1 GiB / 256 retained jobs, including reservations). Transfer stopped; no copies were silently removed." }
                else if case PairingFailure.conflict = error { copyStatus = "Server rejected conflicting retained bytes or state. This job was not replaced; no successful transfer is claimed." }
                else { copyStatus = "Copies interrupted or unavailable. Check permission and Source settings; explicit resume revalidates the saved sample. Missing or incompatible exports stay incomplete." }
            }
            copyAcknowledged = false; busy = false; operation = nil
        }
    }
    private func failure() {
        do { try refresh() } catch { status = "Private checkpoint could not be read. No further import is safe."; return }
        if !pendingRestriction && !resumable { status = "Import was not verified. Check pairing, Photos permission and both shared-origin consents. No successful import is claimed." }
    }
    private func startScan() {
        guard let controller, let scanController else { return }
        let approved = consent, copies = scanCopyChoice, cloud = scanCloudChoice
        busy = true; scanStatus = "Restricting the previous selection and freezing the authorized snapshot."
        operation = Task {
            do { try await originalController?.invalidate(); try await controller.invalidate(); _ = try await scanController.start(consent: approved, copy: copies, cloud: cloud); try refresh() }
            catch { scanFailure(error) }
            scanAcknowledged = false; scanResumeAcknowledged = false; busy = false; operation = nil
        }
    }
    private func resumeScan(copiesOnly: Bool) {
        guard let scanController else { return }
        busy = true; scanStatus = "Verifying the saved snapshot, permission and recorded choices."
        operation = Task {
            do {
                if copiesOnly { _ = try await scanController.retryCopies() }
                else { _ = try await scanController.resume() }
                try refresh()
            } catch { scanFailure(error) }
            scanResumeAcknowledged = false; busy = false; operation = nil
        }
    }
    private func scanFailure(_ error: Error) {
        do { try refreshScan() } catch { scanStatus = "Private scan journal unavailable. No further scan or transfer is safe."; return }
        if scanRestrictionPending { return }
        switch error {
        case ScanFailure.capacity: scanStatus += " Journal or enumeration capacity reached. No completion is claimed and no retained jobs were removed."
        case ScanFailure.snapshotChanged, ScanFailure.snapshotUnavailable: scanStatus += " Snapshot continuity was not verified; start a fresh explicit scan."
        case PairingFailure.unauthorized: scanStatus += " The server refused this scope or identity. Check web Source flags and pairing; flags are never changed automatically."
        case ImportFailure.invalidSelection: scanStatus += " A selected or unsupported PhotoKit item could not be represented; complete coverage is not claimed."
        default: scanStatus += " Scan interrupted. Retained pages may be resumed only after snapshot verification; no completion is inferred."
        }
    }
}
