/** Generated design-system/v1 authority; edit design-system-v1.json instead. */

import designSystem from "./design-system-v1.json" with { type: "json" };

export const DESIGN_SYSTEM_VERSION = "design-system/v1" as const;
export const DESIGN_SYSTEM_CATALOG_VERSION = "catalog-v1" as const;
export const DESIGN_SYSTEM_COMPOSITION_SCHEMA_VERSION = "site-composition/v1" as const;
export const DESIGN_SYSTEM_RENDERER_VERSION = "renderer-v1" as const;
export const RESPONSIVE_LABELS = ["desktop", "tablet", "mobile"] as const;
export type ResponsiveLabel = (typeof RESPONSIVE_LABELS)[number];
export type DesignScope =
  | "component-props:write"
  | "component-variant:write"
  | "layout:write"
  | "responsive-design:write";

export interface DesignProperty {
  readonly name: string;
  readonly type: "enum" | "number";
  readonly values?: readonly string[];
  readonly minimum?: number;
  readonly maximum?: number;
  readonly default: string | number;
  readonly required: boolean;
  readonly responsive: true;
  readonly scope: Exclude<DesignScope, "responsive-design:write">;
  readonly token: string;
}

export interface DesignComponent {
  readonly type: string;
  readonly variants: readonly string[];
  readonly properties: readonly DesignProperty[];
}

export interface DesignTokens {
  readonly spacing: readonly string[];
  readonly gap: readonly string[];
  readonly width: readonly string[];
  readonly alignment: readonly string[];
  readonly columns: readonly number[];
  readonly radius: readonly string[];
  readonly shadow: readonly string[];
  readonly aspect_ratio: readonly string[];
}

export interface DesignSystemDocument {
  readonly version: typeof DESIGN_SYSTEM_VERSION;
  readonly catalog_version: typeof DESIGN_SYSTEM_CATALOG_VERSION;
  readonly composition_schema_version: typeof DESIGN_SYSTEM_COMPOSITION_SCHEMA_VERSION;
  readonly renderer_version: typeof DESIGN_SYSTEM_RENDERER_VERSION;
  readonly responsive_labels: readonly ResponsiveLabel[];
  readonly responsive_scope: "responsive-design:write";
  readonly responsive_fallback: readonly ResponsiveLabel[];
  readonly tokens: DesignTokens;
  readonly components: readonly DesignComponent[];
}

export const DESIGN_SYSTEM_DOCUMENT = designSystem as DesignSystemDocument;

export function designComponent(type: string): DesignComponent | undefined {
  return DESIGN_SYSTEM_DOCUMENT.components.find((item) => item.type === type);
}

export function designProperty(
  componentType: string,
  name: string,
): DesignProperty | undefined {
  return designComponent(componentType)?.properties.find((item) => item.name === name);
}

export function isResponsiveValue(
  value: unknown,
): value is Partial<Record<ResponsiveLabel, string | number>> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) return false;
  const entries = Object.entries(value);
  return (
    entries.length > 0 &&
    entries.length <= RESPONSIVE_LABELS.length &&
    entries.every(
      ([key, item]) =>
        RESPONSIVE_LABELS.includes(key as ResponsiveLabel) &&
        ((typeof item === "string" && item.length > 0) ||
          (typeof item === "number" && Number.isFinite(item))),
    )
  );
}
