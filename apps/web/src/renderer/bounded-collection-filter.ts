/**
 * Bounded client-side filtering over pre-fetched bounded collection
 * bindings. This is the first and only client-state pattern in the
 * trusted renderer: local state only, fixed operator semantics, capped
 * input processing, no network I/O, no persistence, and no URL mutation.
 * The renderer can only ever filter the items the projection already
 * delivered; it cannot widen data access.
 *
 * 083/5-b: the same pure module also hosts the bounded same-path
 * READ-ONLY POST control selection for the flight-free private
 * surfaces (preview/frozen review): server-side, projection-derived
 * authority, no writes.
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

/* ------------------------------------------------------------------ */
/* Bounded same-path POST form decoding (private surfaces)             */
/* ------------------------------------------------------------------ */

/**
 * 083/5-b private search/filter transport: the flight-free preview and
 * review surfaces submit control state as an authenticated READ-ONLY
 * POST to the SAME path. The body is strict
 * ``application/x-www-form-urlencoded`` with finite bounds enforced
 * before any projection work. Decoded fields carry NO identity or
 * authority: the server re-derives every field, operator, facet
 * definition and item set from the trusted projection.
 *
 * Transport representation (083/5-b bound decision): ONE shared native
 * form per page. Every bound collection control renders its own inputs
 * and its own submit button, all associated with the single page form
 * element through the HTML ``form`` attribute. Each control state is
 * represented exactly ONCE in the generated document and exactly once
 * in every submission - no per-control forms, no carried hidden
 * groups, no O(controls^2) matrix. The generated field set of a page is
 * exactly one name per control state slot (``c.<position>.q`` for a
 * CollectionSearch, one ``c.<position>.f<i>`` per TRUSTED facet of a
 * CollectionFilter; position is the control's bounded 0-based inventory
 * position, never the composition node identifier); a valid submission
 * is exactly that set, so
 * multi-control state is preserved across successive submissions with
 * finite O(fields) work and no duplicated bytes.
 */

/**
 * Trusted component catalog bounds mirrored for transport sizing: at
 * most 128 composition nodes per page (MAX_COMPONENTS_PER_PAGE), at
 * most 4 facets per CollectionFilter. Generated form names carry the
 * control's bounded deterministic inventory POSITION (0-based, at most
 * ``String(MAX_CONTROLS_PER_PAGE - 1)`` digits), never the composition
 * node identifier (083/5-b: the raw document - private or canonical -
 * must not leak node UUIDs). The transport caps below are derived
 * EXACTLY from the largest admitted generated form - 128 controls, each
 * a four-facet CollectionFilter - so the own form of every admitted
 * page decodes, and a hostile body cannot exceed them without a uniform
 * refusal.
 */
export const MAX_CONTROLS_PER_PAGE = 128;
export const MAX_FACETS_PER_FILTER = 4;
/** Digits of the largest admitted 0-based control position. */
export const MAX_CONTROL_POSITION_DIGITS = String(MAX_CONTROLS_PER_PAGE - 1).length;
/** Slot name length: ``q`` or ``f<i>``. */
const MAX_SLOT_NAME_LENGTH = 2;
/** Generated name length: ``c.<position>.<slot>``. */
const MAX_CONTROL_FORM_NAME_LENGTH =
  2 + MAX_CONTROL_POSITION_DIGITS + 1 + MAX_SLOT_NAME_LENGTH;
/** Worst slots per control: four facets (a search control has one). */
const MAX_SLOTS_PER_CONTROL = MAX_FACETS_PER_FILTER;

/**
 * Percent-encoding expansion of one value. The raw body is percent-
 * ENCODED ASCII, not decoded Unicode: each UTF-16 code unit of a decoded
 * value occupies at most three UTF-8 bytes (a BMP character) and
 * therefore up to NINE ASCII bytes (`%XX%XX%XX`) in the body. Astral
 * characters (two code units, four UTF-8 bytes) expand to twelve ASCII
 * bytes, so the BMP case is the worst.
 */
