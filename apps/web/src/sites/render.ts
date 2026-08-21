import "server-only";

const RENDER_CONTEXT_URL = "http://render-api:8000/internal/render/v1/site-context";

export type SiteContext = Readonly<{
  site_id: string;
  site_key: string;
  canonical_revision: number;
  default_locale: string;
  matched_hostname: string;
  matched_path_prefix: string;
}>;

export async function resolveSiteContext(
  authority: string,
  path: string,
): Promise<SiteContext | null> {
  const signal = AbortSignal.timeout(1500);
  try {
    const response = await fetch(RENDER_CONTEXT_URL, {
      method: "POST",
      cache: "no-store",
      credentials: "omit",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ authority, path }),
      signal,
    });
    if (!response.ok) return null;
    return (await response.json()) as SiteContext;
  } catch {
    return null;
  }
}

export async function renderReady(): Promise<boolean> {
  try {
    const response = await fetch(RENDER_CONTEXT_URL, {
      method: "POST",
      cache: "no-store",
      credentials: "omit",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ authority: "readiness.invalid", path: "/health" }),
      signal: AbortSignal.timeout(1500),
    });
    return response.status === 404;
  } catch {
    return false;
  }
}
