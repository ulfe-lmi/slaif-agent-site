import catalog from "./catalog-v1.json" with { type: "json" };
import {
  designComponent,
  designProperty,
  isResponsiveValue,
  type DesignProperty,
} from "./design-system";
export { generatePuckThemeConfig } from "./theme-schema";

/**
 * Puck adapter: maps between the normalized composition tree and Puck's
 * editor data format. Puck is only a visual editing UX layer; normalized
 * composition metadata remains the persistence authority.
 */

type CatalogType =
  "string" | "number" | "boolean" | "enum" | "reference" | "object" | "array";

interface CatalogSchema {
  readonly type: CatalogType;
  readonly required?: boolean | readonly string[];
  readonly enum_values?: readonly string[];
  readonly minimum?: number;
  readonly maximum?: number;
  readonly min_items?: number;
  readonly max_items?: number;
  readonly max_length?: number;
  readonly properties?: Readonly<Record<string, CatalogSchema>>;
  readonly additional_properties?: boolean;
  readonly items?: CatalogSchema;
}

interface CatalogProp extends CatalogSchema {
  readonly required: boolean;
  readonly authority: "content" | "design";
  readonly schema?: CatalogSchema;
}

interface CatalogComponent {
  readonly type: string;
  readonly props: Readonly<Record<string, CatalogProp>>;
}

const CATALOG_COMPONENTS = catalog.components as readonly CatalogComponent[];
export const CATALOG_TYPES = CATALOG_COMPONENTS.map(
  (component) => component.type,
) as readonly string[];

const CATALOG_TYPE_SET = new Set<string>(CATALOG_TYPES);
const FORBIDDEN_PROP_KEYS = new Set([
  "__proto__",
  "constructor",
  "prototype",
  "style",
  "class",
  "classname",
  "dangerouslysetinnerhtml",
  "innerhtml",
  "handler",
  "script",
  "eval",
  "onclick",
  "onload",
  "html",
  "template",
  "query",
  "code",
  "package",
  "callback",
]);

export interface NormalizedCompositionNode {
  readonly id: string;
  readonly componentType: string;
  readonly schemaVersion: string;
  readonly parentId: string | null;
  readonly slotKey: string;
  readonly orderKey: number;
  readonly props: Record<string, unknown>;
}

export interface PuckNode {
  type: string;
  props: Record<string, unknown>;
}

export interface PuckNodeMetadata {
  readonly componentType: string;
  readonly schemaVersion: string;
  readonly parentId: string | null;
  readonly slotKey: string;
  readonly orderKey: number;
}

export interface PuckData {
  content: PuckNode[];
  root: Record<string, unknown>;
  /** Legacy DropZone storage used by @measured/puck 0.20.x. */
  zones?: Record<string, PuckNode[]>;
  /** Adapter bookkeeping; never persisted as component props. */
  metadata?: Record<string, PuckNodeMetadata>;
}

export interface PuckField {
  type: string;
  label?: string;
  options?: string[];
  min?: number;
  max?: number;
}

export interface PuckComponentConfig {
  type: string;
  label: string;
  fields: Record<string, PuckField>;
}

