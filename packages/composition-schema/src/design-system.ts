/** Generated design-system/v1 view; edit component-catalog authority instead. */

import designSystem from "./design-system-v1.json" with { type: "json" };

export const RESPONSIVE_LABELS = ["desktop", "tablet", "mobile"] as const;
export type ResponsiveLabel = (typeof RESPONSIVE_LABELS)[number];

export interface DesignProperty {
  readonly name: string;
  readonly type: "enum" | "number";
  readonly values?: readonly string[];
  readonly minimum?: number;
  readonly maximum?: number;
  readonly default: string | number;
  readonly required: boolean;
  readonly responsive: true;
  readonly scope: "component-props:write" | "component-variant:write" | "layout:write";
  readonly token: string;
}

interface DesignComponent {
  readonly type: string;
  readonly variants: readonly string[];
  readonly properties: readonly DesignProperty[];
}

interface DesignSystemDocument {
  readonly components: readonly DesignComponent[];
}

const document = designSystem as DesignSystemDocument;

export function designComponent(type: string): DesignComponent | undefined {
  return document.components.find((item) => item.type === type);
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
