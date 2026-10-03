import Foundation

@main struct OriginalPolicyTests {
    static func resource(_ role: Int, _ name: String, _ uti: String = "public.jpeg") -> ProbeResource {
        .init(role: role, assetLocalIdentifier: "synthetic", originalFilename: name, uniformTypeIdentifier: uti, pixelWidth: 1, pixelHeight: 1)
    }
    static func main() throws {
        let photo = resource(1, "still.HEIC", "public.heic"), raw = resource(4, "RAW.DNG", "com.adobe.raw-image")
        let motion = resource(9, "motion.MOV", "com.apple.quicktime-movie"), audio = resource(3, "audio.WAV", "com.microsoft.waveform-audio")
        let edited = resource(5, "edited.JPG")
        let selected = try OriginalPolicy.select([motion, edited, raw, photo, audio], media: "live")
        assert(selected.map(\.role) == [1, 9, 4, 3])
        let reordered = try OriginalPolicy.select([audio, photo, raw, edited, motion], media: "live")
        assert(reordered.map(\.originalFilename) == selected.map(\.originalFilename))
        print("PASS_original_live_raw_audio_inventory_deterministic_without_edited_substitution")
        for rows in [[motion, edited], [photo, photo, motion], [resource(19,"proxy.JPG")], [photo, resource(999,"unknown")]] {
            do { _ = try OriginalPolicy.select(rows, media: "live"); fatalError("Ambiguous/missing/unknown original admitted") } catch OriginalFailure.unsupported_resource {}
        }
        print("PASS_missing_ambiguous_proxy_and_unknown_resources_refuse_original_claim")
        for name in [".", "..", "../escape", "dir\\file", "bad\nname", "private\u{E000}", String(repeating: "x", count: 256)] {
            do { _ = try OriginalPolicy.select([resource(1,name)], media: "photo"); fatalError("Unsafe filename") } catch OriginalFailure.unsupported_resource {}
        }
        do { _ = try OriginalPolicy.select([resource(1,"safe","bad/uti")], media: "photo"); fatalError("Invalid UTI") } catch OriginalFailure.unsupported_resource {}
        print("PASS_source_filenames_and_uti_are_provenance_never_paths")
        let digest = String(repeating:"a",count:64)
        let one = OriginalDescriptor(resource_type:"photo",original_filename:"synthetic.jpg",uniform_type_identifier:"public.jpeg",size:OriginalPolicy.maximum,sha256:digest)
        try OriginalPolicy.validate([one],media:"photo")
        do { try OriginalPolicy.validate([one, .init(resource_type:"audio",original_filename:"audio.wav",uniform_type_identifier:"public.wav",size:1,sha256:digest)],media:"photo"); fatalError("Budget overflow") } catch OriginalFailure.capacity {}
        print("PASS_original_manifest_total_size_and_resource_count_are_bounded")
    }
}
