import Foundation

@MainActor final class MediaCoordinator {
    private let selection: any MediaSelectionSource
    private let exporter: any MediaExporting
    private let files: any MediaFileReading
    private let service: any MediaServicing
    private var running = false
    init(selection: any MediaSelectionSource, exporter: any MediaExporting, files: any MediaFileReading, service: any MediaServicing) {
        self.selection = selection; self.exporter = exporter; self.files = files; self.service = service
    }
    func start(allowICloud: Bool) async throws -> MediaJob {
        guard !running else { throw ImportFailure.busy }
        running = true; defer { running = false }
        let sample = try await selection.mediaSelection()
        guard sample.media == nil, let accepted = sample.acceptedAssets, !accepted.isEmpty else { throw MediaFailure.incomplete }
        try Task.checkCancellation()
        let job = MediaJob(id: UUID().uuidString, allowICloud: allowICloud)
        try selection.saveMedia(job, jobID: sample.jobID)
        running = false
        return try await resume()
    }
    private func verify(_ original: ImportCheckpoint, mediaID: String) async throws -> ImportCheckpoint {
        try Task.checkCancellation()
        let now = try await selection.mediaSelection()
        guard now.jobID == original.jobID, now.media?.id == mediaID, now.selection.matches(original.selection) else { throw MediaFailure.changedSample }
        try Task.checkCancellation()
        return now
    }
    func resume() async throws -> MediaJob {
        guard !running else { throw ImportFailure.busy }
        running = true; defer { running = false }
        let sample = try await selection.mediaSelection()
        guard var job = sample.media else { throw MediaFailure.incomplete }
        try job.validate(sample)
        let identity = try selection.mediaIdentity(sample)
        if !job.exported {
            _ = try await verify(sample, mediaID: job.id)
            let batch = try await exporter.export(sample, allowICloud: job.allowICloud)
            // Whole captured wrapper is checked again; exporter-only modification
            // date checks cannot bind bytes to a full frozen metadata revision.
            _ = try await verify(sample, mediaID: job.id)
            try job.retain(batch, sample: sample)
            for component in job.components { try files.validate(component) }
            try selection.saveMedia(job, jobID: sample.jobID)
        }
        for index in job.components.indices {
            _ = try await verify(sample, mediaID: job.id)
            if job.components[index].componentID != nil { continue }
            var upload = job.components[index]
            try files.validate(upload)
            let begin = try await service.begin(identity, upload: upload)
            let possibleReplayEnd = upload.offset + min(MediaJob.chunkSize, upload.size - upload.offset)
            guard PairingRequests.identifier(begin.upload_id), ["active", "complete"].contains(begin.state),
                  upload.uploadID == nil || upload.uploadID == begin.upload_id,
                  begin.next_offset == upload.offset || begin.next_offset == possibleReplayEnd else { throw ImportFailure.invalidReceipt }
            _ = try await verify(sample, mediaID: job.id)
            upload.uploadID = begin.upload_id; job.components[index] = upload
            try selection.saveMedia(job, jobID: sample.jobID)
            // Persisted offset is authoritative for retries. Replaying the last
            // identical chunk recovers a lost server acknowledgement safely.
            while upload.offset < upload.size {
                _ = try await verify(sample, mediaID: job.id)
                let count = min(MediaJob.chunkSize, upload.size - upload.offset)
                let bytes = try files.read(upload, offset: upload.offset, count: count)
                guard bytes.count == count else { throw MediaFailure.integrity }
                let receipt = try await service.chunk(identity, uploadID: begin.upload_id, offset: upload.offset, data: bytes)
                guard receipt.upload_id == begin.upload_id, receipt.next_offset == upload.offset + count else { throw ImportFailure.invalidReceipt }
                _ = try await verify(sample, mediaID: job.id)
                upload.offset = receipt.next_offset; job.components[index] = upload
                try selection.saveMedia(job, jobID: sample.jobID)
            }
            try files.validate(upload)
            _ = try await verify(sample, mediaID: job.id)
            let done = try await service.complete(identity, upload: upload)
            guard PairingRequests.identifier(done.component_id), done.state == "ready", done.size == upload.size, done.mime == upload.mime else { throw ImportFailure.invalidReceipt }
            _ = try await verify(sample, mediaID: job.id)
            upload.componentID = done.component_id; job.components[index] = upload
            try selection.saveMedia(job, jobID: sample.jobID)
        }
        _ = try await verify(sample, mediaID: job.id)
        return job
    }
}