const MAX_ENCODED_BYTES_PER_CODE_UNIT = 9;
/** Maximum percent-encoded length of one facet/search value. */
const MAX_ENCODED_VALUE_LENGTH =
  FACET_INPUT_MAX_LENGTH * MAX_ENCODED_BYTES_PER_CODE_UNIT;
/** Worst single form part: generated name + ``=`` + encoded value. */
export const POST_FORM_MAX_PART_LENGTH =
  MAX_CONTROL_FORM_NAME_LENGTH + 1 + MAX_ENCODED_VALUE_LENGTH;

/**
 * Maximum form fields of one admitted page: the complete generated set
 * of the largest admitted control inventory (128 four-facet filters).
 */
export const POST_FORM_MAX_FIELDS = MAX_CONTROLS_PER_PAGE * MAX_SLOTS_PER_CONTROL;

/**
 * Exact total generated-name bytes of the largest admitted form: every
 * control position ``0..MAX_CONTROLS_PER_PAGE - 1`` carries the worst
 * four-facet names, each ``c.<position>.<slot>`` - 5 bytes plus the
 * position's digit count. For 128 positions that is 40 names of 6
 * bytes, 360 of 7 and 112 of 8 (3656 bytes). Deriving the total from
 * the actual position digit lengths keeps the cap exact for every
 * admitted inventory: no uniform name-length padding.
 */
const WORST_TOTAL_NAME_BYTES = Array.from(
  { length: MAX_CONTROLS_PER_PAGE },
  (_, position) =>
    MAX_SLOTS_PER_CONTROL * (2 + String(position).length + 1 + MAX_SLOT_NAME_LENGTH),
).reduce((total, nameBytes) => total + nameBytes, 0);

/**
 * Maximum percent-encoded length of one admitted submission, derived
 * EXACTLY: the worst admitted name-byte total, one ``=`` per part, the
 * worst admitted encoded value total (128 controls x 4 facets x 4096
 * code units x nine encoded bytes per code unit), and the ``&``
 * separators between parts. The largest admitted body therefore sits
 * exactly on this cap: it decodes and is admitted, and one more byte
 * refuses at the length guard.
 */
export const POST_FORM_MAX_BODY_LENGTH =
  WORST_TOTAL_NAME_BYTES +
  POST_FORM_MAX_FIELDS +
  POST_FORM_MAX_FIELDS * MAX_ENCODED_VALUE_LENGTH +
  (POST_FORM_MAX_FIELDS - 1);

/**
 * Raw-bytes cap for the streamed body: a decodable body is percent-
 * encoded ASCII (exactly one raw byte per character - raw non-ASCII
 * bytes are refused by the token decoder), so this equals the body-
 * length cap and strictly bounds the raw input of any decodable body.
 */
export const POST_FORM_MAX_RAW_BYTES = POST_FORM_MAX_BODY_LENGTH;

/** Fatal UTF-8 decoder: invalid byte sequences throw and are refused. */
const UTF8_DECODER = new TextDecoder("utf-8", { fatal: true });

function utf8Decode(bytes: Uint8Array): string | null {
  try {
    return UTF8_DECODER.decode(bytes);
  } catch {
    return null; // malformed UTF-8 sequence: fail closed
  }
}

/**
 * Collect the raw bytes of one urlencoded token: ``+`` is a space,
 * ``%XX`` is a strict hex byte, any other character must be printable
 * ASCII (0x21-0x7E). Raw control characters, raw non-ASCII characters
 * and invalid escapes are refused. Decoded control bytes: NUL and DEL
 * are always refused; the five platform text-whitespace controls (TAB
 * 0x09, LF 0x0A, VT 0x0B, FF 0x0C, CR 0x0D) are ordinary form text in
 * VALUES (the search/facet matcher preserves embedded whitespace, and
 * native form encoding submits them as ``%09`` etc.) while every other
 * C0 control byte is refused. Names (generated ASCII identifiers) allow
 * no control byte at all.
 */
