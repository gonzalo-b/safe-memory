import Foundation

private enum Fixture: Sendable {
    case data(Data, declared: Int?)
    case redirect, unauthorized, stall
    case failure(Int)
}

private final class FixtureState: @unchecked Sendable {
    private let lock = NSLock()
    private var fixture: Fixture = .data(Data("{}".utf8), declared: nil)
    private var requests: [URLRequest] = []
    func reset(_ value: Fixture) { lock.lock(); fixture = value; requests = []; lock.unlock() }
    func record(_ request: URLRequest) -> Fixture { lock.lock(); defer { lock.unlock() }; requests.append(request); return fixture }
    func captured() -> [URLRequest] { lock.lock(); defer { lock.unlock() }; return requests }
}

private final class PairingFixtureProtocol: URLProtocol, @unchecked Sendable {
    static let state = FixtureState()
    override class func canInit(with request: URLRequest) -> Bool { true } // intercept every request; never fall through to a network
    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }
    override func startLoading() {
        switch Self.state.record(request) {
        case .data(let body, let declared):
            var headers = ["Content-Type": "application/json", "Set-Cookie": "fixture=must-not-persist; Secure"]
            if let declared { headers["Content-Length"] = String(declared) }
            let response = HTTPURLResponse(url: request.url!, statusCode: 200, httpVersion: "HTTP/1.1", headerFields: headers)!
            client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
            // Multiple pieces also exercise accumulation rather than only the header limit.
            for offset in stride(from: 0, to: body.count, by: 1024) {
                client?.urlProtocol(self, didLoad: body.subdata(in: offset..<min(body.count, offset + 1024)))
            }
            client?.urlProtocolDidFinishLoading(self)
        case .redirect:
            let response = HTTPURLResponse(url: request.url!, statusCode: 302, httpVersion: "HTTP/1.1", headerFields: ["Location": "https://forbidden.invalid/stolen"])!
            client?.urlProtocol(self, wasRedirectedTo: URLRequest(url: URL(string: "https://forbidden.invalid/stolen")!), redirectResponse: response)
        case .unauthorized:
            client?.urlProtocol(self, didReceive: HTTPURLResponse(url: request.url!, statusCode: 401, httpVersion: "HTTP/1.1", headerFields: ["Content-Type": "application/json"])!, cacheStoragePolicy: .notAllowed)
            client?.urlProtocolDidFinishLoading(self)
        case .failure(let code):
            client?.urlProtocol(self, didReceive: HTTPURLResponse(url: request.url!, statusCode: code, httpVersion: "HTTP/1.1", headerFields: ["Content-Type": "application/json"])!, cacheStoragePolicy: .notAllowed)
            client?.urlProtocolDidFinishLoading(self)
        case .stall: break
        }
    }
    override func stopLoading() {}
}

@main
struct PairingTransportTests {
    static func expect(_ failure: PairingFailure, _ request: URLRequest) async {
        do {
            _ = try await PairingTransfer().perform(request, protocolClasses: [PairingFixtureProtocol.self])
            fatalError("Expected transport refusal")
        } catch let result as PairingFailure { assert(result == failure) }
        catch { fatalError("Unexpected transport result") }
    }

