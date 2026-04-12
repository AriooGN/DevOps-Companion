/**
 * Base URL for the Flask backend.
 * - In the browser: use `/flask/...` so Next.js rewrites proxy to Flask (same origin → no CORS).
 * - On the server (Route Handlers, SSR): use absolute URL from env or 127.0.0.1.
 */
export function flaskApiUrl(path: string): string {
  const p = path.startsWith('/') ? path : `/${path}`;
  if (typeof window === 'undefined') {
    const base = (
      process.env.FLASK_BACKEND_URL ||
      process.env.INTERNAL_FLASK_URL ||
      'http://127.0.0.1:5000'
    ).replace(/\/$/, '');
    return `${base}${p}`;
  }
  return `/flask${p}`;
}
