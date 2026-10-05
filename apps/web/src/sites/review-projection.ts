/**
 * 082/2 review render projection: the pure mapping from the trusted
 * read-model document (``control.slaif_review_read_model``) to the frozen
 * review projection.
 *
 * The resolver's content source is exclusively the document: no live COW
 * reads, no canonical reads, no network access. The mapping mirrors the
 * trusted renderer's resolution semantics (locale prefix contract,
 * effective-route matching, redirect selection, region/navigation/media
 * projection) against the frozen snapshot state, so the rendered output is
 * a deterministic function of the immutable snapshot alone.
 */

import type { ThemeRecord } from "@slaif-agent-site/composition-schema";
import type {
  PageProjection,
  ProjectionLocale,
  ProjectionMedia,
  ProjectionNavigation,
  ProjectionNavigationItem,
  ProjectionNode,
  ProjectionRegionEntry,
  ProjectionRegion,
} from "./render";

/* ------------------------------------------------------------------ */
/* Document shape (the R1 read-model contract)                          */
/* ------------------------------------------------------------------ */

export type ReviewStateSite = Readonly<{
  site_key: string;
  display_name: string;
  default_locale: string;
  component_catalog_version: string;
}>;

export type ReviewStateLocale = Readonly<{
  tag: string;
  enabled: boolean;
  is_default: boolean;
  position: number;
}>;

export type ReviewStatePage = Readonly<{
  id: string;
  site_id: string;
  slug: string;
  title: string;
  status: string;
  locale: string;
  parent_id: string | null;
  route_template: string | null;
  effective_route: string;
  row_version: number;
  nodes: readonly unknown[];
}>;

export type ReviewStateRedirect = Readonly<{
  id: string;
  site_id: string;
  source_route: string;
  target: string;
  status_code: number;
  locale: string | null;
}>;

export type ReviewStateMedia = Readonly<{
  id: string;
  mime_type: string;
  size_bytes: number;
  content_hash: string;
  public_status: string;
}>;

export type ReviewState = Readonly<{
  state_version: string;
  workspace_id: string;
  site_id: string;
  site: ReviewStateSite;
  base_site_revision: number;
  operation_watermark: number;
  locales: readonly ReviewStateLocale[];
  theme: ThemeRecord;
  regions: readonly unknown[];
  navigation: Readonly<{ definitions: readonly unknown[]; items: readonly unknown[] }>;
  redirects: readonly ReviewStateRedirect[];
  pages: readonly ReviewStatePage[];
  media: Readonly<Record<string, ReviewStateMedia>>;
}>;

export type ReviewDocument = Readonly<{
  snapshot: Readonly<{
    id: string;
    digest: string;
    state_version: string;
    revision_watermark: number;
    base_site_revision: number;
    status: string;
    created_at: string;
    created_by: string;
    versions: Readonly<Record<string, string>>;
  }>;
  drift: Readonly<{
    current_site_revision: number;
    base_site_revision: number;
    equal: boolean;
  }>;
  timeline: readonly Readonly<{
    operation_id: string;
    operation_type: string;
    resource: readonly string[];
    created_at: string;
  }>[];
  resource_diff: Readonly<
    Record<
      string,
      Readonly<{
        added: readonly unknown[];
        modified: readonly Readonly<{
          id: string;
          fields: Readonly<
            Record<string, Readonly<{ before: unknown; after: unknown }>>
          >;
        }>[];
        deleted: readonly unknown[];
      }>
    >
  >;
  summaries: Readonly<Record<string, unknown>>;
  validation: Readonly<{ report: unknown; warnings: readonly unknown[] }>;
  evidence: Readonly<{
    runs: readonly Readonly<{ id: string }>[];
    artifacts: readonly Readonly<{
      run_id: string;
      artifacts: readonly Readonly<{
        artifact_id: string;
        kind: string;
        mime_type: string | null;
      }>[];
    }>[];
  }>;
  metadata: Readonly<{
    workspace: Readonly<{
      id: string;
      title: string;
      actor_type: string;
      status: string;
    }>;
    site: Readonly<{ id: string; key: string }>;
    capabilities: readonly unknown[];
    quota_policy: Readonly<Record<string, unknown>>;
    agent_session_browser: Readonly<{
      versions: Readonly<Record<string, string>>;
      review_jobs: readonly unknown[];
    }>;
  }>;
  normalized_state: ReviewState;
}>;

