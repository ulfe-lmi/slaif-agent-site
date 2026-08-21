import { CONTROL, type SessionSummary, session } from "../auth/client";

export type CurrentSite = {
  site_id: string;
  site_key: string;
  display_name: string;
  status: "ACTIVE" | "ARCHIVED";
  default_locale: string;
  canonical_revision: number;
  role_key: string | null;
  membership_version: number | null;
  explicit_delegation_ceiling: number | null;
  effective_delegation_ceiling: number | null;
  platform_administrator: boolean;
};

export type CurrentAuthority = CurrentSite & { effective_permissions: string[] };

function site(value: unknown): CurrentSite {
  if (!value || typeof value !== "object") throw new Error("invalid-response");
  const item = value as Record<string, unknown>;
  if (
    typeof item.site_id !== "string" ||
    typeof item.site_key !== "string" ||
    typeof item.display_name !== "string" ||
    (item.status !== "ACTIVE" && item.status !== "ARCHIVED") ||
    typeof item.default_locale !== "string" ||
    typeof item.canonical_revision !== "number" ||
    typeof item.platform_administrator !== "boolean" ||
    !(typeof item.role_key === "string" || item.role_key === null)
  )
    throw new Error("invalid-response");
  return item as CurrentSite;
}

async function get(path: string): Promise<Response> {
  return fetch(`${CONTROL}${path}`, {
    method: "GET",
    credentials: "same-origin",
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
}

export async function loadAdmin(): Promise<{
  session: SessionSummary;
  sites: CurrentSite[];
}> {
  const [currentSession, response] = await Promise.all([session(), get("/me/sites")]);
  if (response.status === 401) throw new Error("unauthenticated");
  if (!response.ok) throw new Error(response.status === 503 ? "unavailable" : "denied");
  const value = (await response.json()) as unknown;
  if (!Array.isArray(value)) throw new Error("invalid-response");
  return { session: currentSession, sites: value.map(site) };
}

export async function loadAuthority(siteId: string): Promise<CurrentAuthority> {
  const response = await get(`/sites/${encodeURIComponent(siteId)}/my-authority`);
  if (response.status === 401) throw new Error("unauthenticated");
  if (response.status === 403 || response.status === 404) throw new Error("not-found");
  if (!response.ok)
    throw new Error(response.status === 503 ? "unavailable" : "invalid-response");
  const value = site(await response.json());
  const permissions = (value as unknown as Record<string, unknown>)
    .effective_permissions;
  if (
    !Array.isArray(permissions) ||
    !permissions.every((item) => typeof item === "string")
  )
    throw new Error("invalid-response");
  return { ...value, effective_permissions: permissions };
}