function decodeFormToken(
  token: string,
  allowTextWhitespace: boolean,
): Uint8Array | null {
  const bytes: number[] = [];
  for (let i = 0; i < token.length; i += 1) {
    const character = token.charAt(i);
    if (character === "+") {
      bytes.push(0x20);
      continue;
    }
    if (character === "%") {
      const hex = token.slice(i + 1, i + 3);
      if (!/^[0-9A-Fa-f]{2}$/.test(hex)) return null;
      bytes.push(Number.parseInt(hex, 16));
      i += 2;
      continue;
    }
    const code = character.codePointAt(0) ?? 0;
    if (code < 0x21 || code > 0x7e) return null; // printable ASCII only
    bytes.push(code);
  }
  for (const byte of bytes) {
    if (byte === 0x00 || byte === 0x7f) return null;
    if (byte < 0x20) {
      const isTextWhitespace =
        byte === 0x09 ||
        byte === 0x0a ||
        byte === 0x0b ||
        byte === 0x0c ||
        byte === 0x0d;
      if (!allowTextWhitespace || !isTextWhitespace) return null;
    }
  }
  return new Uint8Array(bytes);
}

/**
 * Strict bounded decode of a same-path POST form body. Tokens are
 * collected as raw bytes and decoded as UTF-8 (fatal), so ordinary
 * Unicode text round-trips exactly like real form encoding. Any
 * deviation - empty body, oversized body or field count, empty part,
 * missing separator, empty name, duplicate name (any name, including
 * special object names), invalid escaping, malformed UTF-8 - is a
 * uniform ``null``: never a partial state, never a silently dropped
 * name. Embedded form whitespace (``%09``/``%0A``/``%0B``/``%0C``/
 * ``%0D``) in values is preserved exactly like native form decoding -
 * the product matchers keep supported embedded whitespace - while NUL,
 * DEL and every other C0 control byte refuse. The result is a ``Map``
 * so every submitted name is retained for validation.
 */
export function decodePostedForm(body: string): Map<string, string> | null {
  if (body.length === 0 || body.length > POST_FORM_MAX_BODY_LENGTH) return null;
  // Bound the field count BEFORE any split/allocation: a many-megabyte
  // hostile body of separators must refuse on the count alone, with O(1)
  // intermediate memory.
  let parts = 1;
  for (let i = 0; i < body.length; i += 1) {
    if (body.charCodeAt(i) === 0x26 /* & */) {
      parts += 1;
      if (parts > POST_FORM_MAX_FIELDS) return null;
    }
  }
  const tokens = body.split("&");
  const fields = new Map<string, string>();
  for (const token of tokens) {
    if (token === "") return null;
    // Bound per-part work BEFORE decoding: an oversized token is refused
    // without a full-length byte collection.
    if (token.length > POST_FORM_MAX_PART_LENGTH) return null;
    const separator = token.indexOf("=");
    if (separator <= 0) return null;
    if (separator > MAX_CONTROL_FORM_NAME_LENGTH) return null;
    const nameBytes = decodeFormToken(token.slice(0, separator), false);
    const valueBytes = decodeFormToken(token.slice(separator + 1), true);
    if (nameBytes === null || valueBytes === null) return null;
    const name = utf8Decode(nameBytes);
    const value = utf8Decode(valueBytes);
    if (name === null || value === null) return null;
    if (name === "" || fields.has(name)) return null;
    fields.set(name, value);
  }
  return fields;
}

/* ------------------------------------------------------------------ */
/* Bounded same-path POST control selection (private surfaces)         */
/* ------------------------------------------------------------------ */

/**
 * 083/5-b same-path read-only POST control state for ONE bound
 * collection control of one page: the current values of its own inputs
 * (``own``: ``q`` or ``f<i>`` per facet) and the bounded result items
 * (``filtered``) recomputed over the items the projection already
 * delivered. The single shared page form submits EVERY bound control's
 * inputs in one body, so one submission always carries the complete
 * multi-control state - no carried groups, no persistence, no
 * query-string leakage, no body-selected authority.
 */
export type ControlRenderState = Readonly<{
  readonly nodeId: string;
  readonly kind: "search" | "filter";
  readonly own: Readonly<Record<string, string>>;
  readonly filtered: readonly Record<string, unknown>[];
}>;

