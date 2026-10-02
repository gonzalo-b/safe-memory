export interface Session { owner: { id: string; display_name: string }; csrf_token: string; fixture: boolean }
export interface Source { id: string; name: string; permission: string; status: string; last_success: string | null; index_count: number; media_ready_count: number; include_hidden?: 0 | 1 | boolean; include_shared_library?: 0 | 1 | boolean; include_shared_albums?: 0 | 1 | boolean }
export interface Sources { sources: Source[]; fixture: boolean }
export interface Overview extends Sources {
  vault: { id: string; domain: string } | null;
  counts: { assets: number; media_ready: number; artifacts: number; trips: number };
  coverage: { index_state: string; media_state: string; last_success: string | null };
}
export interface SafeEvent { id: string; action: string; outcome?: string; status?: string; count?: number; created_at: number; completed_at?: number | null }
export interface Debug {
  version: string; environment: string; health: { storage: string; audit: string };
  operations: SafeEvent[]; audit: SafeEvent[]; fixture: boolean;
}
export interface PairingIntent { pairing_id: string; secret: string; expires_at: number }
export interface PairingClaim { claim_id: string; device_name: string; fingerprint: string; expires_at: number }
export interface Device { device_id: string; connection_id: string; device_name: string; fingerprint: string; created_at: number; revoked_at: number | null }

export interface PhotoMetadata { id: string; native_id: string; hidden: number | boolean; collection: 'personal' | 'shared_library' | 'shared_album' | 'unknown'; media_type: 'photo' | 'video' | 'live'; capture_time: string | null; time_basis: 'capture_offset' | 'instant_only' | 'unknown'; capture_day: string | null; owner_presence: 'owner' | 'third_party' | 'unknown'; media_state: 'ready' | 'partial' | 'not_transferred' }
export interface Photos { coverage?: { mode: 'selected_samples' | 'progressive' | 'restricted_or_unknown' }; assets: PhotoMetadata[]; fixture: boolean }
export interface SourcePolicyInput { connection_id: string; include_hidden: boolean; include_shared_library: boolean; include_shared_albums: boolean }

export interface MediaComponent { component_id: string; role: 'still' | 'video' | 'motion'; mime: 'image/jpeg' | 'video/mp4'; size: number }
export interface MediaManifest { asset_id: string; state: 'ready' | 'partial' | 'not_transferred'; components: MediaComponent[] }
