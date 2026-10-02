import Foundation

/// No URL is caller-configurable; each operation uses an isolated ephemeral
/// session. These endpoints carry pairing identity only, never Photos content.
struct PairingTransport: Sendable {
    func claim(secret: String, deviceName: String, libraryID: String, credential: String) async throws -> PairingClaim {
        let request = try PairingRequests.claim(secret: secret, deviceName: deviceName, libraryID: libraryID, credential: credential)
        let data = try await PairingTransfer().perform(request)
        return try PairingRequests.claimResult(data, credential: credential)
    }
    func status(deviceID: String, credential: String) async throws -> PairingBinding {
        let data = try await PairingTransfer().perform(PairingRequests.status(deviceID: deviceID, credential: credential))
        return try PairingRequests.binding(data, deviceID: deviceID)
    }
}

final class PairingTransfer: NSObject, URLSessionDataDelegate, URLSessionTaskDelegate, @unchecked Sendable {
    enum Mode: Sendable { case pairing, metadata }
    private let lock = NSLock()
    private let bridge = ExportRequestBridge<Data>()
    private var received = Data()
    private var failure: PairingFailure?
    private var accepted = false
    private var session: URLSession?
    private var started = false
    private var responseLimit = PairingRequests.maximumBody

    // protocolClasses is an internal fixture hook, never populated by the app.
    func perform(_ request: URLRequest, protocolClasses: [AnyClass]? = nil, mode: Mode = .pairing) async throws -> Data {
        if mode == .pairing { try PairingRequests.validate(request) }
        else { try NativeRequests.validate(request) }
        try Task.checkCancellation()
        return try await withTaskCancellationHandler {
            try await withCheckedThrowingContinuation { continuation in
                lock.lock()
                guard !started else { lock.unlock(); continuation.resume(throwing: PairingFailure.invalidInput); return }
                started = true
                responseLimit = mode == .pairing ? PairingRequests.maximumBody : NativeRequests.responseLimit
                lock.unlock()
                bridge.install(continuation)
                let config = URLSessionConfiguration.ephemeral
                config.urlCache = nil; config.urlCredentialStorage = nil; config.httpCookieStorage = nil
                config.httpShouldSetCookies = false; config.httpCookieAcceptPolicy = .never
                config.requestCachePolicy = .reloadIgnoringLocalAndRemoteCacheData
                config.timeoutIntervalForRequest = 15; config.timeoutIntervalForResource = 20
                config.httpMaximumConnectionsPerHost = 1
                if let protocolClasses { config.protocolClasses = protocolClasses }
                let current = URLSession(configuration: config, delegate: self, delegateQueue: nil)
                lock.lock(); session = current; lock.unlock()
                let task = current.dataTask(with: request)
                bridge.onCancel { task.cancel(); current.invalidateAndCancel() }
                task.resume()
            }
        } onCancel: { bridge.cancel(PairingFailure.cancelled) }
    }

    func urlSession(_ session: URLSession, task: URLSessionTask, willPerformHTTPRedirection response: HTTPURLResponse, newRequest request: URLRequest, completionHandler: @escaping @Sendable (URLRequest?) -> Void) {
        lock.lock(); failure = .redirected; lock.unlock()
        completionHandler(nil)
        task.cancel()
    }

    func urlSession(_ session: URLSession, task: URLSessionTask, didReceive challenge: URLAuthenticationChallenge, completionHandler: @escaping @Sendable (URLSession.AuthChallengeDisposition, URLCredential?) -> Void) {
        // System certificate validation only. No client certificates, saved
        // passwords, interactive challenges or custom trust exceptions.
        completionHandler(challenge.protectionSpace.authenticationMethod == NSURLAuthenticationMethodServerTrust ? .performDefaultHandling : .cancelAuthenticationChallenge, nil)
    }

    func urlSession(_ session: URLSession, didReceive challenge: URLAuthenticationChallenge, completionHandler: @escaping @Sendable (URLSession.AuthChallengeDisposition, URLCredential?) -> Void) {
        completionHandler(challenge.protectionSpace.authenticationMethod == NSURLAuthenticationMethodServerTrust ? .performDefaultHandling : .cancelAuthenticationChallenge, nil)
    }

    func urlSession(_ session: URLSession, dataTask: URLSessionDataTask, didReceive response: URLResponse, completionHandler: @escaping @Sendable (URLSession.ResponseDisposition) -> Void) {
        lock.lock(); defer { lock.unlock() }
        guard let http = response as? HTTPURLResponse, http.url == dataTask.originalRequest?.url else {
            failure = .invalidResponse; completionHandler(.cancel); return
        }
        guard http.statusCode == 200 || http.statusCode == 201 else {
            failure = (300...399).contains(http.statusCode) ? .redirected : ([401, 403].contains(http.statusCode) ? .unauthorized : .unavailable)
            completionHandler(.cancel); return
        }
        guard http.mimeType == "application/json" else { failure = .invalidResponse; completionHandler(.cancel); return }
        guard response.expectedContentLength <= Int64(responseLimit) else { failure = .bodyLimit; completionHandler(.cancel); return }
        accepted = true; completionHandler(.allow)
    }

    func urlSession(_ session: URLSession, dataTask: URLSessionDataTask, didReceive data: Data) {
        lock.lock()
        guard failure == nil, accepted, data.count <= responseLimit - received.count else {
            failure = failure ?? .bodyLimit; lock.unlock(); dataTask.cancel(); return
        }
        received.append(data); lock.unlock()
    }

    func urlSession(_ session: URLSession, task: URLSessionTask, didCompleteWithError error: Error?) {
        lock.lock()
        let result: Result<Data, Error>
        if let failure { result = .failure(failure) }
        else if error != nil || !accepted { result = .failure(PairingFailure.unavailable) }
        else { result = .success(received) }
        received = Data(); self.session = nil
        lock.unlock()
        bridge.finish(result)
        session.invalidateAndCancel()
    }
}
