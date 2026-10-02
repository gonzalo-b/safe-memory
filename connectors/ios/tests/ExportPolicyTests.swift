import Foundation

@main
struct ExportPolicyTests {
    static func main() throws {
        let base = ExportAssetScope(id: "synthetic", hidden: false, sharedAlbum: false, collection: "personal", media: .photo)
        let consent = ExportConsent()
        let scope = try ExportPlan(selectedIDs: ["synthetic"], authorized: [base], consent: consent)
        assert(scope.assets.count == 1)
        func rejected(_ operation: () throws -> Void) {
            do { try operation(); fatalError("Expected restricted export") } catch {}
        }
        rejected { _ = try ExportPlan(selectedIDs: ["other"], authorized: [base], consent: consent) }
        rejected { _ = try ExportPlan(selectedIDs: ["synthetic", "synthetic"], authorized: [base], consent: consent) }
        let hundred = (0..<100).map { ExportAssetScope(id: "synthetic-\($0)", hidden: false, sharedAlbum: false, collection: "personal", media: .photo) }
        let maximum = try ExportPlan(selectedIDs: hundred.map(\.id), authorized: hundred, consent: consent)
        assert(maximum.assets.map(\.id) == hundred.map(\.id))
        rejected { _ = try ExportPlan(selectedIDs: hundred.map(\.id) + ["extra"], authorized: hundred + [base], consent: consent) }
        rejected { _ = try ExportPlan(selectedIDs: ["synthetic"], authorized: [base, base], consent: consent) }
        rejected { _ = try ExportPlan(selectedIDs: [], authorized: [base], consent: consent) }
        for scope in [ExportAssetScope(id: "synthetic", hidden: true, sharedAlbum: false, collection: "personal", media: .photo),
                      ExportAssetScope(id: "synthetic", hidden: false, sharedAlbum: true, collection: "personal", media: .photo),
                      ExportAssetScope(id: "synthetic", hidden: false, sharedAlbum: false, collection: "unknown", media: .photo)] {
            rejected { _ = try ExportPlan(selectedIDs: ["synthetic"], authorized: [scope], consent: consent) }
        }
        let unknown = ExportAssetScope(id: "synthetic", hidden: false, sharedAlbum: false, collection: "unknown", media: .live)
        _ = try ExportPlan(selectedIDs: ["synthetic"], authorized: [unknown], consent: ExportConsent(includeSharedLibrary: true))
        assert(consent.allowICloud == false)
        assert(ExportDimensions.fit(width: 4000, height: 3000) == ExportDimensions(width: 2048, height: 1536))
        assert(ExportDimensions.fit(width: 600, height: 900) == ExportDimensions(width: 600, height: 900))
        assert(ExportDimensions.fit(width: 0, height: 2) == nil)
        assert(ExportMedia.live.requiredRoles == [.cover, .motion])
        assert(!ExportMedia.live.isComplete([.cover]))
        assert(ExportMedia.live.isComplete([.cover, .motion]))
        assert(!ExportMedia.video.isComplete([.cover, .motion]))
        var budget = ExportBudget(limit: 10)
        try budget.reserve(7)
        rejected { try budget.reserve(4) }
        assert(budget.used == 7)
        rejected { try budget.reserve(-1) }
        print("PASS selected_ids_only_and_bounded")
        print("PASS hidden_shared_and_unknown_fail_closed")
        print("PASS cloud_is_opt_in")
        print("PASS dimensions_bounded_without_upscale")
        print("PASS live_requires_linked_motion")
        print("PASS budget_limit_is_atomic")
    }
}
