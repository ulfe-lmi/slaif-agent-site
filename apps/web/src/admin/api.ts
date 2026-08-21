import { CONTROL, csrfCookie, type SessionSummary, session } from "../auth/client";

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
export type SiteRecord = Pick<
  CurrentSite,
  | "site_id"
  | "site_key"
  | "display_name"
  | "status"
  | "default_locale"
  | "canonical_revision"
> & {
  component_catalog_version: string;
  content_model_revision: number;
  created_at: string;
  updated_at: string;
};
export type DomainMapping = {
  domain_id: string;
  site_id: string;
  hostname: string;
  path_prefix: string;
  is_primary: boolean;
  created_at: string;
};

function object(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value))
    throw new Error("invalid-response");
  return value as Record<string, unknown>;
}
function text(item: Record<string, unknown>, key: string): string {
  if (typeof item[key] !== "string") throw new Error("invalid-response");
  return item[key];
}
function number(item: Record<string, unknown>, key: string): number {
  if (typeof item[key] !== "number") throw new Error("invalid-response");
  return item[key];
}
function currentSite(value: unknown): CurrentSite {
  const item = object(value);
  const status = item.status;
  if (
    (status !== "ACTIVE" && status !== "ARCHIVED") ||
    typeof item.platform_administrator !== "boolean" ||
    !(typeof item.role_key === "string" || item.role_key === null)
  )
    throw new Error("invalid-response");
  return {
    site_id: text(item, "site_id"),
    site_key: text(item, "site_key"),
    display_name: text(item, "display_name"),
    status,
    default_locale: text(item, "default_locale"),
    canonical_revision: number(item, "canonical_revision"),
    role_key: item.role_key,
    membership_version: item.membership_version as number | null,
    explicit_delegation_ceiling: item.explicit_delegation_ceiling as number | null,
    effective_delegation_ceiling: item.effective_delegation_ceiling as number | null,
    platform_administrator: item.platform_administrator,
  };
}
function siteRecord(value: unknown): SiteRecord {
  const item = object(value);
  const status = item.status;
  if (status !== "ACTIVE" && status !== "ARCHIVED") throw new Error("invalid-response");
  return {
    site_id: text(item, "site_id"),
    site_key: text(item, "site_key"),
    display_name: text(item, "display_name"),
    status,
    default_locale: text(item, "default_locale"),
    canonical_revision: number(item, "canonical_revision"),
    component_catalog_version: text(item, "component_catalog_version"),
    content_model_revision: number(item, "content_model_revision"),
    created_at: text(item, "created_at"),
    updated_at: text(item, "updated_at"),
  };
}
function domain(value: unknown): DomainMapping {
  const item = object(value);
  if (typeof item.is_primary !== "boolean") throw new Error("invalid-response");
  return {
    domain_id: text(item, "domain_id"),
    site_id: text(item, "site_id"),
    hostname: text(item, "hostname"),
    path_prefix: text(item, "path_prefix"),
    is_primary: item.is_primary,
    created_at: text(item, "created_at"),
  };
}
function classify(status: number): never {
  throw new Error(
    status === 401
      ? "unauthenticated"
      : status === 403
        ? "denied"
        : status === 404
          ? "not-found"
          : status === 409
            ? "conflict"
            : status === 422
              ? "invalid"
              : status === 503
                ? "unavailable"
                : "invalid-response",
  );
}
async function request(path: string, init: RequestInit = {}): Promise<Response> {
  return fetch(`${CONTROL}${path}`, {
    ...init,
    credentials: "same-origin",
    cache: "no-store",
    headers: { Accept: "application/json", ...init.headers },
  });
}
async function json(path: string, init: RequestInit = {}): Promise<unknown> {
  const response = await request(path, init);
  if (!response.ok) classify(response.status);
  return response.json() as Promise<unknown>;
}
function mutation(method: string, body?: unknown): RequestInit {
  const csrf = csrfCookie(document.cookie, window.location.protocol === "https:");
  const init: RequestInit = {
    method,
    headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
  };
  if (body !== undefined) init.body = JSON.stringify(body);
  return init;
}

export async function loadAdmin(): Promise<{
  session: SessionSummary;
  sites: CurrentSite[];
}> {
  const currentSession = await session();
  const value = await json("/me/sites");
  if (!Array.isArray(value)) throw new Error("invalid-response");
  return { session: currentSession, sites: value.map(currentSite) };
}
export async function loadAuthority(siteId: string): Promise<CurrentAuthority> {
  const value = object(await json(`/sites/${encodeURIComponent(siteId)}/my-authority`));
  const permissions = value.effective_permissions;
  if (
    !Array.isArray(permissions) ||
    !permissions.every((item) => typeof item === "string")
  )
    throw new Error("invalid-response");
  return { ...currentSite(value), effective_permissions: permissions };
}
export const loadSite = async (siteId: string) =>
  siteRecord(await json(`/sites/${encodeURIComponent(siteId)}`));
export async function loadDomains(siteId: string): Promise<DomainMapping[]> {
  const value = await json(`/sites/${encodeURIComponent(siteId)}/domains`);
  if (!Array.isArray(value)) throw new Error("invalid-response");
  return value.map(domain);
}
export const createSite = async (body: {
  site_key: string;
  display_name: string;
  default_locale: string;
}) => siteRecord(await json("/sites", mutation("POST", body)));
export const updateSite = async (
  siteId: string,
  body: { display_name: string; default_locale: string },
) =>
  siteRecord(
    await json(`/sites/${encodeURIComponent(siteId)}`, mutation("PATCH", body)),
  );
export const putDomain = async (
  siteId: string,
  body: { hostname: string; path_prefix: string; is_primary: boolean },
  domainId?: string,
) =>
  domain(
    await json(
      `/sites/${encodeURIComponent(siteId)}/domains${domainId ? `/${encodeURIComponent(domainId)}` : ""}`,
      mutation(domainId ? "PUT" : "POST", body),
    ),
  );
export async function removeDomain(siteId: string, domainId: string): Promise<void> {
  const response = await request(
    `/sites/${encodeURIComponent(siteId)}/domains/${encodeURIComponent(domainId)}`,
    mutation("DELETE"),
  );
  if (!response.ok) classify(response.status);
}
export const archiveSite = async (siteId: string) =>
  siteRecord(
    await json(`/sites/${encodeURIComponent(siteId)}/archive`, mutation("POST")),
  );
