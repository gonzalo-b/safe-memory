import Foundation

enum OriginalFailure: String, Error, Codable, Sendable {
    case source_unavailable, permission_changed, revision_changed, icloud_unavailable, capacity, unsupported_resource
    case invalidReceipt, storage, integrity, restricted
    var serverReason: String? {
        switch self {
        case .source_unavailable, .permission_changed, .revision_changed, .icloud_unavailable, .capacity, .unsupported_resource: return rawValue
        default: return nil
        }
    }
}
struct OriginalDescriptor: Codable, Sendable, Equatable {
    let resource_type: String
    let original_filename: String
    let uniform_type_identifier: String
    let size: Int
    let sha256: String
}
enum OriginalPolicy {
    static let maximum = 256 * 1024 * 1024
    static let chunkSize = 1024 * 1024
    static let roles = [1: "photo", 2: "video", 9: "paired_video", 4: "alternate_photo", 3: "audio"]
    static let order = ["photo", "video", "paired_video", "alternate_photo", "audio"]
    static func name(_ text: String) -> Bool {
        (1...255).contains(text.unicodeScalars.count) && text != "." && text != ".." && !text.contains("/") && !text.contains("\\") &&
        !text.unicodeScalars.contains {
            switch $0.properties.generalCategory {
            case .control, .format, .surrogate, .privateUse, .unassigned: return true
            default: return false
            }
        }
    }
    static func uti(_ text: String) -> Bool {
        (1...128).contains(text.utf8.count) && text.range(of: "^[A-Za-z0-9.-]+$", options: .regularExpression) != nil
    }
    private static func checkRoles(_ values: [String], media: String) throws {
        let required: [String]
        switch media { case "photo": required = ["photo"]; case "video": required = ["video"]; case "live": required = ["photo", "paired_video"]; default: throw OriginalFailure.unsupported_resource }
        let allowed = Set(required + (media == "video" ? ["audio"] : ["alternate_photo", "audio"]))
        guard (1...8).contains(values.count), values.allSatisfy({ allowed.contains($0) }),
              required.allSatisfy({ role in values.filter { $0 == role }.count == 1 }) else { throw OriginalFailure.unsupported_resource }
    }
    static func select(_ inventory: [ProbeResource], media: String) throws -> [ProbeResource] {
        // Known edited/adjustment/proxy resources stay in metadata but cannot
        // substitute for an original. New unknown semantics fail closed.
        let knownNonOriginal = Set([5,6,7,8,10,11,12,19])
        guard inventory.allSatisfy({ roles[$0.role] != nil || knownNonOriginal.contains($0.role) }) else { throw OriginalFailure.unsupported_resource }
        let originals = inventory.filter { roles[$0.role] != nil }
        try checkRoles(originals.compactMap { roles[$0.role] }, media: media)
        guard originals.allSatisfy({ name($0.originalFilename) && uti($0.uniformTypeIdentifier) }),
              Set(originals.map { String($0.role) + "\u{0}" + $0.originalFilename + "\u{0}" + $0.uniformTypeIdentifier }).count == originals.count else { throw OriginalFailure.unsupported_resource }
        return originals.sorted {
            let a = order.firstIndex(of: roles[$0.role]!)!, b = order.firstIndex(of: roles[$1.role]!)!
            if a != b { return a < b }
            if $0.originalFilename != $1.originalFilename { return $0.originalFilename.utf8.lexicographicallyPrecedes($1.originalFilename.utf8) }
            return $0.uniformTypeIdentifier < $1.uniformTypeIdentifier
        }
    }
    static func validate(_ resources: [OriginalDescriptor], media: String) throws {
        try checkRoles(resources.map(\.resource_type), media: media)
        var size = 0
        for resource in resources {
            guard name(resource.original_filename), uti(resource.uniform_type_identifier),
                  resource.sha256.range(of: "^[a-f0-9]{64}$", options: .regularExpression) != nil else { throw OriginalFailure.unsupported_resource }
            guard resource.size > 0, resource.size <= maximum - size else { throw OriginalFailure.capacity }
            size += resource.size
        }
        let keys = resources.map { $0.resource_type + "\u{0}" + $0.original_filename + "\u{0}" + $0.uniform_type_identifier }
        guard Set(keys).count == keys.count else { throw OriginalFailure.unsupported_resource }
    }
}
