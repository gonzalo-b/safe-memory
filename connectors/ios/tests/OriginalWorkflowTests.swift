import Foundation
import CryptoKit

@MainActor private final class Source: OriginalSource {
    let local = PairingIdentity(installationID:"installation",libraryID:"library",deviceName:"Synthetic",credential:String(repeating:"A",count:43),claimID:"device",expiresAt:999999)
    var changed = false, offline = false, revoked = false
    let value: OriginalScope
    let request: OriginalRequest
    init() throws {
        let row = ProbeAsset(localIdentifier:"native",creationInstant:nil,modificationInstant:nil,addedInstant:nil,mediaType:1,mediaSubtypes:8,
            pixelWidth:1,pixelHeight:1,duration:1,isHidden:false,isFavorite:false,sourceType:1,location:nil,burstIdentifier:nil,burstSelectionTypes:0,
            representsBurst:false,hasAdjustments:false,adjustmentFormatIdentifier:nil,resources:[
                .init(role:1,assetLocalIdentifier:"native",originalFilename:"still.HEIC",uniformTypeIdentifier:"public.heic",pixelWidth:1,pixelHeight:1),
                .init(role:9,assetLocalIdentifier:"native",originalFilename:"motion.MOV",uniformTypeIdentifier:"com.apple.quicktime-movie",pixelWidth:1,pixelHeight:1)],unavailable:[:])
        let asset = try ImportAsset(row)
        value = OriginalScope(deviceID:"device",libraryID:"library",fingerprint:local.fingerprint,scopeID:UUID().uuidString,permission:"limited",
            consent:.init(includeHidden:false,includeSharedLibrary:true,includeSharedAlbums:true),asset:asset)
        request = .init(request_id:"request",asset_id:"asset",native_id:"native",source_revision:asset.sourceRevision,media_type:"live",state:"waiting_for_device")
    }
    func identity() throws -> PairingIdentity { local }
    func scope(_ request: OriginalRequest) async throws -> OriginalScope { if changed || revoked { throw OriginalFailure.revision_changed }; return value }
    func revoke() async throws { if offline { throw PairingFailure.unavailable }; revoked = true }
}
@MainActor private final class Exporter: OriginalExporting {
    let files: OriginalFiles
    var calls = 0, omitMotion = false, needsCloud = false
    var choices: [Bool] = []
    init(_ files: OriginalFiles) { self.files = files }
    func export(_ job: OriginalJob) async throws -> [OriginalComponent] {
        calls += 1; choices.append(job.allowICloud)
        if needsCloud && !job.allowICloud { throw OriginalFailure.icloud_unavailable }
        var components: [OriginalComponent] = []
        for row in try OriginalPolicy.select(job.scope.asset.metadata.resources, media:job.request.media_type) {
            if omitMotion && row.role == 9 { continue }
            let spool = try files.newSpool(jobID:job.id,limit:OriginalPolicy.maximum)
            try spool.append(Data(repeating:UInt8(row.role),count:row.role == 1 ? OriginalPolicy.chunkSize + 3 : 7))
            components.append(try spool.finish(row))
        }
        return components
    }
}
private actor Server: OriginalServicing {
    let request: OriginalRequest
    var descriptors: [OriginalDescriptor] = [], bytes: [String:Data] = [:], completeIDs = Set<String>()
    var loseChunk = true, loseComplete = true, capacityOnce = false
    var chunks = 0, failures = 0, failed = false
    init(_ request: OriginalRequest) { self.request = request }
    func stats() -> (Int,Int) { (chunks,failures) }
    func ownerRetry() { failed = false }
    func rejectCapacityOnce() { capacityOnce = true }
    func pending(_ identity:PairingIdentity) async throws -> OriginalPending { .init(requests:failed ? [] : [request]) }
    func begin(_ identity:PairingIdentity,job:OriginalJob) async throws -> OriginalBegin {
        if failed { throw PairingFailure.conflict }
        if capacityOnce { capacityOnce = false; throw PairingFailure.capacity }
        if !descriptors.isEmpty { assert(descriptors == job.components.map(\.descriptor)) }
        descriptors = job.components.map(\.descriptor)
        return .init(request_id:request.request_id,state:completeIDs.count == descriptors.count ? "ready":"transferring",resources:descriptors.indices.map {
            .init(ordinal:$0,upload_id:"upload-\($0)",next_offset:bytes["upload-\($0)"]?.count ?? 0,state:completeIDs.contains("upload-\($0)") ? "complete":"active")
        })
    }
    func chunk(_ identity:PairingIdentity,uploadID:String,offset:Int,data:Data) async throws -> OriginalChunk {
        chunks += 1
        var current = bytes[uploadID] ?? Data()
        if offset == current.count { current.append(data); bytes[uploadID] = current }
        else { assert(offset < current.count && current.subdata(in:offset..<offset+data.count) == data, "Replay changed exact bytes") }
        if loseChunk { loseChunk = false; throw PairingFailure.unavailable }
        return .init(upload_id:uploadID,next_offset:offset+data.count,state:"active")
    }
    func complete(_ identity:PairingIdentity,uploadID:String) async throws -> OriginalComplete {
        let ordinal = Int(uploadID.split(separator:"-").last!)!, data = bytes[uploadID]!
        assert(data.count == descriptors[ordinal].size && SHA256.hash(data:data).map{String(format:"%02x",$0)}.joined() == descriptors[ordinal].sha256)
        completeIDs.insert(uploadID)
        if loseComplete { loseComplete = false; throw PairingFailure.unavailable }
        return .init(request_id:request.request_id,upload_id:uploadID,component_id:"component-"+uploadID,state:completeIDs.count == descriptors.count ? "ready":"transferring")
    }
    func fail(_ identity:PairingIdentity,requestID:String,reason:String) async throws { failures += 1; failed = true }
}

