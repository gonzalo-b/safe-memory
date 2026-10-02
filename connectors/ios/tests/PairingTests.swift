import Foundation

@main
struct PairingTests {
    static func main() throws {
        let token = Data(repeating: 0, count: 32).base64EncodedString().replacingOccurrences(of: "=", with: "")
        assert(PairingRequests.canonicalToken(token))
        assert(!PairingRequests.canonicalToken(String(token.dropLast()) + "B"))
        let claim = try PairingRequests.claim(secret: token, deviceName: "Synthetic iPhone", libraryID: "local-library-synthetic", credential: token)
        assert(claim.url?.absoluteString == "https://memory.lazyagent.ai/api/device/claim")
        assert(claim.httpMethod == "POST")
        assert(claim.value(forHTTPHeaderField: "Authorization") == nil)
        assert(claim.value(forHTTPHeaderField: "Cookie") == nil)
        let body = try JSONSerialization.jsonObject(with: claim.httpBody!) as! [String: String]
        assert(Set(body.keys) == ["secret", "device_name", "library_id", "credential"])
        let status = try PairingRequests.status(deviceID: "synthetic-device", credential: token)
        assert(status.value(forHTTPHeaderField: "Authorization") == "Bearer " + token)
        let statusBody = try JSONSerialization.jsonObject(with: status.httpBody!) as! [String: String]
        assert(statusBody == ["device_id": "synthetic-device"])
        assert(!status.httpShouldHandleCookies)
        print("PASS canonical_requests_isolate_credentials_and_headers")
        for origin in ["http://memory.lazyagent.ai", "https://other.invalid", "https://memory.lazyagent.ai.evil.invalid", "https://user:pass@memory.lazyagent.ai", "https://memory.lazyagent.ai:443", "https://memory.lazyagent.ai/path", "https://memory.lazyagent.ai?x", "https://memory.lazyagent.ai#x"] {
            do { try PairingRequests.validateOrigin(origin); fatalError("Origin admitted") } catch {}
        }
        print("PASS strict_https_origin")
        let fingerprint = PairingRequests.fingerprint(token)
        // Independent hashlib.sha256(("A" * 43).encode("utf-8")) fixture,
        // deliberately not the SHA256 of the decoded 32 zero bytes.
        assert(fingerprint == "0f007385b6f9d4b7eeb2748605afe1a984a0a3bfa3f014d09e2a784ce9e5cd1a")
        let response = try JSONSerialization.data(withJSONObject: ["claim_id": "synthetic-device", "fingerprint": fingerprint, "expires_at": 123456])
        let parsed = try PairingRequests.claimResult(response, credential: token)
        assert(parsed.claimID == "synthetic-device")
        let wrong = try JSONSerialization.data(withJSONObject: ["claim_id": "synthetic-device", "fingerprint": String(repeating: "0", count: 64), "expires_at": 123456])
        do { _ = try PairingRequests.claimResult(wrong, credential: token); fatalError("Fingerprint mismatch admitted") } catch {}
        for access in [true, 1] as [Any] {
            let data = try JSONSerialization.data(withJSONObject: ["device_id": "synthetic-device", "owner_id": "owner", "connection_id": "connection", "vault_id": "vault", "data_access": access])
            do { _ = try PairingRequests.binding(data, deviceID: "synthetic-device"); fatalError("Data access admitted") } catch {}
        }
        let allowed = try JSONSerialization.data(withJSONObject: ["device_id": "synthetic-device", "owner_id": "owner", "connection_id": "connection", "vault_id": "vault", "data_access": false])
        let binding = try PairingRequests.binding(allowed, deviceID: "synthetic-device")
        assert(!binding.dataAccess)
        do { _ = try PairingRequests.binding(allowed, deviceID: "other-device"); fatalError("Cross-device binding admitted") } catch {}
        print("PASS_response_identity_and_no_data_access")
    }
}