    static func main() async throws {
        let token = String(repeating: "A", count: 43)
        let claim = try PairingRequests.claim(secret: token, deviceName: "Synthetic", libraryID: "local-library", credential: token)
        let status = try PairingRequests.status(deviceID: "synthetic-device", credential: token)
        PairingFixtureProtocol.state.reset(.data(Data("{}".utf8), declared: 2))
        _ = try await PairingTransfer().perform(claim, protocolClasses: [PairingFixtureProtocol.self])
        _ = try await PairingTransfer().perform(status, protocolClasses: [PairingFixtureProtocol.self])
        let sent = PairingFixtureProtocol.state.captured()
        assert(sent.count == 2)
        assert(sent[0].value(forHTTPHeaderField: "Authorization") == nil)
        assert(sent[1].value(forHTTPHeaderField: "Authorization") == "Bearer " + token)
        assert(sent.allSatisfy { $0.value(forHTTPHeaderField: "Cookie") == nil && $0.value(forHTTPHeaderField: "Referer") == nil })
        print("PASS isolated_ephemeral_requests_no_cookie_reuse")

        PairingFixtureProtocol.state.reset(.redirect)
        await expect(.redirected, status)
        assert(PairingFixtureProtocol.state.captured().count == 1)
        print("PASS redirected_bearer_never_sent_to_destination")

        PairingFixtureProtocol.state.reset(.data(Data("{}".utf8), declared: nil))
        var bad = status; bad.url = URL(string: "https://forbidden.invalid/api/device/status")!
        await expect(.forbiddenOrigin, bad)
        assert(PairingFixtureProtocol.state.captured().isEmpty)
        print("PASS invalid_origin_refused_before_request")

        PairingFixtureProtocol.state.reset(.data(Data(), declared: 8193))
        await expect(.bodyLimit, status)
        PairingFixtureProtocol.state.reset(.data(Data(repeating: 65, count: 8193), declared: nil))
        await expect(.bodyLimit, status)
        PairingFixtureProtocol.state.reset(.data(Data(repeating: 65, count: 8192), declared: nil))
        let boundary = try await PairingTransfer().perform(status, protocolClasses: [PairingFixtureProtocol.self])
        assert(boundary.count == 8192)
        print("PASS_declared_and_streamed_body_bounds")

        PairingFixtureProtocol.state.reset(.unauthorized)
        await expect(.unauthorized, status)
        print("PASS_unconfirmed_status_is_not_binding")

        PairingFixtureProtocol.state.reset(.stall)
        let pending = Task { try await PairingTransfer().perform(status, protocolClasses: [PairingFixtureProtocol.self]) }
        for _ in 0..<200 {
            if !PairingFixtureProtocol.state.captured().isEmpty { break }
            try await Task.sleep(for: .milliseconds(2))
        }
        pending.cancel()
        do { _ = try await pending.value; fatalError("Cancellation did not stop request") }
        catch PairingFailure.cancelled {} catch is CancellationError {} catch { fatalError("Unexpected cancellation") }
        print("PASS_cancellation_completes_pending_request")

        let permissionRequest = try NativeRequests.make("/api/device/permission", body: ["device_id": "synthetic-device", "permission": "denied"], credential: token)
        PairingFixtureProtocol.state.reset(.data(Data("{\"ok\":true}".utf8), declared: nil))
        _ = try await PairingTransfer().perform(permissionRequest, protocolClasses: [PairingFixtureProtocol.self], mode: .metadata)
        assert(PairingFixtureProtocol.state.captured().first?.value(forHTTPHeaderField: "Authorization") == "Bearer " + token)
        PairingFixtureProtocol.state.reset(.redirect)
        do {
            _ = try await PairingTransfer().perform(permissionRequest, protocolClasses: [PairingFixtureProtocol.self], mode: .metadata)
            fatalError("Metadata redirect admitted")
        } catch PairingFailure.redirected {}
        assert(PairingFixtureProtocol.state.captured().count == 1)
        PairingFixtureProtocol.state.reset(.data(Data(repeating: 65, count: NativeRequests.responseLimit + 1), declared: nil))
        do {
            _ = try await PairingTransfer().perform(permissionRequest, protocolClasses: [PairingFixtureProtocol.self], mode: .metadata)
            fatalError("Metadata response limit admitted")
        } catch PairingFailure.bodyLimit {}
        print("PASS_metadata_transport_keeps_bearer_redirect_and_body_guards")

        struct Chunk: Encodable { let device_id: String; let upload_id: String; let offset: Int; let data_base64: String }
        let binary = Data(repeating: 0x65, count: 1024 * 1024)
        let chunk = try NativeRequests.make("/api/device/media/chunk", body: Chunk(device_id: "synthetic-device", upload_id: "upload", offset: 0, data_base64: binary.base64EncodedString()), credential: token)
        assert(chunk.httpBody!.count < 2 * 1024 * 1024 && chunk.httpBody!.count > 1024 * 1024)
        let object = try JSONSerialization.jsonObject(with: chunk.httpBody!) as! [String: Any]
        assert(Data(base64Encoded: object["data_base64"] as! String) == binary && object["credential"] == nil)
        PairingFixtureProtocol.state.reset(.data(Data("{}".utf8), declared: 2))
        _ = try await PairingTransfer().perform(chunk, protocolClasses: [PairingFixtureProtocol.self], mode: .metadata)
        assert(PairingFixtureProtocol.state.captured().count == 1)
        var wrongOrigin = chunk; wrongOrigin.url = URL(string: "https://memory.lazyagent.ai:443/api/device/media/chunk")!
        do { try NativeRequests.validate(wrongOrigin); fatalError("Alternate URL admitted") } catch PairingFailure.forbiddenOrigin {}
        var tooLarge = chunk; tooLarge.httpBody = Data(repeating: 0x61, count: 2 * 1024 * 1024 + 1)
        do { try NativeRequests.validate(tooLarge); fatalError("Unbounded media body admitted") } catch PairingFailure.bodyLimit {}
        PairingFixtureProtocol.state.reset(.redirect)
        do { _ = try await PairingTransfer().perform(chunk, protocolClasses: [PairingFixtureProtocol.self], mode: .metadata); fatalError("Media redirect followed") } catch PairingFailure.redirected {}
        assert(PairingFixtureProtocol.state.captured().count == 1)
        for (code, expected) in [(507, PairingFailure.capacity), (409, PairingFailure.conflict)] {
            PairingFixtureProtocol.state.reset(.failure(code))
            do { _ = try await PairingTransfer().perform(chunk, protocolClasses: [PairingFixtureProtocol.self], mode: .metadata); fatalError("Server refusal accepted") }
            catch let failure as PairingFailure { assert(failure == expected) }
        }
        print("PASS_media_chunk_bounds_no_redirect_or_cookie_and_explicit_capacity")
    }
}
