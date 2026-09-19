/**
 * Bounded site-global region schema (global-region/v1).
 *
 * Architecture reference: ARCHITECTURE-for-agents.md §5 (L4 global regions).
 * Region records are site-level COW data (header/footer) with closed variant
 * enums and bounded content documents. This module is product-owned schema
 * shared by the Editor Design surface and tests; it is not generator output
 * and is not the component catalog.
 */

export const GLOBAL_REGION_SCHEMA_VERSION = "global-region/v1" as const;

export type RegionKey = "header" | "footer";
export type HeaderVariant = "institutional" | "minimal";
export type FooterVariant = "multi-column" | "single-column";
export type RegionVariant = HeaderVariant | FooterVariant;
export type RegionTargetKind = "page" | "internal" | "external";

export const REGION_VARIANTS: Readonly<Record<RegionKey, readonly RegionVariant[]>> = {
  header: ["institutional", "minimal"],
  footer: ["multi-column", "single-column"],
};

export const MAX_REGION_LABEL_LENGTH = 256;
export const MAX_REGION_NOTE_LENGTH = 4096;
export const MAX_EXTERNAL_TARGET_LENGTH = 2048;
export const MAX_INTERNAL_TARGET_LENGTH = 256;
export const MAX_REGION_CONTENT_BYTES = 16 * 1024;
export const MAX_HEADER_NAV_ENTRIES = 12;
export const MAX_FOOTER_LINK_ENTRIES = 16;

const PAGE_TARGET = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const INTERNAL_TARGET = /^\/[a-z0-9._~/-]*$/;
const EXTERNAL_TARGET = /^https?:\/\/[^@/][!-~]*$/;
const RESERVED_ROUTE_PREFIXES = [
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
];

export interface RegionTarget {
  readonly kind: RegionTargetKind;
  readonly value: string;
}

export interface RegionEntry {
  readonly label: string;
  readonly target: RegionTarget;
}

export interface HeaderRegionContent {
  readonly nav: readonly RegionEntry[];
}

export interface FooterRegionContent {
  readonly links: readonly RegionEntry[];
  readonly note?: string;
}

export type GlobalRegionContent = HeaderRegionContent | FooterRegionContent;

export interface GlobalRegionRecord {
  readonly id: string;
  readonly site_id: string;
  readonly region_key: RegionKey;
  readonly variant: RegionVariant;
  readonly content: GlobalRegionContent;
  readonly schema_version: typeof GLOBAL_REGION_SCHEMA_VERSION;
  readonly row_version: number;
  readonly created_at: string;
  readonly updated_at: string;
}

/** The lazy bootstrap defaults materialized per region on first write. */
export interface GlobalRegionDefaults {
  readonly header: Readonly<{
    variant: HeaderVariant;
    content: HeaderRegionContent;
  }>;
  readonly footer: Readonly<{
    variant: FooterVariant;
    content: FooterRegionContent;
  }>;
}

export function globalRegionDefaults(siteKey: string): GlobalRegionDefaults {
  return {
    header: {
      variant: "institutional",
      content: {
        nav: [{ label: siteKey, target: { kind: "internal", value: "/" } }],
      },
    },
    footer: {
      variant: "single-column",
      content: { links: [], note: "" },
    },
  };
}

export function isRegionVariant(
  regionKey: RegionKey,
  variant: string,
): variant is RegionVariant {
  return REGION_VARIANTS[regionKey].includes(variant as RegionVariant);
}

export function isRegionTarget(value: unknown): value is RegionTarget {
  if (typeof value !== "object" || value === null) return false;
  const target = value as Record<string, unknown>;
  if (
    target.kind !== "page" &&
    target.kind !== "internal" &&
    target.kind !== "external"
  ) {
    return false;
  }
  if (typeof target.value !== "string") return false;
  return validateRegionTarget(target.kind, target.value);
}

export function validateRegionTarget(kind: string, value: string): boolean {
  if (kind === "page") {
    return PAGE_TARGET.test(value);
  }
  if (kind === "internal") {
    if (value.length < 1 || value.length > MAX_INTERNAL_TARGET_LENGTH) {
      return false;
    }
    if (!INTERNAL_TARGET.test(value)) return false;
    if (value.includes("//") || value.includes("..") || value.includes("%")) {
      return false;
    }
    const first = value.replace(/^\//, "").split("/")[0] ?? "";
    return !RESERVED_ROUTE_PREFIXES.includes(first);
  }
  if (kind === "external") {
    if (value.length < 8 || value.length > MAX_EXTERNAL_TARGET_LENGTH) {
      return false;
    }
    if (value.includes("@")) return false;
    return EXTERNAL_TARGET.test(value);
  }
  return false;
}

/** Serialized bounded document size used for the 16 KiB content bound. */
export function regionContentBytes(content: GlobalRegionContent): number {
  const normalized: Record<string, unknown> =
    "nav" in content
      ? { nav: content.nav }
      : {
          links: content.links,
          ...(content.note !== undefined ? { note: content.note } : {}),
        };
  return new TextEncoder().encode(
    JSON.stringify(normalized, Object.keys(normalized).sort()),
  ).length;
}

export function isGlobalRegionRecord(value: unknown): value is GlobalRegionRecord {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  if (
    typeof record.id !== "string" ||
    typeof record.site_id !== "string" ||
    (record.region_key !== "header" && record.region_key !== "footer")
  ) {
    return false;
  }
  if (!isRegionVariant(record.region_key, record.variant as string)) {
    return false;
  }
  if (record.schema_version !== GLOBAL_REGION_SCHEMA_VERSION) return false;
  if (typeof record.row_version !== "number" || record.row_version <= 0) {
    return false;
  }
  const content = record.content;
  if (typeof content !== "object" || content === null) return false;
  const shape = content as Record<string, unknown>;
  if (record.region_key === "header") {
    return (
      Object.keys(shape).length === 1 &&
      Array.isArray(shape.nav) &&
      shape.nav.length >= 1 &&
      shape.nav.length <= MAX_HEADER_NAV_ENTRIES
    );
  }
  return (
    Object.keys(shape).length <= 2 &&
    Array.isArray(shape.links) &&
    shape.links.length <= MAX_FOOTER_LINK_ENTRIES
  );
}
