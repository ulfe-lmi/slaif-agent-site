/**
 * Puck adapter: maps between the normalized composition tree and Puck's
 * editor data format. Puck is only a visual editing UX layer; normalized
 * composition metadata remains the persistence authority.
 */

export const CATALOG_TYPES = [
  "Section",
  "Container",
  "Columns",
  "Grid",
  "Stack",
  "Spacer",
  "Heading",
  "RichText",
  "Image",
  "Button",
  "Quote",
  "CollectionList",
  "CollectionGrid",
  "CollectionDetail",
  "Hero",
  "Statistics",
  "Timeline",
  "FAQ",
  "Header",
  "Footer",
  "Breadcrumbs",
  "LanguageSwitcher",
] as const;

const CATALOG_TYPE_SET = new Set<string>(CATALOG_TYPES);
const FORBIDDEN_PROP_KEYS = new Set([
  "dangerouslysetinnerhtml",
  "innerhtml",
  "script",
  "eval",
  "onclick",
  "onload",
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

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function assertTrustedType(type: string): void {
  if (!CATALOG_TYPE_SET.has(type)) throw new Error("unknown-component-type");
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
    config[componentType] = {
      type: componentType,
      label: componentType,
      fields: {},
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
