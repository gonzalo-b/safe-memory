/** HTTP transport only. Python owns authentication, authorization and auditing. */
export class ApiError extends Error {
  status: number;
  code: string;
  constructor(status: number, code: string, message: string) {
    super(message); this.name = 'ApiError'; this.status = status; this.code = code;
  }
}
const errorMessages: Record<number, string> = {
  400: 'Check the details and try again.', 401: 'Sign in to continue.',
  403: 'This action is not permitted. Refresh your session and try again.',
  404: 'This item is unavailable.', 409: 'This item changed. Refresh before trying again.',
  413: 'This request is too large.', 429: 'Too many attempts. Wait a moment and try again.',
  501: 'Not implemented in this build.', 503: 'Memory is temporarily unavailable. Try again shortly.',
};
export async function request<T>(path: string, options: {
  method?: 'GET' | 'POST'; csrf?: string; body?: unknown; signal?: AbortSignal; query?: Record<string, string | number>;
} = {}): Promise<T> {
  const plainPath = /^\/api\/[a-z]+(?:\/[a-z]+)*$/.test(path) && !path.startsWith('/api/photos/');
  const manifestPath = /^\/api\/photos\/[a-f0-9]{32}\/media$/.test(path);
  if (!plainPath && !manifestPath) throw new Error('A local API path is required.');
  const method = options.method || 'GET';
  if (method === 'POST' && path !== '/api/auth/login' && !options.csrf) {
    throw new ApiError(403, 'csrf', 'Session verification is unavailable. Sign in again.');
  }
  const query = new URLSearchParams(Object.entries(options.query || {}).map(([key, value]) => [key, String(value)])).toString();
  const url = query ? `${path}?${query}` : path;
  let response: Response;
  try {
    response = await fetch(url, {
      method, credentials: 'same-origin', cache: 'no-store', redirect: 'error', signal: options.signal,
      headers: { Accept: 'application/json', ...(method === 'POST' ? { 'Content-Type': 'application/json' } : {}),
        ...(options.csrf ? { 'X-CSRF-Token': options.csrf } : {}) },
      ...(method === 'POST' ? { body: JSON.stringify(options.body ?? {}) } : {}),
    });
  } catch (error) {
    if (options.signal?.aborted) throw error;
    throw new ApiError(0, 'network', 'Could not reach Memory. Check your connection and try again.');
  }
  if (!response.ok) {
    // Do not echo response bodies: malformed proxies must not expose internal paths/secrets.
    throw new ApiError(response.status, 'request_failed', errorMessages[response.status] || 'This request did not finish. Try again.');
  }
  try { return await response.json() as T; }
  catch { throw new ApiError(502, 'invalid_response', 'The server response could not be read. Try again.'); }
}

/** IDs become private same-origin paths only after exact validation. Never accept a server URL. */
export function mediaPath(componentId: string): string {
  if (!/^[a-f0-9]{32}$/.test(componentId)) throw new Error('A local media component ID is required.');
  return `/api/media/${componentId}`;
}
/** Media element errors hide the frame first, then use HEAD to detect authorization loss. */
export async function verifyMedia(componentId: string, signal: AbortSignal): Promise<void> {
  const path = mediaPath(componentId);
  let response: Response;
  try { response = await fetch(path, { method: 'HEAD', credentials: 'same-origin', cache: 'no-store', redirect: 'error', signal }); }
  catch (error) {
    if (signal.aborted) throw error;
    throw new ApiError(0, 'network', 'Could not reach Memory. Check your connection and try again.');
  }
  if (!response.ok) throw new ApiError(response.status, 'request_failed', errorMessages[response.status] || 'This request did not finish. Try again.');
}