function assertDesignValue(value: unknown, definition: DesignProperty): void {
  if (isResponsiveValue(value)) {
    for (const item of Object.values(value)) assertDesignValue(item, definition);
    return;
  }
  if (definition.type === "enum") {
    if (typeof value !== "string" || !definition.values?.includes(value))
      throw new Error("invalid-component-props");
    return;
  }
  if (typeof value !== "number" || !Number.isFinite(value))
    throw new Error("invalid-component-props");
  if (definition.minimum !== undefined && value < definition.minimum)
    throw new Error("invalid-component-props");
  if (definition.maximum !== undefined && value > definition.maximum)
    throw new Error("invalid-component-props");
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function assertTrustedType(type: string): void {
  if (!CATALOG_TYPE_SET.has(type)) throw new Error("unknown-component-type");
}

function assertSchema(value: unknown, schema: CatalogSchema): void {
  if (schema.type === "string") {
    if (typeof value !== "string") throw new Error("invalid-component-props");
    if (schema.max_length !== undefined && value.length > schema.max_length)
      throw new Error("invalid-component-props");
    const lowered = value.toLowerCase();
    if (
      lowered.startsWith("javascript:") ||
      lowered.startsWith("data:") ||
      lowered.startsWith("file:") ||
      lowered.startsWith("vbscript:") ||
      lowered.includes("<script") ||
      lowered.includes("onerror=") ||
      lowered.includes("onload=")
    )
      throw new Error("invalid-component-props");
    return;
  }
  if (schema.type === "number") {
    if (typeof value !== "number" || !Number.isFinite(value))
      throw new Error("invalid-component-props");
    if (schema.minimum !== undefined && value < schema.minimum)
      throw new Error("invalid-component-props");
    if (schema.maximum !== undefined && value > schema.maximum)
      throw new Error("invalid-component-props");
    return;
  }
  if (schema.type === "boolean") {
    if (typeof value !== "boolean") throw new Error("invalid-component-props");
    return;
  }
  if (schema.type === "enum") {
    if (typeof value !== "string" || !schema.enum_values?.includes(value))
      throw new Error("invalid-component-props");
    return;
  }
  if (schema.type === "reference") {
    if (
      typeof value !== "string" ||
      !/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
        value,
      )
    )
      throw new Error("invalid-component-props");
    return;
  }
  if (schema.type === "object") {
    if (!isRecord(value)) throw new Error("invalid-component-props");
    if (
      Array.isArray(schema.required) &&
      schema.required.some((key) => !(key in value))
    )
      throw new Error("invalid-component-props");
    const properties = schema.properties ?? {};
    if (
      schema.additional_properties === false &&
      Object.keys(value).some((key) => !(key in properties))
    )
      throw new Error("invalid-component-props");
    for (const [key, child] of Object.entries(value)) {
      const childSchema = properties[key];
      if (childSchema) assertSchema(child, childSchema);
    }
    return;
  }
  if (schema.type === "array") {
    if (!Array.isArray(value)) throw new Error("invalid-component-props");
    if (schema.min_items !== undefined && value.length < schema.min_items)
      throw new Error("invalid-component-props");
    if (schema.max_items !== undefined && value.length > schema.max_items)
      throw new Error("invalid-component-props");
    if (schema.items) value.forEach((item) => assertSchema(item, schema.items!));
  }
}

function assertCatalogProps(
  componentType: string,
  props: Record<string, unknown>,
): void {
  assertTrustedType(componentType);
  const component = CATALOG_COMPONENTS.find(
    (candidate) => candidate.type === componentType,
  );
  if (!component) throw new Error("unknown-component-type");
  const definitions = component.props;
  for (const [key, definition] of Object.entries(definitions)) {
    if (definition.required && !(key in props))
      throw new Error("invalid-component-props");
  }
  for (const [key, value] of Object.entries(props)) {
    const definition = definitions[key];
    const design = designProperty(componentType, key);
    if (design) {
      assertDesignValue(value, design);
      continue;
    }
    if (!definition) throw new Error("invalid-component-props");
    assertSchema(value, definition.schema ?? definition);
  }
  if (componentType === "Button") {
    const href = props.href;
    if (typeof href !== "string" || href.startsWith("//") || !href.startsWith("/"))
      throw new Error("invalid-component-props");
  }
}

function assertSafeProps(props: Record<string, unknown>): void {
  for (const key of Object.keys(props)) {
    if (key === "id" || FORBIDDEN_PROP_KEYS.has(key.toLowerCase())) {
      throw new Error("forbidden-component-prop");
    }
  }
}

function zoneKey(parentId: string, slotKey: string): string {
  return `${parentId}:${slotKey}`;
}

function orderedNodes(
  nodes: readonly NormalizedCompositionNode[],
): NormalizedCompositionNode[] {
  return [...nodes].sort((left, right) => {
    if (left.orderKey !== right.orderKey) return left.orderKey - right.orderKey;
    return left.id.localeCompare(right.id);
  });
}

export function generatePuckConfig(): Record<string, PuckComponentConfig> {
  const config: Record<string, PuckComponentConfig> = {};
  for (const componentType of CATALOG_TYPES) {
    const fields: Record<string, PuckField> = {};
    for (const property of designComponent(componentType)?.properties ?? []) {
      fields[property.name] =
        property.type === "enum"
          ? {
              type: "select",
              label: `${property.name} (responsive-safe)`,
              options: [...(property.values ?? [])],
            }
          : {
              type: "number",
              label: `${property.name} (responsive-safe)`,
              ...(property.minimum === undefined ? {} : { min: property.minimum }),
              ...(property.maximum === undefined ? {} : { max: property.maximum }),
            };
    }
    config[componentType] = {
      type: componentType,
      label: componentType,
      fields,
    };
  }
  return config;
}

