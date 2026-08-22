/**
 * Puck adapter: maps between the normalized composition tree and Puck's
 * editor data format. Puck is used only as a visual editing UX layer.
 */

const CATALOG_TYPES = [
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

interface PuckNode {
  type: string;
  props: Record<string, unknown>;
}

export interface PuckData {
  content: PuckNode[];
  root: Record<string, unknown>;
}

export function generatePuckConfig(): Record<string, PuckComponentConfig> {
  const config: Record<string, PuckComponentConfig> = {};
  for (const component_type of CATALOG_TYPES) {
    config[component_type] = {
      type: component_type,
      label: component_type,
      fields: {},
    };
  }
  return config;
}

export function compositionToPuck(
  nodes: readonly {
    id: string;
    componentType: string;
    props: Record<string, unknown>;
  }[],
): PuckData {
  return {
    content: nodes.map((n) => ({
      type: n.componentType,
      props: { ...n.props, id: n.id },
    })),
    root: { locale: "en" },
  };
}

export function puckToComposition(
  data: PuckData,
): readonly { id: string; componentType: string; props: Record<string, unknown> }[] {
  return data.content.map((node) => ({
    id: typeof node.props.id === "string" ? node.props.id : crypto.randomUUID(),
    componentType: node.type,
    props: node.props,
  }));
}
