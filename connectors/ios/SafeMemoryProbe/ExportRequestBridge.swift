import Foundation

// Photos can invoke callbacks before returning the request ID, and cancellation
// can race completion. This bridge resumes exactly once and cancels late IDs.
final class ExportRequestBridge<Value: Sendable>: @unchecked Sendable {
    private let lock = NSLock()
    private var continuation: CheckedContinuation<Value, Error>?
    private var result: Result<Value, Error>?
    private var cancellation: (@Sendable () -> Void)?
    private var stopped = false

    func install(_ continuation: CheckedContinuation<Value, Error>) {
        lock.lock()
        if let result { lock.unlock(); continuation.resume(with: result) }
        else { self.continuation = continuation; lock.unlock() }
    }
    func onCancel(_ action: @escaping @Sendable () -> Void) {
        lock.lock(); cancellation = action; let cancelNow = stopped; lock.unlock()
        if cancelNow { action() }
    }
    func finish(_ value: Result<Value, Error>) {
        lock.lock()
        guard result == nil else { lock.unlock(); return }
        result = value
        let pending = continuation; continuation = nil; lock.unlock()
        pending?.resume(with: value)
    }
    func cancel(_ error: Error = ExportFailure.cancelled) {
        lock.lock(); stopped = true; let action = cancellation; lock.unlock()
        finish(.failure(error)); action?()
    }
}