/** Identifier of the one shared page form element rendered per page. */
export const PAGE_CONTROL_FORM_ID = "slaif-page-control-form";

/**
 * Minimal structural input port of the pure control-state helpers: the
 * subset of the trusted page projection these helpers read (composition
 * node tree, delivered binding items, filter-field metadata). The
 * server-side ``PageProjection`` satisfies this port structurally;
 * declaring the input here keeps this pure module OUT of the server
 * implementation's module graph, so contract projects that type-check
 * the helper without the web ambient declarations (for example the
 * standalone E2E tsconfig) never resolve the server-only boundary.
 */
type ControlNode = Readonly<{
  readonly id: string;
  readonly component_type: string;
  readonly props: Readonly<Record<string, unknown>>;
  readonly children: readonly ControlNode[];
}>;

type ControlProjectionInput = Readonly<{
  readonly composition: Readonly<{ readonly nodes: readonly ControlNode[] }>;
  readonly bindings: Readonly<
    Record<string, readonly Record<string, unknown>[] | undefined>
  >;
  readonly binding_meta: Readonly<
    Record<
      string,
      Readonly<{ readonly filter_fields: readonly FilterField[] }> | undefined
    >
  >;
}>;

/**
 * The page's bound collection controls (CollectionSearch/CollectionFilter
 * composition nodes) in deterministic tree order. The control inventory
 * is always derived from the trusted projection - never from the body.
 * A CollectionFilter without trusted facets has no state to carry or
 * submit (the catalog requires at least one facet), so it renders the
 * inert static variant and is not a bound control.
 */
export function controlInventory(projection: ControlProjectionInput): ControlNode[] {
  const out: ControlNode[] = [];
  const walk = (nodes: readonly ControlNode[]): void => {
    for (const node of nodes) {
      if (node.component_type === "CollectionSearch") {
        out.push(node);
      } else if (
        node.component_type === "CollectionFilter" &&
        parseCollectionFacets(node.props).length > 0
      ) {
        out.push(node);
      }
      walk(node.children);
    }
  };
  walk(projection.composition.nodes);
  return out;
}

/**
 * The generated form field names of one control at its trusted
 * inventory POSITION: ``c.<position>.q`` for a search control, one
 * ``c.<position>.f<i>`` per TRUSTED facet (facet order from the node's
 * own props) for a filter control. The position is the control's
 * 0-based index in the deterministic trusted inventory (tree order);
 * BOTH the document renderer and the POST verifier re-derive it from
 * the same trusted projection, so a posted name is admitted only when
 * it matches the page's generated set exactly. The node identifier
 * itself never appears in a generated document.
 */
export function searchControlFieldName(position: number): string {
  return `c.${position}.q`;
}

export function filterControlFieldName(position: number, index: number): string {
  return `c.${position}.f${index}`;
}

export function controlFieldNames(node: ControlNode, position: number): string[] {
  if (node.component_type === "CollectionSearch") {
    return [searchControlFieldName(position)];
  }
  return parseCollectionFacets(node.props).map((_, index) =>
    filterControlFieldName(position, index),
  );
}

/**
 * The bounded deterministic position of every bound control: the node's
 * 0-based index in the trusted inventory tree order. Derived from the
 * trusted projection only - the document renderer and the POST verifier
 * must both re-derive positions this way (or an equivalent trusted
 * re-derivation) so generated names and posted names agree exactly.
 */
export function controlPositions(
  projection: ControlProjectionInput,
): ReadonlyMap<string, number> {
  const out = new Map<string, number>();
  for (const [position, node] of controlInventory(projection).entries()) {
    out.set(node.id, position);
  }
  return out;
}

function deliveredItems(
  projection: ControlProjectionInput,
  nodeId: string,
): readonly Record<string, unknown>[] {
  const items = projection.bindings[nodeId];
  if (items === undefined) return [];
  return items;
}