export type ReviewProjectionResult =
  | { kind: "not_found" }
  | { kind: "redirect"; target: string; status_code: 301 | 302 | 303 | 307 | 308 }
  | { kind: "page"; projection: PageProjection };

/* ------------------------------------------------------------------ */
/* Trusted renderer semantics mirrored against the frozen state         */
/* ------------------------------------------------------------------ */

const PATH_SEGMENT = /^[A-Za-z0-9._~-]+$/;
const PATH_MAX_LENGTH = 512;
const RESERVED_TOP_LEVEL = new Set([
  "api",
  "admin",
  "agent",
  "control",
  "editor",
  "health",
  "internal",
  "login",
  "logout",
  "mcp",
  "media",
  "preview",
  "setup",
  "_next",
  "static",
]);
const RENDERABLE_STATUSES = new Set(["PUBLISHED", "DRAFT"]);
const IMAGE_MIME_CLASSES = new Set(["image/png", "image/jpeg"]);
const DOCUMENT_MIME_CLASSES = new Set(["application/pdf"]);
const MAX_ANCESTOR_DEPTH = 64;

const isString = (value: unknown): value is string => typeof value === "string";
const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);
const isNonEmptyString = (value: unknown): value is string =>
  typeof value === "string" && value.trim() !== "";

/**
 * Structural validation of the trusted read-model document's
 * ``normalized_state``. The projection mapping is pure and type-driven
 * after this gate: every field the mapping reads is runtime-checked
 * here, so the single cast to ``ReviewState`` is sound. A corrupt or
 * forged document fails closed (uniform ``not_found``), never partially.
 */
function parseReviewState(rawState: Record<string, unknown>): ReviewState | null {
  const rawSite = rawState["site"];
  const rawLocales = rawState["locales"];
  const rawRegions = rawState["regions"];
  const rawRedirects = rawState["redirects"];
  const rawPages = rawState["pages"];
  const rawNavigation = rawState["navigation"];
  const rawMedia = rawState["media"];
  if (
    !isString(rawState["state_version"]) ||
    !isString(rawState["workspace_id"]) ||
    !isString(rawState["site_id"]) ||
    typeof rawState["base_site_revision"] !== "number" ||
    typeof rawState["operation_watermark"] !== "number" ||
    !isRecord(rawSite) ||
    !isString(rawSite["site_key"]) ||
    !isString(rawSite["display_name"]) ||
    !isString(rawSite["default_locale"]) ||
    !isString(rawSite["component_catalog_version"]) ||
    !isRecord(rawState["theme"]) ||
    !Array.isArray(rawLocales) ||
    !Array.isArray(rawRegions) ||
    !Array.isArray(rawRedirects) ||
    !Array.isArray(rawPages) ||
    !isRecord(rawNavigation) ||
    !Array.isArray(rawNavigation["definitions"]) ||
    !Array.isArray(rawNavigation["items"]) ||
    !isRecord(rawMedia)
  ) {
    return null;
  }
  for (const rawLocale of rawLocales) {
    if (
      !isRecord(rawLocale) ||
      !isString(rawLocale["tag"]) ||
      typeof rawLocale["enabled"] !== "boolean" ||
      typeof rawLocale["is_default"] !== "boolean" ||
      typeof rawLocale["position"] !== "number"
    ) {
      return null;
    }
  }
  for (const rawRedirect of rawRedirects) {
    if (
      !isRecord(rawRedirect) ||
      !isString(rawRedirect["id"]) ||
      !isString(rawRedirect["site_id"]) ||
      !isString(rawRedirect["source_route"]) ||
      !isString(rawRedirect["target"]) ||
      typeof rawRedirect["status_code"] !== "number" ||
      (rawRedirect["locale"] !== null && !isString(rawRedirect["locale"]))
    ) {
      return null;
    }
  }
  for (const rawPage of rawPages) {
    if (
      !isRecord(rawPage) ||
      !isString(rawPage["id"]) ||
      !isString(rawPage["site_id"]) ||
      !isString(rawPage["slug"]) ||
      !isString(rawPage["title"]) ||
      !isString(rawPage["status"]) ||
      !isString(rawPage["locale"]) ||
      (rawPage["parent_id"] !== null && !isString(rawPage["parent_id"])) ||
      (rawPage["route_template"] !== null && !isString(rawPage["route_template"])) ||
      typeof rawPage["row_version"] !== "number" ||
      !Array.isArray(rawPage["nodes"])
    ) {
      return null;
    }
  }
  for (const rawAsset of Object.values(rawMedia)) {
    if (
      !isRecord(rawAsset) ||
      !isString(rawAsset["id"]) ||
      !isString(rawAsset["mime_type"]) ||
      typeof rawAsset["size_bytes"] !== "number" ||
      !isString(rawAsset["content_hash"]) ||
      !isString(rawAsset["public_status"])
    ) {
      return null;
    }
  }
  // Every field the mapping reads is verified; the cast is sound.
  return rawState as unknown as ReviewState;
}

