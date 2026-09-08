/**
 * Trusted component catalog for SLAIF Agent-Site.
 *
 * Architecture reference: ARCHITECTURE-for-agents.md §7 (normalized
 * composition, component catalog). Components are code-defined; agents and
 * users can only instantiate/configure them. No executable code is ever
 * accepted from editorial input.
 */

export interface ComponentDefinition {
  readonly type: string;
  readonly category: "layout" | "basic" | "data" | "institutional" | "global";
  readonly schemaVersion: string;
  readonly allowedSlots: readonly string[];
  readonly maxChildren: number;
  readonly propsSchema: Record<string, PropDefinition>;
  readonly bindingKind: "none" | "collection_view" | "media_asset";
  readonly authorityClass: "content" | "structure" | "global";
}

interface ComponentDefinitionBase {
  readonly type: string;
  readonly category: "layout" | "basic" | "data" | "institutional" | "global";
  readonly schemaVersion: string;
  readonly allowedSlots: readonly string[];
  readonly maxChildren: number;
  readonly propsSchema: Record<string, PropDefinition>;
}

export interface PropDefinition {
  readonly type:
    "string" | "number" | "boolean" | "enum" | "reference" | "object" | "array";
  readonly required: boolean;
  readonly enumValues?: readonly string[];
  readonly bounded?: { min?: number; max?: number };
  readonly localized?: boolean;
  readonly authority?: "content" | "design";
}

const LAYOUT_COMPONENTS: readonly ComponentDefinitionBase[] = [
  {
    type: "Section",
    category: "layout",
    schemaVersion: "1",
    allowedSlots: ["default"],
    maxChildren: 32,
    propsSchema: {
      variant: {
        type: "enum",
        required: false,
        enumValues: ["default", "full", "narrow"],
      },
      background: { type: "string", required: false },
    },
  },
  {
    type: "Container",
    category: "layout",
    schemaVersion: "1",
    allowedSlots: ["default"],
    maxChildren: 16,
    propsSchema: {
      width: { type: "enum", required: false, enumValues: ["sm", "md", "lg", "xl"] },
    },
  },
  {
    type: "Columns",
    category: "layout",
    schemaVersion: "1",
    allowedSlots: ["col-1", "col-2", "col-3", "col-4"],
    maxChildren: 4,
    propsSchema: {
      count: { type: "number", required: true, bounded: { min: 1, max: 4 } },
      gap: { type: "enum", required: false, enumValues: ["none", "sm", "md", "lg"] },
    },
  },
  {
    type: "Grid",
    category: "layout",
    schemaVersion: "1",
    allowedSlots: ["default"],
    maxChildren: 24,
    propsSchema: {
      columns: { type: "number", required: false, bounded: { min: 1, max: 12 } },
      gap: { type: "enum", required: false, enumValues: ["sm", "md", "lg"] },
    },
  },
  {
    type: "Stack",
    category: "layout",
    schemaVersion: "1",
    allowedSlots: ["default"],
    maxChildren: 16,
    propsSchema: {
      direction: {
        type: "enum",
        required: false,
        enumValues: ["vertical", "horizontal"],
      },
      gap: { type: "enum", required: false, enumValues: ["none", "sm", "md", "lg"] },
    },
  },
  {
    type: "Spacer",
    category: "layout",
    schemaVersion: "1",
    allowedSlots: [],
    maxChildren: 0,
    propsSchema: {
      size: {
        type: "enum",
        required: true,
        enumValues: ["xs", "sm", "md", "lg", "xl"],
      },
    },
  },
];

const BASIC_COMPONENTS: readonly ComponentDefinitionBase[] = [
  {
    type: "Heading",
    category: "basic",
    schemaVersion: "1",
    allowedSlots: [],
    maxChildren: 0,
    propsSchema: {
      text: { type: "string", required: true, localized: true },
      level: { type: "number", required: true, bounded: { min: 1, max: 6 } },
    },
  },
  {
    type: "RichText",
    category: "basic",
    schemaVersion: "1",
    allowedSlots: [],
    maxChildren: 0,
    propsSchema: {
      content: { type: "object", required: true, localized: true },
    },
  },
  {
    type: "Image",
    category: "basic",
    schemaVersion: "1",
    allowedSlots: [],
    maxChildren: 0,
    propsSchema: {
      mediaId: { type: "reference", required: true },
      alt: { type: "string", required: true, localized: true },
      aspectRatio: {
        type: "enum",
        required: false,
        enumValues: ["auto", "16:9", "4:3", "1:1"],
      },
    },
  },
  {
    type: "Button",
    category: "basic",
    schemaVersion: "1",
    allowedSlots: [],
    maxChildren: 0,
    propsSchema: {
      label: { type: "string", required: true, localized: true },
      href: { type: "string", required: true },
      variant: {
        type: "enum",
        required: false,
        enumValues: ["primary", "secondary", "ghost"],
      },
    },
  },
  {
    type: "Quote",
    category: "basic",
    schemaVersion: "1",
    allowedSlots: [],
    maxChildren: 0,
    propsSchema: {
      text: { type: "string", required: true, localized: true },
      attribution: { type: "string", required: false, localized: true },
    },
  },
];

