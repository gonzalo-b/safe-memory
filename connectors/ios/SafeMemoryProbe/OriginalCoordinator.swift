import Foundation

@MainActor final class OriginalCoordinator {
    let store: any OriginalStoring
    private let source: any OriginalSource
    private let exporter: any OriginalExporting
    private let files: any OriginalFileReading
    private let service: any OriginalServicing
    private var running = false
    private var revocation: Task<Void, Error>?
    init(store: any OriginalStoring, source: any OriginalSource, exporter: any OriginalExporting, files: any OriginalFileReading, service: any OriginalServicing) {
        self.store = store; self.source = source; self.exporter = exporter; self.files = files; self.service = service
    }
    func pending() async throws -> [OriginalRequest] {
        if try store.load()?.stage == .revocationPending { try await flushRevocation() }
        let response = try await service.pending(source.identity())
        guard response.requests.count <= 20, Set(response.requests.map(\.request_id)).count == response.requests.count else { throw OriginalFailure.invalidReceipt }
        try response.requests.forEach { try $0.validate() }; return response.requests
    }
    private func current(_ job: OriginalJob) throws -> OriginalJob {
        guard let saved = try store.load(), saved.id == job.id, ![.revocationPending, .revoked].contains(saved.stage) else { throw OriginalFailure.restricted }
        return saved
    }
    private func verify(_ job: OriginalJob) async throws -> PairingIdentity {
        try Task.checkCancellation(); _ = try current(job)
        let identity = try source.identity()
        guard identity.claimID == job.scope.deviceID, identity.libraryID == job.scope.libraryID, identity.fingerprint == job.scope.fingerprint else { throw PairingFailure.relinkRequired }
        do {
            let scope = try await source.scope(job.request)
            guard job.scope.matches(scope) else { throw OriginalFailure.revision_changed }
        } catch is CancellationError { throw CancellationError() }
        catch PairingFailure.unavailable { throw PairingFailure.unavailable }
        catch { try await invalidate(); throw OriginalFailure.revision_changed }
        _ = try current(job); try Task.checkCancellation(); return identity
    }
    func start(_ request: OriginalRequest, allowICloud: Bool) async throws -> OriginalJob {
        guard !running else { throw ImportFailure.busy }
        try request.validate()
        if let old = try store.load(), old.request.request_id == request.request_id, old.stage != .revoked {
            if old.allowICloud == allowICloud { return try await resume() }
            // A fresh explicit cloud choice may replace an unstaged failed
            // attempt after the owner retry. Keep its old partial files; never
            // change consent or the frozen manifest of registered bytes.
            guard old.stage == .failed && old.components.isEmpty else { throw ImportFailure.consentRequired }
        }
        running = true; defer { running = false }
        let available = try await pending()
        guard available.contains(where: { $0.request_id == request.request_id && $0.asset_id == request.asset_id && $0.native_id == request.native_id && $0.source_revision == request.source_revision }) else { throw OriginalFailure.restricted }
        let scope = try await source.scope(request)
        let job = OriginalJob(id: UUID().uuidString, request: request, scope: scope, allowICloud: allowICloud)
        try job.validate(); try store.save(job)
        running = false; return try await resume()
    }
    func resume() async throws -> OriginalJob {
        guard !running else { throw ImportFailure.busy }
        running = true; defer { running = false }
        guard var job = try store.load() else { throw OriginalFailure.restricted }
        if job.stage == .revocationPending { try await flushRevocation(); throw OriginalFailure.restricted }
        guard job.stage != .revoked else { throw OriginalFailure.restricted }
        try job.validate()
        do {
            var identity = try await verify(job)
            if job.components.isEmpty {
                // Failed export retries require a current owner retry; an app
                // button cannot silently clear the server's failed state.
                let requests = try await pending()
                guard requests.contains(where: { $0.request_id == job.request.request_id && $0.source_revision == job.request.source_revision }) else { throw OriginalFailure.restricted }
                job.stage = .staging; job.error = nil; try store.save(job)
                let components = try await exporter.export(job)
                identity = try await verify(job)
                job.components = components; job.stage = .transferring; try job.validate()
                for component in components { try files.validate(component, jobID: job.id) }
                try store.save(job)
            }
            for component in job.components { try files.validate(component, jobID: job.id) }
            identity = try await verify(job)
            let begun = try await service.begin(identity, job: job)
            guard begun.request_id == job.request.request_id, ["transferring", "ready"].contains(begun.state), begun.resources.count == job.components.count,
                  Set(begun.resources.map(\.upload_id)).count == job.components.count else { throw OriginalFailure.invalidReceipt }
            for index in job.components.indices {
                let receipt = begun.resources[index], component = job.components[index]
                let next = component.offset + min(OriginalPolicy.chunkSize, component.descriptor.size - component.offset)
                guard receipt.ordinal == index, PairingRequests.identifier(receipt.upload_id), ["active", "complete"].contains(receipt.state),
                      component.uploadID == nil || component.uploadID == receipt.upload_id,
                      (component.uploadID == nil && (0...component.descriptor.size).contains(receipt.next_offset)) ||
                        receipt.next_offset == component.offset || receipt.next_offset == next,
                      receipt.state != "complete" || receipt.next_offset == component.descriptor.size else { throw OriginalFailure.invalidReceipt }
                job.components[index].uploadID = receipt.upload_id
                if component.uploadID == nil {
                    // begin binds the already validated exact manifest. A
                    // different authorized device may have staged these bytes.
                    // Existing local uploads keep their offset and replay the
                    // last chunk instead of skipping a lost acknowledgement.
                    job.components[index].offset = receipt.next_offset
                }
            }
            identity = try await verify(job); job.stage = .transferring; job.error = nil; try store.save(job)
            var parentReady = begun.state == "ready"
            for index in job.components.indices {
                var component = job.components[index]
                guard let upload = component.uploadID else { throw OriginalFailure.invalidReceipt }
                if component.componentID != nil { continue }
                while component.offset < component.descriptor.size {
                    identity = try await verify(job)
                    let size = min(OriginalPolicy.chunkSize, component.descriptor.size - component.offset)
                    let data = try files.read(component, jobID: job.id, offset: component.offset, count: size)
                    let receipt = try await service.chunk(identity, uploadID: upload, offset: component.offset, data: data)
                    guard receipt.upload_id == upload, receipt.next_offset == component.offset + size,
                          ["active", "complete"].contains(receipt.state), receipt.state != "complete" || receipt.next_offset == component.descriptor.size else { throw OriginalFailure.invalidReceipt }
                    identity = try await verify(job); component.offset = receipt.next_offset; job.components[index] = component; try store.save(job)
                }
                try files.validate(component, jobID: job.id); identity = try await verify(job)
                let receipt = try await service.complete(identity, uploadID: upload)
                guard receipt.request_id == job.request.request_id, receipt.upload_id == upload, PairingRequests.identifier(receipt.component_id),
                      ["transferring", "ready"].contains(receipt.state) else { throw OriginalFailure.invalidReceipt }
                identity = try await verify(job)
                component.componentID = receipt.component_id; job.components[index] = component; parentReady = receipt.state == "ready"; try store.save(job)
            }
            guard parentReady, job.components.allSatisfy({ $0.componentID != nil }) else { throw OriginalFailure.invalidReceipt }
            _ = try await verify(job); job.stage = .ready; try store.save(job); return job
        } catch PairingFailure.capacity {
            try await recordFailure(job, reason: "capacity")
            throw OriginalFailure.capacity
        } catch PairingFailure.unauthorized {
            try await invalidate()
            throw PairingFailure.unauthorized
        } catch let failure as OriginalFailure {
            if [.permission_changed, .revision_changed].contains(failure) { try await invalidate() }
            else if let reason = failure.serverReason { try await recordFailure(job, reason: reason) }
            throw failure
        }
    }
    private func recordFailure(_ original: OriginalJob, reason: String) async throws {
        guard var job = try? current(original) else { return }
        job.stage = .failed; job.error = reason; try store.save(job)
        // A source policy change may make reporting failure unauthorized;
        // that cannot weaken the server's denial or erase local state.
        if let identity = try? await verify(job) { try? await service.fail(identity, requestID: job.request.request_id, reason: reason) }
    }
    func invalidate() async throws {
        guard var job = try store.load(), job.stage != .revoked else { return }
        job.stage = .revocationPending; try store.save(job); try await flushRevocation()
    }
    func flushRevocation() async throws {
        if let revocation { try await revocation.value; return }
        let task = Task { @MainActor in
            defer { self.revocation = nil }
            guard var job = try self.store.load(), job.stage == .revocationPending else { return }
            try await self.source.revoke()
            guard let latest = try self.store.load(), latest.id == job.id, latest.stage == .revocationPending else { throw OriginalFailure.restricted }
            job = latest; job.stage = .revoked; try self.store.save(job)
        }
        revocation = task; try await task.value
    }
    func inspect() async throws {
        guard let job = try store.load(), job.stage != .revoked else { return }
        if job.stage == .revocationPending { try await flushRevocation(); return }
        _ = try await verify(job)
    }
}
