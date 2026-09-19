/**
 * Bounded client-side filtering over pre-fetched bounded collection
 * bindings. This is the first and only client-state pattern in the
 * trusted renderer: local state only, fixed operator semantics, capped
 * input processing, no network I/O, no persistence, and no URL mutation.
 * The renderer can only ever filter the items the projection already
 * delivered; it cannot widen data access.
 */

export interface FilterField {
  readonly key: string;
  readonly primitive: string;
}

export interface CollectionFacet {
  readonly fieldKey: string;
  readonly operator: string;
  readonly value: string;
}

/** CollectionSearch input processing cap (characters). */
export const SEARCH_INPUT_MAX_LENGTH = 256;
/** CollectionFilter facet value cap (characters), mirroring the catalog. */
export const FACET_INPUT_MAX_LENGTH = 4096;
/** CollectionFilter `in` list bounds, mirroring the write-time contract. */
export const IN_LIST_MAX_ENTRIES = 8;
export const IN_LIST_ENTRY_MAX_LENGTH = 256;

export const TEXT_PRIMITIVES = new Set(["short_text", "long_text", "url", "email"]);
export const SEARCH_TEXT_PRIMITIVES = new Set(["short_text", "long_text"]);
export const NUMERIC_PRIMITIVES = new Set(["integer", "decimal"]);
export const DATE_PRIMITIVES = new Set(["date", "datetime"]);

export function capSearchInput(value: string): string {
  return value.slice(0, SEARCH_INPUT_MAX_LENGTH);
}

export function capFacetInput(value: string): string {
  return value.slice(0, FACET_INPUT_MAX_LENGTH);
}

export function stringValue(value: unknown): string | null {
  return typeof value === "string" ? value : null;
}

export function itemValues(
  item: Readonly<Record<string, unknown>>,
): Readonly<Record<string, unknown>> {
  const values = item.values;
  return typeof values === "object" && values !== null
    ? (values as Readonly<Record<string, unknown>>)
    : {};
}

export function itemTitle(item: Readonly<Record<string, unknown>>): string {
  const values = itemValues(item);
  return stringValue(values.title) ?? stringValue(item.slug) ?? "";
}

/**
 * CollectionSearch semantics: case-insensitive `contains` over the item
 * title and every short/long text value; an empty query matches all.
 */
export function matchesSearch(
  item: Readonly<Record<string, unknown>>,
  filterFields: readonly FilterField[],
  query: string,
): boolean {
  const needle = query.trim().toLowerCase();
  if (needle === "") return true;
  if (itemTitle(item).toLowerCase().includes(needle)) return true;
  const values = itemValues(item);
  return filterFields.some((field) => {
    if (!SEARCH_TEXT_PRIMITIVES.has(field.primitive)) return false;
    const value = stringValue(values[field.key]);
    return value !== null && value.toLowerCase().includes(needle);
  });
}

export function numericValue(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value.trim());
    if (Number.isFinite(parsed)) return parsed;
  }
  return null;
}

export function dateValue(value: unknown): number | null {
  if (typeof value !== "string" || value.trim() === "") return null;
  const parsed = Date.parse(value.trim());
  return Number.isNaN(parsed) ? null : parsed;
}

/** Fixed `in` list semantics: comma-separated, trimmed, capped. */
export function splitInList(value: string): string[] {
  return value
    .split(",")
    .map((entry) => entry.trim().slice(0, IN_LIST_ENTRY_MAX_LENGTH))
    .filter((entry) => entry !== "")
    .slice(0, IN_LIST_MAX_ENTRIES);
}

/**
 * Parse and sanitize the ``facets`` prop of a CollectionFilter node.
 * Malformed entries are dropped: shape-invalid props are rejected at
 * write time by the catalog guard, so this only ever sees shape-valid
 * facets in trusted renderings and degrades safely elsewhere.
 */
export function parseCollectionFacets(
  props: Readonly<Record<string, unknown>>,
): CollectionFacet[] {
  const raw = props.facets;
  if (!Array.isArray(raw)) return [];
  const facets: CollectionFacet[] = [];
  for (const entry of raw) {
    if (typeof entry !== "object" || entry === null) continue;
    const record = entry as Record<string, unknown>;
    const fieldKey = typeof record.fieldKey === "string" ? record.fieldKey : "";
    const operator = typeof record.operator === "string" ? record.operator : "";
    const value = typeof record.value === "string" ? record.value : "";
    if (!fieldKey || !operator) continue;
    facets.push({ fieldKey, operator, value });
  }
  return facets;
}

/**
 * CollectionFilter semantics: fixed per-primitive operator comparisons.
 * Unknown primitives, missing values, and unparseable operands never
 * match (fail-closed).
 */
export function matchesFacet(
  item: Readonly<Record<string, unknown>>,
  filterFields: readonly FilterField[],
  facet: CollectionFacet,
): boolean {
  const field = filterFields.find((candidate) => candidate.key === facet.fieldKey);
  if (field === undefined) return false;
  const raw = itemValues(item)[field.key];
  if (raw === undefined || raw === null) return false;
  const value = facet.value.trim();
  if (value === "") return false;
  const operator = facet.operator;
  if (TEXT_PRIMITIVES.has(field.primitive)) {
    const text = stringValue(raw);
    if (text === null) return false;
    const target = text.toLowerCase();
    const needle = value.toLowerCase();
    if (operator === "eq") return target === needle;
    if (operator === "contains") return target.includes(needle);
    if (operator === "prefix") return target.startsWith(needle);
    return false;
  }
  if (NUMERIC_PRIMITIVES.has(field.primitive)) {
    const left = numericValue(raw);
    const right = numericValue(value);
    if (left === null || right === null) return false;
    if (operator === "eq") return left === right;
    if (operator === "lt") return left < right;
    if (operator === "lte") return left <= right;
    if (operator === "gt") return left > right;
    if (operator === "gte") return left >= right;
    return false;
  }
  if (DATE_PRIMITIVES.has(field.primitive)) {
    const left = dateValue(raw);
    const right = dateValue(value);
    if (left === null || right === null) return false;
    if (operator === "eq") return left === right;
    if (operator === "lt") return left < right;
    if (operator === "lte") return left <= right;
    if (operator === "gt") return left > right;
    if (operator === "gte") return left >= right;
    return false;
  }
  if (field.primitive === "boolean") {
    if (operator !== "eq") return false;
    if (value.toLowerCase() === "true") return raw === true;
    if (value.toLowerCase() === "false") return raw === false;
    return false;
  }
  if (field.primitive === "enum") {
    const entry = stringValue(raw);
    if (entry === null) return false;
    if (operator === "eq") return entry.toLowerCase() === value.toLowerCase();
    if (operator === "in") {
      return splitInList(facet.value).some(
        (candidate) => entry.toLowerCase() === candidate.toLowerCase(),
      );
    }
    return false;
  }
  return false;
}

export function matchesAllFacets(
  item: Readonly<Record<string, unknown>>,
  filterFields: readonly FilterField[],
  facets: readonly CollectionFacet[],
): boolean {
  return facets.every((facet) => matchesFacet(item, filterFields, facet));
}
