import Foundation
import CryptoKit

enum PairingFailure: Error, Sendable {
    case invalidInput, forbiddenOrigin, invalidResponse, redirected, bodyLimit
    case unauthorized, unavailable, cancelled, secureStorage, relinkRequired
    case capacity, conflict
}

struct PairingClaim: Decodable, Sendable {
    let claimID: String
    let fingerprint: String
    let expiresAt: Int64
    enum CodingKeys: String, CodingKey { case claimID = "claim_id", fingerprint, expiresAt = "expires_at" }
}

struct PairingBinding: Decodable, Sendable {
    let deviceID: String
    let ownerID: String
    let connectionID: String
    let vaultID: String
    let dataAccess: Bool
    enum CodingKeys: String, CodingKey {
        case deviceID = "device_id", ownerID = "owner_id", connectionID = "connection_id", vaultID = "vault_id", dataAccess = "data_access"
    }
}

enum PairingRequests {
    static let origin = "https://memory.lazyagent.ai"
    static let maximumBody = 8192

    static func canonicalToken(_ value: String) -> Bool {
        guard value.utf8.count == 43, value.allSatisfy({ $0.isASCII && ($0.isLetter || $0.isNumber || $0 == "_" || $0 == "-") }),
              let raw = Data(base64Encoded: value.replacingOccurrences(of: "-", with: "+").replacingOccurrences(of: "_", with: "/") + "="), raw.count == 32 else { return false }
        return raw.base64EncodedString().replacingOccurrences(of: "+", with: "-").replacingOccurrences(of: "/", with: "_").replacingOccurrences(of: "=", with: "") == value
    }

    static func fingerprint(_ credential: String) -> String {
        SHA256.hash(data: Data(credential.utf8)).map { String(format: "%02x", $0) }.joined()
    }

    static func identifier(_ value: String) -> Bool {
        (1...128).contains(value.utf8.count) && value.allSatisfy { $0.isASCII && ($0.isLetter || $0.isNumber || $0 == "-" || $0 == "_") }
    }

    static func text(_ value: String, maximum: Int) -> Bool {
        guard (1...maximum).contains(value.unicodeScalars.count), value == value.trimmingCharacters(in: .whitespacesAndNewlines) else { return false }
        return value.unicodeScalars.allSatisfy {
            switch $0.properties.generalCategory {
            case .control, .format, .surrogate, .privateUse, .unassigned: return false
            default: return true
            }
        }
    }

    static func validateOrigin(_ value: String) throws {
        guard value == origin else { throw PairingFailure.forbiddenOrigin }
    }

    static func claim(secret: String, deviceName: String, libraryID: String, credential: String) throws -> URLRequest {
        guard canonicalToken(secret), canonicalToken(credential), text(deviceName, maximum: 100), text(libraryID, maximum: 256) else { throw PairingFailure.invalidInput }
        return try request(path: "/api/device/claim", values: ["secret": secret, "device_name": deviceName, "library_id": libraryID, "credential": credential], credential: nil)
    }

    static func status(deviceID: String, credential: String) throws -> URLRequest {
        guard identifier(deviceID), canonicalToken(credential) else { throw PairingFailure.invalidInput }
        return try request(path: "/api/device/status", values: ["device_id": deviceID], credential: credential)
    }

    private static func request(path: String, values: [String: String], credential: String?) throws -> URLRequest {
        try validateOrigin(origin)
        guard let url = URL(string: origin + path) else { throw PairingFailure.forbiddenOrigin }
        var result = URLRequest(url: url, cachePolicy: .reloadIgnoringLocalAndRemoteCacheData, timeoutInterval: 15)
        result.httpMethod = "POST"
        result.httpShouldHandleCookies = false
        result.allHTTPHeaderFields = ["Content-Type": "application/json", "Accept": "application/json"]
        if let credential { result.allHTTPHeaderFields?["Authorization"] = "Bearer " + credential }
        result.httpBody = try JSONSerialization.data(withJSONObject: values, options: [.sortedKeys])
        guard result.httpBody!.count <= maximumBody else { throw PairingFailure.bodyLimit }
        return result
    }

    static func validate(_ request: URLRequest) throws {
        guard let url = request.url, let components = URLComponents(url: url, resolvingAgainstBaseURL: false),
              components.scheme == "https", components.host == "memory.lazyagent.ai", components.port == nil,
              components.user == nil, components.password == nil, components.query == nil, components.fragment == nil,
              ["/api/device/claim", "/api/device/status"].contains(components.path), request.httpMethod == "POST",
              !request.httpShouldHandleCookies, let body = request.httpBody, body.count <= maximumBody,
              request.httpBodyStream == nil else { throw PairingFailure.forbiddenOrigin }
        let headers = Set((request.allHTTPHeaderFields ?? [:]).keys.map { $0.lowercased() })
        let allowed: Set<String> = components.path == "/api/device/status" ? ["content-type", "accept", "authorization"] : ["content-type", "accept"]
        guard headers == allowed, request.value(forHTTPHeaderField: "Content-Type") == "application/json",
              request.value(forHTTPHeaderField: "Accept") == "application/json" else { throw PairingFailure.invalidInput }
        guard let values = try JSONSerialization.jsonObject(with: body) as? [String: String] else { throw PairingFailure.invalidInput }
        if components.path == "/api/device/claim" {
            guard Set(values.keys) == ["secret", "credential", "library_id", "device_name"],
                  canonicalToken(values["secret"] ?? ""), canonicalToken(values["credential"] ?? ""),
                  text(values["device_name"] ?? "", maximum: 100), text(values["library_id"] ?? "", maximum: 256) else { throw PairingFailure.invalidInput }
        } else {
            let bearer = request.value(forHTTPHeaderField: "Authorization") ?? ""
            guard Set(values.keys) == ["device_id"], identifier(values["device_id"] ?? ""), bearer.hasPrefix("Bearer "), canonicalToken(String(bearer.dropFirst(7))) else { throw PairingFailure.invalidInput }
        }
    }

    private static func keys(_ data: Data, equal expected: Set<String>) throws {
        guard data.count <= maximumBody, let object = try JSONSerialization.jsonObject(with: data) as? [String: Any], Set(object.keys) == expected else { throw PairingFailure.invalidResponse }
    }

    static func claimResult(_ data: Data, credential: String) throws -> PairingClaim {
        try keys(data, equal: ["claim_id", "fingerprint", "expires_at"])
        let claim = try JSONDecoder().decode(PairingClaim.self, from: data)
        guard identifier(claim.claimID), claim.fingerprint == fingerprint(credential), claim.expiresAt > 0 else { throw PairingFailure.invalidResponse }
        return claim
    }

    static func binding(_ data: Data, deviceID: String) throws -> PairingBinding {
        try keys(data, equal: ["device_id", "owner_id", "connection_id", "vault_id", "data_access"])
        let binding = try JSONDecoder().decode(PairingBinding.self, from: data)
        guard binding.deviceID == deviceID, [binding.deviceID, binding.ownerID, binding.connectionID, binding.vaultID].allSatisfy(identifier), !binding.dataAccess else { throw PairingFailure.invalidResponse }
        return binding
    }
}