/** Convert normalized nodes to Puck content plus stable zone/metadata indexes. */
export function compositionToPuck(
  nodes: readonly NormalizedCompositionNode[],
): PuckData {
  const content: PuckNode[] = [];
  const zones: Record<string, PuckNode[]> = {};
  const metadata: Record<string, PuckNodeMetadata> = {};
  const seen = new Set<string>();

  for (const node of orderedNodes(nodes)) {
    assertTrustedType(node.componentType);
    if (seen.has(node.id)) throw new Error("duplicate-component-id");
    if (!isRecord(node.props)) throw new Error("invalid-component-props");
    assertSafeProps(node.props);
    assertCatalogProps(node.componentType, node.props);
    seen.add(node.id);
    metadata[node.id] = {
      componentType: node.componentType,
      schemaVersion: node.schemaVersion,
      parentId: node.parentId,
      slotKey: node.slotKey,
      orderKey: node.orderKey,
    };
    const puckNode = {
      type: node.componentType,
      props: { ...node.props, id: node.id },
    };
    if (node.parentId === null) content.push(puckNode);
    else {
      const key = zoneKey(node.parentId, node.slotKey);
      (zones[key] ??= []).push(puckNode);
    }
  }
  return { content, root: { props: { locale: "en" } }, zones, metadata };
}

function originalOrder(
  metadata: Record<string, PuckNodeMetadata>,
  parentId: string | null,
  slotKey: string,
): string[] {
  return Object.entries(metadata)
    .filter(([, value]) => value.parentId === parentId && value.slotKey === slotKey)
    .sort(([leftId, left], [rightId, right]) =>
      left.orderKey === right.orderKey
        ? leftId.localeCompare(rightId)
        : left.orderKey - right.orderKey,
    )
    .map(([id]) => id);
}

function getNodeId(node: PuckNode): string {
  if (!isRecord(node.props)) throw new Error("invalid-component-props");
  const id = node.props.id;
  return typeof id === "string" && id.length > 0 ? id : crypto.randomUUID();
}

/**
 * Convert Puck data back to flat normalized nodes. Existing order keys are
 * preserved for an unchanged zone; edited zones receive deterministic index
 * order keys. Adapter metadata is separate from persisted props.
 */
export function puckToComposition(
  data: PuckData,
  suppliedMetadata: Record<string, PuckNodeMetadata> = data.metadata ?? {},
): readonly NormalizedCompositionNode[] {
  if (!Array.isArray(data.content)) throw new Error("invalid-puck-content");
  const zones = data.zones ?? {};
  const result: NormalizedCompositionNode[] = [];
  const seen = new Set<string>();

  function visit(nodes: PuckNode[], parentId: string | null, slotKey: string): void {
    const ids = nodes.map(getNodeId);
    const previous = originalOrder(suppliedMetadata, parentId, slotKey);
    const unchanged =
      ids.length === previous.length &&
      ids.every((id, index) => id === previous[index]);
    nodes.forEach((node, index) => {
      assertTrustedType(node.type);
      if (!isRecord(node.props)) throw new Error("invalid-component-props");
      const id = ids[index];
      if (!id || seen.has(id)) throw new Error("duplicate-component-id");
      const { id: _bookkeepingId, ...props } = node.props;
      void _bookkeepingId;
      assertSafeProps(props);
      assertCatalogProps(node.type, props);
      seen.add(id);
      const prior = suppliedMetadata[id];
      const actualSlot =
        parentId === null && prior?.parentId === null ? prior.slotKey : slotKey;
      result.push({
        id,
        componentType: node.type,
        schemaVersion: prior?.schemaVersion ?? "1",
        parentId,
        slotKey: actualSlot,
        orderKey: unchanged && prior ? prior.orderKey : index,
        props,
      });
      for (const [key, children] of Object.entries(zones)) {
        const prefix = `${id}:`;
        if (key.startsWith(prefix)) {
          if (!Array.isArray(children)) throw new Error("invalid-puck-zone");
          visit(children, id, key.slice(prefix.length));
        }
      }
    });
  }

  visit(data.content, null, "default");
  return result;
}