function filterDelivered(
  node: ControlNode,
  projection: ControlProjectionInput,
  facets: readonly CollectionFacet[],
  query: string,
): readonly Record<string, unknown>[] {
  const items = deliveredItems(projection, node.id);
  const filterFields = projection.binding_meta[node.id]?.filter_fields ?? [];
  if (node.component_type === "CollectionSearch") {
    return items.filter((item) => matchesSearch(item, filterFields, query));
  }
  return items.filter((item) => matchesAllFacets(item, filterFields, facets));
}

/**
 * The page's control states with every control at its TRUSTED initial
 * values (what a fresh GET document renders: empty search, the node's
 * own facet defaults). Total over every admitted projection: each bound
 * control yields exactly one state; a page without bound controls
 * yields the empty map.
 */
export function defaultControlStates(
  projection: ControlProjectionInput,
): ReadonlyMap<string, ControlRenderState> {
  const states = new Map<string, ControlRenderState>();
  for (const node of controlInventory(projection)) {
    if (node.component_type === "CollectionSearch") {
      states.set(node.id, {
        nodeId: node.id,
        kind: "search",
        own: { q: "" },
        filtered: filterDelivered(node, projection, [], ""),
      });
      continue;
    }
    const facets = parseCollectionFacets(node.props);
    const own: Record<string, string> = {};
    facets.forEach((facet, index) => {
      own[`f${index}`] = facet.value;
    });
    states.set(node.id, {
      nodeId: node.id,
      kind: "filter",
      own,
      filtered: filterDelivered(node, projection, facets, ""),
    });
  }
  return states;
}

/**
 * 083/5-b: validate and select the posted control states of one
 * same-path POST submission over the SINGLE shared page form. The body
 * supplies control STATE only, and exactly the page's generated field
 * set - one ``c.<position>.q`` per search control and one
 * ``c.<position>.f<i>`` per TRUSTED facet of every filter control,
 * where the position is the control's 0-based index in the trusted
 * inventory (re-derived here from the trusted projection, never taken
 * from the body). Field names, operators, facet keys, item data and
 * the control inventory always come from the trusted projection. Any
 * mismatch - missing or extra field, unknown name or position
 * (including authority-like special names), oversized value - is a
 * uniform ``null`` refusal.
 */
export function selectPostedControls(
  projection: ControlProjectionInput,
  fields: ReadonlyMap<string, string>,
): Readonly<{
  readonly states: ReadonlyMap<string, ControlRenderState>;
}> | null {
  const inventory = controlInventory(projection);
  const expected = new Set<string>();
  for (let position = 0; position < inventory.length; position += 1) {
    const node = inventory[position];
    if (node === undefined) return null;
    for (const name of controlFieldNames(node, position)) expected.add(name);
  }
  if (fields.size !== expected.size) return null;
  for (const name of fields.keys()) {
    if (!expected.has(name)) return null;
  }
  const states = new Map<string, ControlRenderState>();
  for (let position = 0; position < inventory.length; position += 1) {
    const node = inventory[position];
    if (node === undefined) return null;
    if (node.component_type === "CollectionSearch") {
      const query = fields.get(searchControlFieldName(position));
      if (query === undefined || query.length > SEARCH_INPUT_MAX_LENGTH) {
        return null;
      }
      states.set(node.id, {
        nodeId: node.id,
        kind: "search",
        own: { q: query },
        filtered: filterDelivered(node, projection, [], query),
      });
      continue;
    }
    const facets = parseCollectionFacets(node.props);
    const own: Record<string, string> = {};
    const posted: CollectionFacet[] = [];
    for (let index = 0; index < facets.length; index += 1) {
      const facet = facets[index];
      if (facet === undefined) return null;
      const value = fields.get(filterControlFieldName(position, index));
      if (value === undefined || value.length > FACET_INPUT_MAX_LENGTH) {
        return null;
      }
      own[`f${index}`] = value;
      posted.push({ ...facet, value });
    }
    states.set(node.id, {
      nodeId: node.id,
      kind: "filter",
      own,
      filtered: filterDelivered(node, projection, posted, ""),
    });
  }
  return { states };
}
