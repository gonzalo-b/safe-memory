import Foundation

private final class Counter: @unchecked Sendable {
    private let lock = NSLock()
    private var count = 0
    func increment() { lock.lock(); count += 1; lock.unlock() }
    func value() -> Int { lock.lock(); defer { lock.unlock() }; return count }
}

@main
struct ExportBridgeTests {
    static func main() async throws {
        let early = ExportRequestBridge<Int>()
        early.finish(.success(7)); early.finish(.success(9))
        let value = try await withCheckedThrowingContinuation { early.install($0) }
        assert(value == 7)
        print("PASS synchronous_callback_keeps_first_result")

        let cancelled = ExportRequestBridge<Int>()
        cancelled.cancel()
        let calls = Counter()
        cancelled.onCancel { calls.increment() }
        do {
            _ = try await withCheckedThrowingContinuation { cancelled.install($0) }
            fatalError("Cancellation must finish an uninstalled continuation")
        } catch ExportFailure.cancelled {} catch { fatalError("Wrong cancellation result") }
        assert(calls.value() == 1)
        print("PASS cancellation_before_request_id_cancels_late_id")

        let pending = ExportRequestBridge<Int>()
        let pendingCalls = Counter()
        pending.onCancel { pendingCalls.increment() }
        do {
            _ = try await withCheckedThrowingContinuation {
                pending.install($0)
                pending.cancel(ExportFailure.limitExceeded)
                pending.finish(.success(42))
            }
            fatalError("Failure must not turn into a later success")
        } catch ExportFailure.limitExceeded {} catch { fatalError("Wrong limit result") }
        assert(pendingCalls.value() == 1)
        print("PASS bounded_resource_failure_resumes_once_and_cancels")

        for _ in 0..<200 {
            let race = ExportRequestBridge<Int>()
            await withTaskGroup(of: Void.self) { group in
                group.addTask { race.finish(.success(1)) }
                group.addTask { race.finish(.success(2)) }
                group.addTask { race.cancel() }
            }
            do {
                let result = try await withCheckedThrowingContinuation { race.install($0) }
                assert(result == 1 || result == 2)
            } catch ExportFailure.cancelled {} catch { fatalError("Unexpected race result") }
        }
        print("PASS concurrent_completion_and_cancellation_resume_once")
    }
}
