/** Generated catalog-v1 authority; edit catalog-v1.json instead. */

import catalog from "./catalog-v1.json" with { type: "json" };

export interface PropSchema {
  readonly type:
    "string" | "number" | "boolean" | "enum" | "reference" | "object" | "array";
  readonly required?: boolean | readonly string[];
  readonly enum_values?: readonly string[];
  readonly minimum?: number | null;
  readonly maximum?: number | null;
  readonly min_items?: number;
  readonly max_items?: number;
  readonly max_length?: number;
  readonly format?: "uuid";
  readonly properties?: Readonly<Record<string, PropSchema>>;
  readonly required_keys?: readonly string[];
  readonly additional_properties?: boolean;
  readonly items?: PropSchema;
}

export interface PropDefinition {
  readonly type: PropSchema["type"];
  readonly required: boolean;
  readonly enumValues?: readonly string[];
  readonly bounded?: { readonly min?: number; readonly max?: number };
  readonly localized?: boolean;
  readonly authority: "content" | "design";
  readonly schema?: PropSchema;
}

export interface ComponentDefinition {
  readonly type: string;
  readonly category: "layout" | "basic" | "data" | "institutional" | "global";
  readonly schemaVersion: string;
  readonly allowedSlots: readonly string[];
  readonly maxChildren: number;
  readonly propsSchema: Readonly<Record<string, PropDefinition>>;
  readonly bindingKind: "none" | "collection_view" | "media_asset";
  readonly authorityClass: "content" | "structure" | "global";
}

interface CatalogPropInput {
  readonly type: PropSchema["type"];
  readonly required: boolean;
  readonly enum_values?: readonly string[];
  readonly minimum?: number | null;
  readonly maximum?: number | null;
  readonly localized?: boolean;
  readonly authority: "content" | "design";
  readonly schema?: Record<string, unknown>;
}

interface CatalogComponentInput {
  readonly type: string;
  readonly category: ComponentDefinition["category"];
  readonly schema_version: string;
  readonly allowed_slots: readonly string[];
  readonly max_children: number;
  readonly props: Readonly<Record<string, CatalogPropInput>>;
  readonly binding_kind: ComponentDefinition["bindingKind"];
  readonly authority_class: ComponentDefinition["authorityClass"];
}

interface CatalogDocumentInput {
  readonly version: string;
  readonly composition_schema_version: string;
  readonly components: readonly CatalogComponentInput[];
}

const catalogDocument = catalog as unknown as CatalogDocumentInput;

export const COMPONENT_CATALOG_VERSION = "catalog-v1" as const;
export const COMPOSITION_SCHEMA_VERSION = "site-composition/v1" as const;

function propSchema(value: Record<string, unknown>): PropSchema {
  const properties = value.properties as
    Record<string, Record<string, unknown>> | undefined;
  return {
    type: value.type as PropSchema["type"],
    ...(value.required === undefined
      ? {}
      : { required: value.required as boolean | readonly string[] }),
    ...(value.enum_values === undefined
      ? {}
      : { enum_values: value.enum_values as readonly string[] }),
    ...(value.minimum === undefined ? {} : { minimum: value.minimum as number | null }),
    ...(value.maximum === undefined ? {} : { maximum: value.maximum as number | null }),
    ...(value.min_items === undefined ? {} : { min_items: value.min_items as number }),
    ...(value.max_items === undefined ? {} : { max_items: value.max_items as number }),
    ...(value.max_length === undefined
      ? {}
      : { max_length: value.max_length as number }),
    ...(value.format === undefined ? {} : { format: value.format as "uuid" }),
    ...(value.additional_properties === undefined
      ? {}
      : { additional_properties: value.additional_properties as boolean }),
    ...(value.items === undefined
      ? {}
      : { items: propSchema(value.items as Record<string, unknown>) }),
    ...(properties === undefined
      ? {}
      : {
          properties: Object.fromEntries(
            Object.entries(properties).map(([key, item]) => [key, propSchema(item)]),
          ),
        }),
  };
}

export const COMPONENT_CATALOG: readonly ComponentDefinition[] =
  catalogDocument.components.map((component) => ({
    type: component.type,
    category: component.category,
    schemaVersion: component.schema_version,
    allowedSlots: component.allowed_slots,
    maxChildren: component.max_children,
    bindingKind: component.binding_kind,
    authorityClass: component.authority_class,
    propsSchema: Object.fromEntries(
      Object.entries(component.props).map(([key, prop]) => [
        key,
        {
          type: prop.type,
          required: prop.required,
          ...((prop.enum_values ?? []).length === 0
            ? {}
            : { enumValues: prop.enum_values }),
          ...(prop.minimum === null && prop.maximum === null
            ? {}
            : {
                bounded: {
                  min: prop.minimum ?? undefined,
                  max: prop.maximum ?? undefined,
                },
              }),
          ...(prop.localized ? { localized: true } : {}),
          authority: prop.authority,
          ...(prop.schema === undefined ? {} : { schema: propSchema(prop.schema) }),
        },
      ]),
    ),
  })) as unknown as readonly ComponentDefinition[];

export const COMPONENT_TYPES: ReadonlySet<string> = new Set(
  COMPONENT_CATALOG.map((component) => component.type),
);
export const FORBIDDEN_PROP_KEYS: ReadonlySet<string> = new Set([
  "__proto__",
  "constructor",
  "prototype",
  "innerhtml",
  "dangerouslysetinnerhtml",
  "style",
  "class",
  "classname",
  "onclick",
  "onload",
  "handler",
  "script",
  "eval",
  "html",
  "template",
  "query",
  "code",
  "package",
  "callback",
]);

export function getComponent(type: string): ComponentDefinition | undefined {
  return COMPONENT_CATALOG.find((component) => component.type === type);
}

export function validateComponentType(type: string): boolean {
  return COMPONENT_TYPES.has(type);
}

export const COMPONENT_CATALOG_DOCUMENT = catalogDocument;
export * from "./design-system";