@main struct OriginalWorkflowTests {
    @MainActor static func main() async throws {
        let temporary = FileManager.default.temporaryDirectory.appendingPathComponent("memory-original-fixture-"+UUID().uuidString)
        defer { try? FileManager.default.removeItem(at:temporary) }
        let root = temporary.appendingPathComponent("private/originals")
        let files = try OriginalFiles(directory:root), source = try Source(), server = Server(source.request), exporter = Exporter(files)
        let worker = OriginalCoordinator(store:files,source:source,exporter:exporter,files:files,service:server)
        do { _ = try await worker.start(source.request,allowICloud:false); fatalError("Lost chunk not surfaced") } catch PairingFailure.unavailable {}
        let saved = try files.load()!
        assert(saved.stage == .transferring && saved.components[0].offset == 0 && exporter.calls == 1)
        let reopened = try OriginalFiles(directory:root)
        let resumed = OriginalCoordinator(store:reopened,source:source,exporter:exporter,files:reopened,service:server)
        do { _ = try await resumed.resume(); fatalError("Lost completion not surfaced") } catch PairingFailure.unavailable {}
        let interrupted = try reopened.load()!; assert(interrupted.components[0].componentID == nil)
        let done = try await resumed.resume()
        assert(done.stage == .ready && done.components.count == 2 && done.components.allSatisfy{$0.componentID != nil} && exporter.calls == 1)
        print("PASS_original_restart_replays_identical_chunks_and_completion_without_reexport")
        assert(done.components[0].descriptor.original_filename == "still.HEIC" && done.components[1].descriptor.resource_type == "paired_video")
        print("PASS_live_original_parent_ready_only_after_all_exact_components")

        // Another authorized device may already have advanced the immutable
        // manifest between pending-list retrieval and this device's begin.
        let peerFiles = try OriginalFiles(directory:temporary.appendingPathComponent("private/peer")), peerExporter = Exporter(peerFiles)
        let peer = OriginalCoordinator(store:peerFiles,source:source,exporter:peerExporter,files:peerFiles,service:server)
        let peerDone = try await peer.start(source.request,allowICloud:false)
        assert(peerDone.stage == .ready && peerDone.components.count == 2)
        print("PASS_frozen_manifest_can_resume_existing_authorized_resource_offsets")

        source.changed = true; source.offline = true
        do { try await resumed.inspect(); fatalError("Changed source accepted") } catch {}
        let pending = try reopened.load()!; assert(pending.stage == .revocationPending)
        let before = await server.stats()
        do { _ = try await resumed.resume(); fatalError("Pending revocation resumed") } catch {}
        let after = await server.stats(); assert(before.0 == after.0)
        source.offline = false; try await resumed.flushRevocation()
        let revoked = try reopened.load()!; assert(revoked.stage == .revoked)
        print("PASS_original_revision_change_persists_revocation_before_any_retry")

        let missingFiles = try OriginalFiles(directory:temporary.appendingPathComponent("private/missing")), missingSource = try Source()
        let missingExporter = Exporter(missingFiles); missingExporter.omitMotion = true
        let missingServer = Server(missingSource.request)
        let missingWorker = OriginalCoordinator(store:missingFiles,source:missingSource,exporter:missingExporter,files:missingFiles,service:missingServer)
        do { _ = try await missingWorker.start(missingSource.request,allowICloud:false); fatalError("Missing motion claimed original") } catch OriginalFailure.unsupported_resource {}
        let failed = try missingFiles.load()!, failedStats = await missingServer.stats()
        assert(failed.stage == .failed && failedStats.0 == 0 && failedStats.1 == 1)
        print("PASS_missing_live_original_records_failure_without_partial_ready_claim")

        let cloudFiles = try OriginalFiles(directory:temporary.appendingPathComponent("private/cloud")), cloudSource = try Source()
        let cloudExporter = Exporter(cloudFiles); cloudExporter.needsCloud = true
        let cloudServer = Server(cloudSource.request)
        let cloudWorker = OriginalCoordinator(store:cloudFiles,source:cloudSource,exporter:cloudExporter,files:cloudFiles,service:cloudServer)
        do { _ = try await cloudWorker.start(cloudSource.request,allowICloud:false); fatalError("Cloud silently enabled") } catch OriginalFailure.icloud_unavailable {}
        let oldCloudJob = try cloudFiles.load()!
        do { _ = try await cloudWorker.resume(); fatalError("Owner retry bypassed") } catch OriginalFailure.restricted {}
        assert(cloudExporter.choices == [false])
        await cloudServer.ownerRetry()
        do { _ = try await cloudWorker.start(cloudSource.request,allowICloud:true); fatalError("Lost chunk not surfaced") } catch PairingFailure.unavailable {}
        do { _ = try await cloudWorker.resume(); fatalError("Lost complete not surfaced") } catch PairingFailure.unavailable {}
        let cloudDone = try await cloudWorker.resume()
        assert(cloudDone.stage == .ready && cloudDone.id != oldCloudJob.id && cloudDone.allowICloud && cloudExporter.choices == [false,true])
        let retainedCloudFolder = try cloudFiles.folder(oldCloudJob.id)
        assert(FileManager.default.fileExists(atPath:retainedCloudFolder.appendingPathComponent("checkpoint.json").path))
        print("PASS_owner_retry_and_new_explicit_cloud_choice_retain_old_failed_attempt")

        let capacityFiles = try OriginalFiles(directory:temporary.appendingPathComponent("private/capacity")), capacitySource = try Source()
        let capacityExporter = Exporter(capacityFiles), capacityServer = Server(capacitySource.request)
        await capacityServer.rejectCapacityOnce()
        let capacityWorker = OriginalCoordinator(store:capacityFiles,source:capacitySource,exporter:capacityExporter,files:capacityFiles,service:capacityServer)
        do { _ = try await capacityWorker.start(capacitySource.request,allowICloud:false); fatalError("Capacity not surfaced") } catch OriginalFailure.capacity {}
        let capacityJob = try capacityFiles.load()!, capacityStats = await capacityServer.stats()
        assert(capacityJob.stage == .failed && capacityJob.error == "capacity" && capacityJob.components.count == 2 && capacityStats.1 == 1)
        print("PASS_server_capacity_records_failure_and_retains_exact_staged_manifest")

        let component = done.components[0], path = root.appendingPathComponent(done.id).appendingPathComponent(component.filename)
        let sentinel = temporary.appendingPathComponent("sentinel"); try Data("outside".utf8).write(to:sentinel)
        try FileManager.default.removeItem(at:path); try FileManager.default.createSymbolicLink(at:path,withDestinationURL:sentinel)
        do { try reopened.validate(component,jobID:done.id); fatalError("Symlink accepted") } catch {}
        let sentinelBytes = try Data(contentsOf:sentinel); assert(sentinelBytes == Data("outside".utf8))
        print("PASS_original_files_refuse_external_symlinks_and_preserve_target")
        let bounded = try OriginalFiles(directory:temporary.appendingPathComponent("private/bounded"),maximum:20)
        var tiny = done; tiny.components = []; tiny.stage = .staging
        do { try bounded.save(tiny); fatalError("Oversized journal admitted") } catch OriginalFailure.capacity {}
        print("PASS_original_private_retained_storage_refuses_budget_overflow")
    }
}
