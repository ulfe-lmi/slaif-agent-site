import schema from "./theme-schema-v1.json" with { type: "json" };

export const THEME_SCHEMA_VERSION = "theme-schema/v1" as const;
export const THEME_RENDERER_VERSION = "renderer-v1" as const;
export const THEME_RESPONSIVE_LABELS = ["desktop", "tablet", "mobile"] as const;

export type ThemePalettePreset = "ocean" | "meadow" | "ember";
export type ThemeTypographyFamily = "system" | "serif" | "mono";
export type ThemeTypographyScale = "compact" | "balanced" | "spacious";
export type ThemeTypographyWeight = "regular" | "medium" | "bold";
export type ThemeLayoutToken = "sm" | "md" | "lg" | "xl";
export type ThemeSpacingToken = "sm" | "md" | "lg";
export type ThemeRadiusToken = "none" | "sm" | "md" | "lg" | "full";
export type ThemeShadowToken = "none" | "sm" | "md" | "lg";

export interface ThemePalette {
  readonly preset: ThemePalettePreset;
}

export interface ThemeTypography {
  readonly family: ThemeTypographyFamily;
  readonly scale: ThemeTypographyScale;
  readonly weight: ThemeTypographyWeight;
}

export interface ThemeLayout {
  readonly content_width: ThemeLayoutToken;
  readonly spacing: ThemeSpacingToken;
  readonly grid_gap: ThemeSpacingToken;
}

export interface ThemeShape {
  readonly radius: ThemeRadiusToken;
  readonly shadow: ThemeShadowToken;
}

export interface ThemeRecord {
  readonly id: string;
  readonly site_id: string;
  readonly schema_version: typeof THEME_SCHEMA_VERSION;
  readonly renderer_version: typeof THEME_RENDERER_VERSION;
  readonly row_version: number;
  readonly palette: ThemePalette;
  readonly typography: ThemeTypography;
  readonly layout: ThemeLayout;
  readonly shape: ThemeShape;
  readonly created_at: string;
  readonly updated_at: string;
}

export type ThemeSchemaDocument = typeof schema;

export const THEME_SCHEMA_DOCUMENT: ThemeSchemaDocument = schema;

export interface PuckThemeField {
  readonly type: "select";
  readonly label: string;
  readonly options: readonly string[];
}

export interface PuckThemeGroupConfig {
  readonly label: string;
  readonly fields: Readonly<Record<string, PuckThemeField>>;
}

/** Build Puck controls from the product-owned theme schema, never literals. */
export function generatePuckThemeConfig(): Readonly<
  Record<string, PuckThemeGroupConfig>
> {
  return Object.fromEntries(
    schema.groups.map((group) => [
      group.name,
      {
        label: group.name,
        fields: Object.fromEntries(
          group.tokens.map((token) => [
            token.name,
            {
              type: "select" as const,
              label: `${token.name} (${token.accessibility_class})`,
              options: token.values,
            },
          ]),
        ),
      },
    ]),
  );
}

export const THEME_DEFAULTS: Omit<
  ThemeRecord,
  "id" | "site_id" | "created_at" | "updated_at"
> = {
  schema_version: THEME_SCHEMA_VERSION,
  renderer_version: THEME_RENDERER_VERSION,
  row_version: 1,
  palette: { preset: "ocean" },
  typography: { family: "system", scale: "balanced", weight: "regular" },
  layout: { content_width: "md", spacing: "md", grid_gap: "md" },
  shape: { radius: "md", shadow: "sm" },
};

export function isThemeRecord(value: unknown): value is ThemeRecord {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  return (
    typeof record.id === "string" &&
    typeof record.site_id === "string" &&
    record.schema_version === THEME_SCHEMA_VERSION &&
    record.renderer_version === THEME_RENDERER_VERSION &&
    typeof record.row_version === "number" &&
    record.row_version > 0 &&
    typeof record.palette === "object" &&
    typeof record.typography === "object" &&
    typeof record.layout === "object" &&
    typeof record.shape === "object"
  );
}