/** Exact mirror of the trusted ``normalize_request_path`` (fail closed). */
function normalizeRequestPath(path: string): string | null {
  if (path === "/") return "/";
  let value = path;
  if (value.endsWith("/")) value = value.slice(0, -1);
  if (value === "/") return "/";
  if (
    !value.startsWith("/") ||
    value.length > PATH_MAX_LENGTH ||
    value.includes("%") ||
    value.includes("?") ||
    value.includes("#") ||
    value.includes("\\") ||
    value.includes("\u0000") ||
    value.includes("//")
  ) {
    return null;
  }
  const segments = value.split("/").slice(1);
  for (const segment of segments) {
    if (
      segment.length === 0 ||
      segment === "." ||
      segment === ".." ||
      !PATH_SEGMENT.test(segment)
    ) {
      return null;
    }
  }
  return "/" + segments.map((segment) => segment.toLowerCase()).join("/");
}

function pathIsReserved(path: string): boolean {
  if (path === "/") return false;
  return RESERVED_TOP_LEVEL.has(path.split("/", 2)[1]?.toLowerCase() ?? "");
}

type LocaleSelection = { route: string; tag: string } | null;

/** Exact mirror of the trusted locale-prefix contract. */
function selectLocale(
  normalized: string,
  locales: readonly ReviewStateLocale[],
): LocaleSelection {
  const enabled = locales.filter(
    (locale) => isRecord(locale) && locale.enabled === true && isString(locale.tag),
  );
  const byLower = new Map<string, (typeof enabled)[number]>();
  for (const locale of enabled) byLower.set(locale.tag.toLowerCase(), locale);
  const defaults = enabled.filter((locale) => locale.is_default === true);
  const firstDefault = defaults.length === 1 ? defaults[0] : undefined;
  if (firstDefault === undefined) return null;
  const defaultTag = firstDefault.tag;
  const segments = normalized === "/" ? [] : normalized.replace(/^\//, "").split("/");
  let selectedTag = defaultTag;
  const head = segments[0];
  if (head !== undefined) {
    const candidate = byLower.get(head.toLowerCase());
    if (candidate) {
      // Default locales have no prefix in the effective-route contract.
      if (candidate.tag.toLowerCase() === defaultTag.toLowerCase()) return null;
      selectedTag = candidate.tag;
    }
  }
  return { route: normalized, tag: selectedTag };
}

function matchedPage(
  state: ReviewState,
  route: string,
  locale: string,
): ReviewStatePage | null {
  const lowerRoute = route.toLowerCase();
  const lowerLocale = locale.toLowerCase();
  const matches = state.pages.filter(
    (page) =>
      page.effective_route.toLowerCase() === lowerRoute &&
      page.locale.toLowerCase() === lowerLocale &&
      RENDERABLE_STATUSES.has(page.status),
  );
  const first = matches.length === 1 ? matches[0] : undefined;
  return first ?? null;
}

function selectedRedirect(
  state: ReviewState,
  route: string,
  locale: string,
): ReviewStateRedirect | null {
  const lowerRoute = route.toLowerCase();
  const lowerLocale = locale.toLowerCase();
  let selected: ReviewStateRedirect | null = null;
  for (const redirect of state.redirects) {
    if (
      redirect.source_route.toLowerCase() === lowerRoute &&
      (redirect.locale === null || redirect.locale.toLowerCase() === lowerLocale)
    ) {
      if (![301, 302, 303, 307, 308].includes(redirect.status_code)) return null;
      if (selected) return null; // duplicate binding: fail closed
      selected = redirect;
    }
  }
  return selected;
}

function labelFor(
  labels: unknown,
  selected: string,
  fallback: string,
  base?: unknown,
): string {
  if (isRecord(labels)) {
    const selectedLabel = labels[selected];
    if (isNonEmptyString(selectedLabel)) return selectedLabel;
    const fallbackLabel = labels[fallback];
    if (isNonEmptyString(fallbackLabel)) return fallbackLabel;
  }
  return isString(base) ? base : "";
}

function projectLocales(state: ReviewState, page: ReviewStatePage): ProjectionLocale[] {
  const defaultLocale = state.site.default_locale;
  const enabled = state.locales
    .filter((locale) => locale.enabled === true)
    .sort((a, b) => a.position - b.position || a.tag.localeCompare(b.tag));
  return enabled.map((locale) => {
    const tag = locale.tag;
    let switcherHref: string | null = null;
    if (tag.toLowerCase() !== page.locale.toLowerCase()) {
      // Re-root the matched page under the target tag (the trusted
      // effective-route contract).
      const lowerLocale = page.locale.toLowerCase();
      const rest =
        lowerLocale === defaultLocale.toLowerCase()
          ? page.effective_route
          : page.effective_route.toLowerCase() === `/${lowerLocale}`
            ? "/"
            : page.effective_route.toLowerCase().startsWith(`/${lowerLocale}/`)
              ? page.effective_route.slice(page.locale.length + 1)
              : page.effective_route;
      const target =
        tag.toLowerCase() === defaultLocale.toLowerCase()
          ? rest
          : rest === "/"
            ? `/${tag}`
            : `/${tag}${rest}`;
      const targetPage = matchedPage(state, target, tag);
      if (targetPage) switcherHref = targetPage.effective_route;
    }
    return {
      id: "",
      site_id: state.site_id,
      tag,
      enabled: true,
      is_default: locale.is_default,
      position: locale.position,
      metadata: {},
      switcher_href: switcherHref,
    };
  });
}

function projectAncestors(
  state: ReviewState,
  page: ReviewStatePage,
): PageProjection["ancestors"] {
  const byId = new Map<string, ReviewStatePage>(
    state.pages.map((entry): [string, ReviewStatePage] => [entry.id, entry]),
  );
  const chain: ReviewStatePage[] = [];
  let cursor = page;
  for (let depth = 0; cursor.parent_id && depth < MAX_ANCESTOR_DEPTH; depth += 1) {
    const parent = byId.get(cursor.parent_id);
    if (!parent || parent.locale !== cursor.locale) break;
    chain.push(parent);
    cursor = parent;
  }
  // Breadcrumb order: outermost ancestor first (the trusted chain orders
  // by depth DESC, i.e. the root parent precedes the direct parent).
  return chain
    .slice()
    .reverse()
    .filter((entry) => entry.id !== page.id)
    .map((entry) => ({ title: entry.title, effective_route: entry.effective_route }));
}

type RegionEntries = PageProjection["regions"][number]["entries"];

function projectRegionEntries(
  state: ReviewState,
  content: Record<string, unknown>,
  regionKey: string,
): { entries: RegionEntries; note: string | null } | null {
  const rawEntries = regionKey === "header" ? content["nav"] : content["links"];
  if (!Array.isArray(rawEntries)) return null;
  const entries: ProjectionRegionEntry[] = [];
  for (const raw of rawEntries) {
    if (!isRecord(raw) || !isString(raw["label"]) || raw["label"].length === 0) {
      return null;
    }
    if (!isRecord(raw["target"])) return null;
    const kind = raw["target"]["kind"];
    const value = raw["target"]["value"];
    if (!isString(kind) || !isString(value) || value.length === 0) return null;
    let href: string;
    if (kind === "page") {
      // Page targets resolve against the frozen page set only.
      const page = state.pages.find(
        (entry) => entry.id === value && RENDERABLE_STATUSES.has(entry.status),
      );
      if (!page) continue;
      href = page.effective_route;
    } else if (kind === "internal" || kind === "external") {
      href = value;
    } else {
      return null;
    }
    if (kind !== "external") {
      if (!href.startsWith("/") || pathIsReserved(href)) continue;
    }
    entries.push({ label: raw["label"], href });
  }
  let note: string | null = null;
  if (regionKey === "footer") {
    if (content["note"] !== undefined && !isString(content["note"])) return null;
    note = isString(content["note"]) ? content["note"] : null;
  }
  return { entries, note };
}

function projectRegions(state: ReviewState): ProjectionRegion[] {
  const regions: ProjectionRegion[] = [];
  for (const raw of state.regions) {
    if (!isRecord(raw)) return [];
    const regionKey = raw["region_key"];
    const variant = raw["variant"];
    const rowVersion = raw["row_version"];
    const content = raw["content"];
    if (
      (regionKey !== "header" && regionKey !== "footer") ||
      !isString(variant) ||
      !isRecord(content) ||
      typeof rowVersion !== "number"
    ) {
      return [];
    }
    const projected = projectRegionEntries(state, content, regionKey);
    if (!projected) return [];
    regions.push({
      id: isString(raw["id"]) ? raw["id"] : "",
      region_key: regionKey,
      variant: variant as ProjectionRegion["variant"],
      entries: projected.entries,
      note: projected.note,
      row_version: rowVersion,
    });
  }
  return regions;
}

type RawNavItem = {
  id: string;
  navigation_id: string;
  parent_id: string | null;
  locale: string | null;
  position: number;
  labels: unknown;
  target_kind: string;
  resolved_target: string;
};

function projectNavigation(
  state: ReviewState,
  selected: string,
  defaultLocale: string,
): ProjectionNavigation[] {
  const definitionDrafts: Array<{
    id: string;
    key: string;
    label: string;
    labels: Record<string, unknown>;
    settings: Record<string, unknown>;
  }> = [];
  for (const rawDefinition of state.navigation.definitions) {
    if (!isRecord(rawDefinition) || !isString(rawDefinition["key"])) return [];
    definitionDrafts.push({
      id: isString(rawDefinition["id"]) ? rawDefinition["id"] : "",
      key: rawDefinition["key"],
      label: labelFor(
        rawDefinition["labels"],
        selected,
        defaultLocale,
        rawDefinition["label"],
      ),
      labels: isRecord(rawDefinition["labels"]) ? rawDefinition["labels"] : {},
      settings: isRecord(rawDefinition["settings"]) ? rawDefinition["settings"] : {},
    });
  }
  const itemsById = new Map<string, RawNavItem>();
  for (const rawItem of state.navigation.items) {
    if (!isRecord(rawItem)) return [];
    const id = rawItem["id"];
    const navigationId = rawItem["navigation_id"];
    const parentId = rawItem["parent_id"];
    const targetKind = rawItem["target_kind"];
    const resolvedTarget = rawItem["resolved_target"];
    const position = rawItem["position"];
    if (
      !isString(id) ||
      !isString(navigationId) ||
      (parentId !== null && !isString(parentId)) ||
      !isString(targetKind) ||
      !isString(resolvedTarget) ||
      typeof position !== "number" ||
      itemsById.has(id)
    ) {
      return [];
    }
    itemsById.set(id, {
      id,
      navigation_id: navigationId,
      parent_id: parentId,
      locale: isString(rawItem["locale"]) ? rawItem["locale"] : null,
      position,
      labels: rawItem["labels"],
      target_kind: targetKind,
      resolved_target: resolvedTarget,
    });
  }
  // Cycle/duplicate guard over the frozen item graph (defensive: the
  // snapshot materializer already validated it; a corrupt document must
  // fail closed, never loop).
  const visiting = new Set<string>();
  const visited = new Set<string>();
  const acyclic = (id: string): boolean => {
    if (visiting.has(id)) return false;
    if (visited.has(id)) return true;
    visiting.add(id);
    const ok = itemsById.has(id)
      ? [...itemsById.values()].every(
          (child) => child.parent_id !== id || acyclic(child.id),
        )
      : false;
    visiting.delete(id);
    visited.add(id);
    return ok;
  };
  for (const item of itemsById.values()) {
    if (!acyclic(item.id)) return [];
  }
  const projectItem = (item: RawNavItem): ProjectionNavigationItem => {
    const children = [...itemsById.values()]
      .filter(
        (child) =>
          child.parent_id === item.id &&
          (child.locale === null ||
            child.locale.toLowerCase() === selected.toLowerCase()),
      )
      .sort((a, b) => a.position - b.position || a.id.localeCompare(b.id))
      .map((child) => projectItem(child));
    return {
      id: item.id,
      site_id: state.site_id,
      navigation_id: item.navigation_id,
      parent_id: item.parent_id,
      page_id: null,
      locale: item.locale,
      position: item.position,
      label: labelFor(item.labels, selected, defaultLocale),
      labels: isRecord(item.labels) ? item.labels : {},
      target: {
        kind: item.target_kind as "PAGE" | "INTERNAL" | "EXTERNAL",
        value: item.resolved_target,
      },
      children,
    };
  };
  return definitionDrafts.map((draft) => ({
    id: draft.id,
    site_id: state.site_id,
    key: draft.key,
    label: draft.label,
    labels: draft.labels,
    settings: draft.settings,
    items: [...itemsById.values()]
      .filter(
        (item) =>
          item.navigation_id === draft.id &&
          item.parent_id === null &&
          (item.locale === null ||
            item.locale.toLowerCase() === selected.toLowerCase()),
      )
      .sort((a, b) => a.position - b.position || a.id.localeCompare(b.id))
      .map((item) => projectItem(item)),
  }));
}

function mediaDescriptor(
  state: ReviewState,
  mediaId: string,
  mimeClass: ReadonlySet<string>,
): ProjectionMedia | null {
  const descriptor = state.media?.[mediaId];
  if (
    !descriptor ||
    !isString(descriptor.mime_type) ||
    !mimeClass.has(descriptor.mime_type) ||
    typeof descriptor.size_bytes !== "number"
  ) {
    return null;
  }
  // Frozen review media always renders through the session-scoped private
  // path; the public URL namespace is never used by the review render.
  return {
    url: `/media/v1/sites/${state.site_id}/assets/${mediaId}/content`,
    mime_type: descriptor.mime_type,
    size_bytes: descriptor.size_bytes,
  };
}

// The projection JSON may carry list-valued media descriptors for Gallery,
// LogoGrid, and DocumentList nodes; the wire shape is an optional sibling of
// ProjectionNode so the shared projection contract stays untouched (same
// pattern as the trusted renderer's MediaItemsNode).
type ReviewMediaItemsNode = ProjectionNode & {
  readonly media_items?: readonly (ProjectionMedia | null)[] | null;
};

function attachMedia(
  nodes: readonly ReviewMediaItemsNode[],
  state: ReviewState,
): ReviewMediaItemsNode[] {
  return nodes.map((node) => {
    const children = attachMedia(node.children, state);
    let media: ProjectionMedia | null = null;
    let mediaItems: readonly (ProjectionMedia | null)[] | null = null;
    if (node.component_type === "Image") {
      const raw = node.props["mediaId"];
      if (typeof raw === "string")
        media = mediaDescriptor(state, raw, IMAGE_MIME_CLASSES);
    } else if (
      node.component_type === "Gallery" ||
      node.component_type === "LogoGrid"
    ) {
      const rawItems = node.props["items"];
      if (Array.isArray(rawItems)) {
        mediaItems = rawItems.map((rawItem) =>
          isRecord(rawItem) && typeof rawItem["mediaId"] === "string"
            ? mediaDescriptor(state, rawItem["mediaId"], IMAGE_MIME_CLASSES)
            : null,
        );
      }
    } else if (node.component_type === "DocumentList") {
      const rawItems = node.props["items"];
      if (Array.isArray(rawItems)) {
        mediaItems = rawItems.map((rawItem) =>
          isRecord(rawItem) && typeof rawItem["mediaId"] === "string"
            ? mediaDescriptor(state, rawItem["mediaId"], DOCUMENT_MIME_CLASSES)
            : null,
        );
      }
    }
    return { ...node, children, media, media_items: mediaItems };
  });
}

/**
 * Map the snapshot's nested node tree (the exact ``_node_tree`` output the
 * trusted renderer consumed at freeze time) to projection nodes. The
 * snapshot tree order is authoritative; the mapping is defensive and pure.
 */
function projectNodes(nodes: readonly unknown[]): ReviewMediaItemsNode[] {
  const result: ReviewMediaItemsNode[] = [];
  for (const raw of nodes) {
    if (!isRecord(raw)) continue;
    if (
      !isString(raw["id"]) ||
      !isString(raw["component_type"]) ||
      !isString(raw["slot_key"]) ||
      typeof raw["order_key"] !== "number"
    ) {
      continue;
    }
    result.push({
      id: raw["id"],
      component_type: raw["component_type"],
      schema_version: isString(raw["schema_version"]) ? raw["schema_version"] : "1",
      parent_id: isString(raw["parent_id"]) ? raw["parent_id"] : null,
      slot_key: raw["slot_key"],
      order_key: raw["order_key"],
      props: isRecord(raw["props"]) ? raw["props"] : {},
      media: null,
      media_items: null,
      children: Array.isArray(raw["children"]) ? projectNodes(raw["children"]) : [],
    });
  }
  return result;
}

/* ------------------------------------------------------------------ */
/* The pure resolver                                                    */
/* ------------------------------------------------------------------ */

/**
 * Build the review resolution for one requested site path from the
 * read-model document alone. Every gate failure (malformed path, locale
 * state, no match) is the uniform ``not_found`` kind: the document is the
 * only input, so no oracle can leak from the frozen state.
 */
export function projectionFromReviewDocument(
  document: ReviewDocument,
  requestedPath: string,
): ReviewProjectionResult {
  // Re-apply the full structural gate (callers gate before us too): a
  // corrupt or forged document never reaches the pure mapping.
  if (!isReviewDocument(document)) return { kind: "not_found" };
  const state = document.normalized_state;
  const normalized = normalizeRequestPath(requestedPath);
  if (normalized === null || pathIsReserved(normalized)) return { kind: "not_found" };
  const selection = selectLocale(normalized, state.locales);
  if (!selection) return { kind: "not_found" };
  const redirect = selectedRedirect(state, selection.route, selection.tag);
  if (redirect) {
    return {
      kind: "redirect",
      target: redirect.target,
      status_code: redirect.status_code as 301 | 302 | 303 | 307 | 308,
    };
  }
  const page = matchedPage(state, selection.route, selection.tag);
  if (!page) return { kind: "not_found" };
  const defaultLocale = state.site.default_locale;
  const nodes = attachMedia(projectNodes(page.nodes), state);
  return {
    kind: "page",
    projection: {
      route_kind: "page",
      // The frozen review reuses the preview projection contract: no
      // canonical claims, no shared renderer semantics change.
      render_mode: "preview",
      site: {
        id: state.site_id,
        key: state.site.site_key,
        // The frozen document reports the revision at freeze time; the
        // live drift is surfaced separately by the review banner.
        canonical_revision: state.base_site_revision,
      },
      requested_path: requestedPath,
      matched_path: selection.route,
      locale: page.locale,
      route_parameters: {},
      page: {
        id: page.id,
        site_id: state.site_id,
        slug: page.slug,
        title: page.title,
        status: page.status,
        locale: page.locale,
        parent_id: page.parent_id,
        route_template: page.route_template,
        effective_route: page.effective_route,
        row_version: page.row_version,
      },
      composition: {
        schema_version:
          document.snapshot.versions.composition_schema ?? "composition-schema/v1",
        catalog_version: document.snapshot.versions.catalog ?? "1",
        nodes,
      },
      theme: state.theme,
      // The frozen snapshot captures the site theme; per-page style
      // overrides are not part of the snapshot, so the frozen render
      // applies the site theme as the page style (the trusted
      // no-override fallback).
      page_style: state.theme,
      locales: projectLocales(state, page),
      navigation: projectNavigation(state, page.locale, defaultLocale),
      bindings: {},
      binding_meta: {},
      regions: projectRegions(state),
      ancestors: projectAncestors(state, page),
      default_locale: defaultLocale,
    },
  };
}

/**
 * Prefix an internal review redirect target with the review render base
 * (the frozen redirect set is site-relative, exactly like the preview
 * contract prefixes with ``/preview/{workspaceId}`).
 */
export function reviewRedirectTarget(target: string, workspaceId: string): string {
  if (!target.startsWith("/")) return target;
  return target === "/" ? `/review/${workspaceId}` : `/review/${workspaceId}${target}`;
}

/** Build the server-rendered review banner facts (no client JS). */
export function reviewBannerFacts(document: ReviewDocument): {
  digest: string;
  baseSiteRevision: number;
  currentSiteRevision: number;
  equal: boolean;
  revisionWatermark: number;
} {
  return {
    digest: document.snapshot.digest,
    baseSiteRevision: document.snapshot.base_site_revision,
    currentSiteRevision: document.drift.current_site_revision,
    equal: document.drift.equal,
    revisionWatermark: document.snapshot.revision_watermark,
  };
}

/**
 * Full structural gate for the trusted read-model document (fail closed).
 * Every field the review surface reads is runtime-checked before any part
 * of the document is treated as ``ReviewDocument``; the gate is the single
 * entry for both the frozen render resolver and the admin review view.
 */
export function isReviewDocument(value: unknown): value is ReviewDocument {
  if (!isRecord(value)) return false;
  const snapshot = value["snapshot"];
  const versions = isRecord(snapshot) ? snapshot["versions"] : null;
  if (
    !isRecord(snapshot) ||
    !isString(snapshot["id"]) ||
    !isString(snapshot["digest"]) ||
    !isString(snapshot["state_version"]) ||
    typeof snapshot["revision_watermark"] !== "number" ||
    typeof snapshot["base_site_revision"] !== "number" ||
    !isString(snapshot["status"]) ||
    !isString(snapshot["created_at"]) ||
    !isString(snapshot["created_by"]) ||
    !isRecord(versions)
  ) {
    return false;
  }
  for (const version of Object.values(versions)) {
    if (!isString(version)) return false;
  }
  const drift = value["drift"];
  if (
    !isRecord(drift) ||
    typeof drift["current_site_revision"] !== "number" ||
    typeof drift["base_site_revision"] !== "number" ||
    typeof drift["equal"] !== "boolean"
  ) {
    return false;
  }
  const timeline = value["timeline"];
  if (!Array.isArray(timeline)) return false;
  for (const entry of timeline) {
    if (
      !isRecord(entry) ||
      !isString(entry["operation_id"]) ||
      !isString(entry["operation_type"]) ||
      !Array.isArray(entry["resource"]) ||
      !isString(entry["created_at"])
    ) {
      return false;
    }
  }
  const resourceDiff = value["resource_diff"];
  if (!isRecord(resourceDiff)) return false;
  for (const family of Object.values(resourceDiff)) {
    if (
      !isRecord(family) ||
      !Array.isArray(family["added"]) ||
      !Array.isArray(family["modified"]) ||
      !Array.isArray(family["deleted"])
    ) {
      return false;
    }
    for (const change of family["modified"]) {
      if (!isRecord(change) || !isString(change["id"]) || !isRecord(change["fields"])) {
        return false;
      }
    }
  }
  if (!isRecord(value["summaries"])) return false;
  const validation = value["validation"];
  if (!isRecord(validation) || !Array.isArray(validation["warnings"])) return false;
  const evidence = value["evidence"];
  const evidenceRuns = isRecord(evidence) ? evidence["runs"] : null;
  const evidenceArtifacts = isRecord(evidence) ? evidence["artifacts"] : null;
  if (
    !isRecord(evidence) ||
    !Array.isArray(evidenceRuns) ||
    !Array.isArray(evidenceArtifacts)
  ) {
    return false;
  }
  for (const run of evidenceRuns) {
    if (!isRecord(run) || !isString(run["id"])) return false;
  }
  for (const artifactGroup of evidenceArtifacts) {
    const artifacts = isRecord(artifactGroup) ? artifactGroup["artifacts"] : null;
    if (
      !isRecord(artifactGroup) ||
      !isString(artifactGroup["run_id"]) ||
      !Array.isArray(artifacts)
    ) {
      return false;
    }
    for (const artifact of artifacts) {
      if (
        !isRecord(artifact) ||
        !isString(artifact["artifact_id"]) ||
        !isString(artifact["kind"]) ||
        (artifact["mime_type"] !== null && !isString(artifact["mime_type"]))
      ) {
        return false;
      }
    }
  }
  const metadata = value["metadata"];
  const metadataWorkspace = isRecord(metadata) ? metadata["workspace"] : null;
  const metadataSite = isRecord(metadata) ? metadata["site"] : null;
  const metadataSession = isRecord(metadata) ? metadata["agent_session_browser"] : null;
  if (
    !isRecord(metadata) ||
    !isRecord(metadataWorkspace) ||
    !isString(metadataWorkspace["id"]) ||
    !isString(metadataWorkspace["title"]) ||
    !isString(metadataWorkspace["actor_type"]) ||
    !isString(metadataWorkspace["status"]) ||
    !isRecord(metadataSite) ||
    !isString(metadataSite["id"]) ||
    !isString(metadataSite["key"]) ||
    !Array.isArray(metadata["capabilities"]) ||
    !isRecord(metadata["quota_policy"]) ||
    !isRecord(metadataSession) ||
    !isRecord(metadataSession["versions"]) ||
    !Array.isArray(metadataSession["review_jobs"])
  ) {
    return false;
  }
  for (const version of Object.values(metadataSession["versions"])) {
    if (!isString(version)) return false;
  }
  const state = value["normalized_state"];
  return isRecord(state) && parseReviewState(state) !== null;
}
