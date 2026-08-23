/**
 * Normalized composition schema (site-composition/v1).
 *
 * Architecture reference: ARCHITECTURE-for-agents.md §7. The composition is
 * a tree of stable component nodes with IDs, types, slots, order keys, and
 * validated props. This is the authoritative representation shared between
 * Puck editing and agent API operations.
 */

export const COMPOSITION_SCHEMA_VERSION = "site-composition/v1";

export interface CompositionNode {
  readonly id: string;
  readonly componentType: string;
  readonly schemaVersion: string;
  readonly parentId: string | null;
  readonly slotKey: string;
  readonly orderKey: number;
  readonly props: Record<string, unknown>;
  readonly children: readonly CompositionNode[];
}

export interface PageComposition {
  readonly pageId: string;
  readonly siteId: string;
  readonly locale: string;
  readonly schemaVersion: typeof COMPOSITION_SCHEMA_VERSION;
  readonly root: CompositionNode | null;
  readonly catalogVersion: string;
}

export interface CompositionOperation {
  readonly operationId: string;
  readonly kind:
    "component.add" | "component.update" | "component.move" | "component.delete";
  readonly nodeId: string;
  readonly payload: Record<string, unknown>;
}

export function isCompositionNode(value: unknown): value is CompositionNode {
  if (typeof value !== "object" || value === null) return false;
  const node = value as Record<string, unknown>;
  return (
    typeof node.id === "string" &&
    typeof node.componentType === "string" &&
    (node.parentId === null || typeof node.parentId === "string") &&
    typeof node.slotKey === "string" &&
    typeof node.orderKey === "number" &&
    typeof node.props === "object"
  );
}

export * from "./puck-adapter";
