export interface Session { owner: { id: string; display_name: string }; csrf_token: string; fixture: boolean }
export interface Source { id: string; name: string; permission: string; status: string; last_success: string | null; index_count: number; media_ready_count: number }
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
