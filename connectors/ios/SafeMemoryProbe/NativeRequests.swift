import Foundation

enum NativeJSON {
    // Stable sorted keys and explicit ASCII escaping. Nonfinite numbers fail.
    static func encode<T: Encodable>(_ value: T) throws -> Data {
        let encoder = JSONEncoder(); encoder.outputFormatting = [.sortedKeys, .withoutEscapingSlashes]
        let text = String(decoding: try encoder.encode(value), as: UTF8.self)
        var ascii = ""
        for unit in text.utf16 {
            if unit < 128 { ascii.append(Character(UnicodeScalar(unit)!)) }
            else { ascii += String(format: "\\u%04x", unit) }
        }
        return Data(ascii.utf8)
    }
}

enum NativeRequests {
    static let responseLimit = 256 * 1024
    static let appendLimit = 1024 * 1024
    static let paths: [String: Set<String>] = [
        "/api/device/permission": ["device_id", "permission"],
        "/api/device/ingest/begin": ["device_id", "request_key", "permission", "phase", "selected_ids"],
        "/api/device/ingest/append": ["device_id", "run_id", "batch_key", "sequence", "checkpoint", "assets"],
        "/api/device/ingest/finish": ["device_id", "run_id"]
    ]
    static func make<T: Encodable>(_ path: String, body: T, credential: String) throws -> URLRequest {
        guard paths[path] != nil, PairingRequests.canonicalToken(credential), let url = URL(string: PairingRequests.origin + path) else { throw PairingFailure.invalidInput }
        var request = URLRequest(url: url, cachePolicy: .reloadIgnoringLocalAndRemoteCacheData, timeoutInterval: 15)
        request.httpMethod = "POST"; request.httpShouldHandleCookies = false
        request.allHTTPHeaderFields = ["Content-Type": "application/json", "Accept": "application/json", "Authorization": "Bearer " + credential]
        request.httpBody = try NativeJSON.encode(body)
        try validate(request)
        return request
    }
    static func validate(_ request: URLRequest) throws {
        guard let url = request.url, let c = URLComponents(url: url, resolvingAgainstBaseURL: false),
              c.scheme == "https", c.host == "memory.lazyagent.ai", c.port == nil, c.user == nil, c.password == nil,
              c.query == nil, c.fragment == nil, let keys = paths[c.path], request.httpMethod == "POST", !request.httpShouldHandleCookies,
              request.httpBodyStream == nil, let body = request.httpBody else { throw PairingFailure.forbiddenOrigin }
        guard body.count <= (c.path.hasSuffix("/append") ? appendLimit : 65536) else { throw PairingFailure.bodyLimit }
        let headers = Set((request.allHTTPHeaderFields ?? [:]).keys.map { $0.lowercased() })
        let bearer = request.value(forHTTPHeaderField: "Authorization") ?? ""
        guard headers == ["content-type", "accept", "authorization"], request.value(forHTTPHeaderField: "Content-Type") == "application/json",
              request.value(forHTTPHeaderField: "Accept") == "application/json", bearer.hasPrefix("Bearer "), PairingRequests.canonicalToken(String(bearer.dropFirst(7))),
              let object = try JSONSerialization.jsonObject(with: body) as? [String: Any], Set(object.keys) == keys,
              let device = object["device_id"] as? String, PairingRequests.identifier(device) else { throw PairingFailure.invalidInput }
    }
}