const DATA_COMPONENTS: readonly ComponentDefinitionBase[] = [
  {
    type: "CollectionList",
    category: "data",
    schemaVersion: "1",
    allowedSlots: ["item"],
    maxChildren: 0,
    propsSchema: {
      viewId: { type: "reference", required: true },
      limit: { type: "number", required: false, bounded: { min: 1, max: 100 } },
    },
  },
  {
    type: "CollectionGrid",
    category: "data",
    schemaVersion: "1",
    allowedSlots: ["item"],
    maxChildren: 0,
    propsSchema: {
      viewId: { type: "reference", required: true },
      columns: { type: "number", required: false, bounded: { min: 1, max: 6 } },
    },
  },
  {
    type: "CollectionDetail",
    category: "data",
    schemaVersion: "1",
    allowedSlots: [],
    maxChildren: 0,
    propsSchema: {
      viewId: { type: "reference", required: true },
    },
  },
];

const INSTITUTIONAL_COMPONENTS: readonly ComponentDefinitionBase[] = [
  {
    type: "Hero",
    category: "institutional",
    schemaVersion: "1",
    allowedSlots: ["content"],
    maxChildren: 8,
    propsSchema: {
      heading: { type: "string", required: true, localized: true },
      subheading: { type: "string", required: false, localized: true },
      mediaId: { type: "reference", required: false },
    },
  },
  {
    type: "Statistics",
    category: "institutional",
    schemaVersion: "1",
    allowedSlots: [],
    maxChildren: 0,
    propsSchema: {
      items: { type: "array", required: true },
    },
  },
  {
    type: "Timeline",
    category: "institutional",
    schemaVersion: "1",
    allowedSlots: [],
    maxChildren: 0,
    propsSchema: {
      items: { type: "array", required: true },
    },
  },
  {
    type: "FAQ",
    category: "institutional",
    schemaVersion: "1",
    allowedSlots: [],
    maxChildren: 0,
    propsSchema: {
      items: { type: "array", required: true },
    },
  },
];

const GLOBAL_COMPONENTS: readonly ComponentDefinitionBase[] = [
  {
    type: "Header",
    category: "global",
    schemaVersion: "1",
    allowedSlots: ["nav"],
    maxChildren: 12,
    propsSchema: {},
  },
  {
    type: "Footer",
    category: "global",
    schemaVersion: "1",
    allowedSlots: ["links"],
    maxChildren: 16,
    propsSchema: {},
  },
  {
    type: "Breadcrumbs",
    category: "global",
    schemaVersion: "1",
    allowedSlots: [],
    maxChildren: 0,
    propsSchema: {},
  },
  {
    type: "LanguageSwitcher",
    category: "global",
    schemaVersion: "1",
    allowedSlots: [],
    maxChildren: 0,
    propsSchema: {},
  },
];

export const COMPONENT_CATALOG_VERSION = "catalog-v1";

export const COMPOSITION_SCHEMA_VERSION = "site-composition/v1";

const COLLECTION_VIEW_COMPONENTS = new Set([
  "CollectionList",
  "CollectionGrid",
  "CollectionDetail",
]);
const MEDIA_COMPONENTS = new Set(["Image", "Hero"]);

function enrichComponent(component: ComponentDefinitionBase): ComponentDefinition {
  const authorityClass =
    component.category === "global"
      ? "global"
      : component.category === "layout"
        ? "structure"
        : "content";
  const propsSchema = Object.fromEntries(
    Object.entries(component.propsSchema).map(([key, prop]) => [
      key,
      {
        ...prop,
        authority: component.category === "layout" ? "design" : "content",
      },
    ]),
  ) as Record<string, PropDefinition>;
  return {
    ...component,
    propsSchema,
    bindingKind: COLLECTION_VIEW_COMPONENTS.has(component.type)
      ? "collection_view"
      : MEDIA_COMPONENTS.has(component.type)
        ? "media_asset"
        : "none",
    authorityClass,
  };
}

export const COMPONENT_CATALOG: readonly ComponentDefinition[] = [
  ...LAYOUT_COMPONENTS,
  ...BASIC_COMPONENTS,
  ...DATA_COMPONENTS,
  ...INSTITUTIONAL_COMPONENTS,
  ...GLOBAL_COMPONENTS,
].map(enrichComponent);

export const COMPONENT_TYPES: ReadonlySet<string> = new Set(
  COMPONENT_CATALOG.map((c) => c.type),
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
  return COMPONENT_CATALOG.find((c) => c.type === type);
}

export function validateComponentType(type: string): boolean {
  return COMPONENT_TYPES.has(type);
}

export const COMPONENT_CATALOG_DOCUMENT = {
  version: COMPONENT_CATALOG_VERSION,
  composition_schema_version: COMPOSITION_SCHEMA_VERSION,
  components: COMPONENT_CATALOG.map((component) => ({
    type: component.type,
    category: component.category,
    schema_version: component.schemaVersion,
    allowed_slots: [...component.allowedSlots],
    max_children: component.maxChildren,
    binding_kind: component.bindingKind,
    authority_class: component.authorityClass,
    props: Object.fromEntries(
      Object.entries(component.propsSchema).map(([key, prop]) => [
        key,
        {
          type: prop.type,
          required: prop.required,
          enum_values: [...(prop.enumValues ?? [])],
          minimum: prop.bounded?.min ?? null,
          maximum: prop.bounded?.max ?? null,
          localized: prop.localized ?? false,
          authority: prop.authority ?? "content",
        },
      ]),
    ),
  })),
} as const;
