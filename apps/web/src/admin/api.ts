import { CONTROL, csrfCookie } from "../auth/client";
import type { NormalizedCompositionNode } from "@slaif-agent-site/composition-schema";

const EDITOR = "/api/editor/v1";

export type AdminSession = {
  recent_auth: boolean;
  absolute_expires_at: string;
  user_account_id: string;
};

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
export type RoleCatalog = {
  role_key: string;
  label: string;
  description: string;
  default_delegation_ceiling: number;
  default_permissions: string[];
};
export type PermissionCatalog = {
  permission_key: string;
  category: string;
  agent_delegation_level: number | null;
  site_assignable: boolean;
  installation_only: boolean;
  system_only: boolean;
  role_keys: string[];
};
export type Membership = {
  site_id: string;
  user_account_id: string;
  role_key: string;
  delegation_ceiling: number;
  effective_delegation_ceiling: number;
  status: "ACTIVE" | "INACTIVE";
  version: number;
  allow_permissions: string[];
  deny_permissions: string[];
  effective_permissions: string[];
  platform_administrator: boolean;
  created_at: string;
  updated_at: string;
};
export type MembershipBody = {
  role_key: string;
  delegation_ceiling: number;
  allow_permissions: string[];
  deny_permissions: string[];
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
function integer(item: Record<string, unknown>, key: string, minimum = 0): number {
  const value = number(item, key);
  if (!Number.isInteger(value) || value < minimum) throw new Error("invalid-response");
  return value;
}
function uuid(item: Record<string, unknown>, key: string): string {
  const value = text(item, key);
  if (
    !/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
      value,
    )
  )
    throw new Error("invalid-response");
  return value;
}
function strings(item: Record<string, unknown>, key: string): string[] {
  const value = item[key];
  if (!Array.isArray(value) || !value.every((entry) => typeof entry === "string"))
    throw new Error("invalid-response");
  return value;
}
function adminSession(value: unknown): AdminSession {
  const item = object(value);
  if (typeof item.recent_auth !== "boolean") throw new Error("invalid-response");
  return {
    recent_auth: item.recent_auth,
    absolute_expires_at: text(item, "absolute_expires_at"),
    user_account_id: uuid(item, "user_account_id"),
  };
}
function role(value: unknown): RoleCatalog {
  const item = object(value);
  const ceiling = integer(item, "default_delegation_ceiling");
  if (ceiling > 4) throw new Error("invalid-response");
  return {
    role_key: text(item, "role_key"),
    label: text(item, "label"),
    description: text(item, "description"),
    default_delegation_ceiling: ceiling,
    default_permissions: strings(item, "default_permissions"),
  };
}
function permission(value: unknown): PermissionCatalog {
  const item = object(value);
  const category = text(item, "category");
  const delegationLevel = item.agent_delegation_level;
  const categories = new Set([
    "READ",
    "L1_WRITE",
    "L2_WRITE",
    "L3_WRITE",
    "L4_WRITE",
    "HUMAN_ONLY",
    "INSTALLATION_ONLY",
    "SYSTEM_ONLY",
  ]);
  if (
    !categories.has(category) ||
    typeof item.site_assignable !== "boolean" ||
    typeof item.installation_only !== "boolean" ||
    typeof item.system_only !== "boolean" ||
    !(
      (typeof delegationLevel === "number" &&
        Number.isInteger(delegationLevel) &&
        delegationLevel >= 0 &&
        delegationLevel <= 4) ||
      delegationLevel === null
    )
  )
    throw new Error("invalid-response");
  return {
    permission_key: text(item, "permission_key"),
    category,
    agent_delegation_level: delegationLevel,
    site_assignable: item.site_assignable,
    installation_only: item.installation_only,
    system_only: item.system_only,
    role_keys: strings(item, "role_keys"),
  };
}
function membership(value: unknown): Membership {
  const item = object(value);
  const explicitCeiling = integer(item, "delegation_ceiling");
  const effectiveCeiling = integer(item, "effective_delegation_ceiling");
  if (
    (item.status !== "ACTIVE" && item.status !== "INACTIVE") ||
    typeof item.platform_administrator !== "boolean" ||
    explicitCeiling > 4 ||
    effectiveCeiling > 4
  )
    throw new Error("invalid-response");
  return {
    site_id: uuid(item, "site_id"),
    user_account_id: uuid(item, "user_account_id"),
    role_key: text(item, "role_key"),
    delegation_ceiling: explicitCeiling,
    effective_delegation_ceiling: effectiveCeiling,
    status: item.status,
    version: integer(item, "version", 1),
    allow_permissions: strings(item, "allow_permissions"),
    deny_permissions: strings(item, "deny_permissions"),
    effective_permissions: strings(item, "effective_permissions"),
    platform_administrator: item.platform_administrator,
    created_at: text(item, "created_at"),
    updated_at: text(item, "updated_at"),
  };
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
    site_id: uuid(item, "site_id"),
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

async function editorRequest(path: string, init: RequestInit = {}): Promise<Response> {
  return fetch(`${EDITOR}${path}`, {
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

function editorMutation(method: string, body?: unknown): RequestInit {
  const csrf = csrfCookie(document.cookie, window.location.protocol === "https:");
  const init: RequestInit = {
    method,
    headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
  };
  if (body !== undefined) init.body = JSON.stringify(body);
  return init;
}

async function editorJson(path: string, init: RequestInit = {}): Promise<unknown> {
  const response = await editorRequest(path, init);
  if (!response.ok) classify(response.status);
  return response.json() as Promise<unknown>;
}

function compositionNode(value: unknown): NormalizedCompositionNode {
  const item = object(value);
  const parentId = item.parent_id;
  const props = item.props;
  if (
    (parentId !== null && typeof parentId !== "string") ||
    !isUuidValue(item.id) ||
    !isUuidValue(item.page_id) ||
    !isUuidValue(item.site_id) ||
    typeof item.component_type !== "string" ||
    typeof item.schema_version !== "string" ||
    typeof item.slot_key !== "string" ||
    typeof item.order_key !== "number" ||
    !Number.isInteger(item.order_key) ||
    !isPlainObject(props)
  )
    throw new Error("invalid-response");
  return {
    id: item.id,
    componentType: item.component_type,
    schemaVersion: item.schema_version,
    parentId,
    slotKey: item.slot_key,
    orderKey: item.order_key,
    props,
  };
}

function isUuidValue(value: unknown): value is string {
  return (
    typeof value === "string" &&
    /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
      value,
    )
  );
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === "object" && !Array.isArray(value));
}

function editorPath(siteId: string, pageId: string, suffix = "") {
  return `/sites/${encodeURIComponent(siteId)}/pages/${encodeURIComponent(pageId)}/composition/${suffix}`;
}

export async function loadComposition(
  siteId: string,
  pageId: string,
): Promise<NormalizedCompositionNode[]> {
  const value = await editorJson(editorPath(siteId, pageId));
  if (!Array.isArray(value)) throw new Error("invalid-response");
  return value.map((item) => {
    const node = compositionNode(item);
    if (node.parentId !== null && !isUuidValue(node.parentId))
      throw new Error("invalid-response");
    return node;
  });
}

export async function addCompositionNode(
  siteId: string,
  pageId: string,
  node: Pick<
    NormalizedCompositionNode,
    "componentType" | "parentId" | "slotKey" | "orderKey" | "props"
  >,
): Promise<NormalizedCompositionNode> {
  const result = compositionNode(
    await editorJson(
      editorPath(siteId, pageId, "components"),
      editorMutation("POST", {
        component_type: node.componentType,
        parent_id: node.parentId,
        slot_key: node.slotKey,
        order_key: node.orderKey,
        props: node.props,
      }),
    ),
  );
  return result;
}

export async function updateCompositionNode(
  siteId: string,
  pageId: string,
  nodeId: string,
  props: Record<string, unknown>,
): Promise<NormalizedCompositionNode> {
  return compositionNode(
    await editorJson(
      editorPath(siteId, pageId, `components/${encodeURIComponent(nodeId)}`),
      editorMutation("PATCH", { props }),
    ),
  );
}

export async function moveCompositionNode(
  siteId: string,
  pageId: string,
  nodeId: string,
  parentId: string | null,
  slotKey: string,
  orderKey: number,
): Promise<NormalizedCompositionNode> {
  return compositionNode(
    await editorJson(
      editorPath(siteId, pageId, `components/${encodeURIComponent(nodeId)}/move`),
      editorMutation("POST", {
        new_parent_id: parentId,
        new_slot_key: slotKey,
        new_order_key: orderKey,
      }),
    ),
  );
}

export async function deleteCompositionNode(
  siteId: string,
  pageId: string,
  nodeId: string,
): Promise<void> {
  const response = await editorRequest(
    editorPath(siteId, pageId, `components/${encodeURIComponent(nodeId)}`),
    editorMutation("DELETE"),
  );
  if (!response.ok) classify(response.status);
}

export async function loadAdmin(): Promise<{
  session: AdminSession;
  sites: CurrentSite[];
}> {
  const currentSession = adminSession(await json("/session"));
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

export async function loadMembershipAdministration(siteId: string): Promise<{
  authority: CurrentAuthority;
  roles: RoleCatalog[];
  permissions: PermissionCatalog[];
  memberships: Membership[];
  session: AdminSession;
}> {
  const [authority, rolesValue, permissionsValue, membershipsValue, sessionValue] =
    await Promise.all([
      loadAuthority(siteId),
      json("/roles"),
      json("/permissions"),
      json(`/sites/${encodeURIComponent(siteId)}/memberships`),
      json("/session"),
    ]);
  if (
    !Array.isArray(rolesValue) ||
    !Array.isArray(permissionsValue) ||
    !Array.isArray(membershipsValue)
  )
    throw new Error("invalid-response");
  const roles = rolesValue.map(role);
  const permissions = permissionsValue.map(permission);
  const memberships = membershipsValue.map(membership);
  const roleByKey = new Map(roles.map((item) => [item.role_key, item]));
  const permissionByKey = new Map(
    permissions.map((item) => [item.permission_key, item]),
  );
  if (roleByKey.size !== roles.length || permissionByKey.size !== permissions.length)
    throw new Error("invalid-response");
  for (const item of memberships) {
    const membershipRole = roleByKey.get(item.role_key);
    const overrides = [...item.allow_permissions, ...item.deny_permissions];
    if (
      item.site_id !== authority.site_id ||
      !membershipRole ||
      item.delegation_ceiling > membershipRole.default_delegation_ceiling ||
      new Set(overrides).size !== overrides.length ||
      overrides.some((key) => !permissionByKey.get(key)?.site_assignable) ||
      item.effective_permissions.some((key) => !permissionByKey.has(key))
    )
      throw new Error("invalid-response");
  }
  return {
    authority,
    roles,
    permissions,
    memberships: memberships.sort((left, right) =>
      left.user_account_id.localeCompare(right.user_account_id),
    ),
    session: adminSession(sessionValue),
  };
}
export const createMembership = async (
  siteId: string,
  targetUserId: string,
  body: MembershipBody,
) =>
  membership(
    await json(
      `/sites/${encodeURIComponent(siteId)}/memberships`,
      mutation("POST", { target_user_id: targetUserId, ...body }),
    ),
  );
export const updateMembership = async (
  siteId: string,
  userId: string,
  expectedVersion: number,
  status: "ACTIVE" | "INACTIVE",
  body: MembershipBody,
) =>
  membership(
    await json(
      `/sites/${encodeURIComponent(siteId)}/memberships/${encodeURIComponent(userId)}`,
      mutation("PATCH", {
        expected_version: expectedVersion,
        status,
        ...body,
      }),
    ),
  );
export const deactivateMembership = async (
  siteId: string,
  userId: string,
  expectedVersion: number,
) =>
  membership(
    await json(
      `/sites/${encodeURIComponent(siteId)}/memberships/${encodeURIComponent(userId)}?expected_version=${encodeURIComponent(String(expectedVersion))}`,
      mutation("DELETE"),
    ),
  );
