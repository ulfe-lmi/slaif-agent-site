/** Generated catalog-v1 authority; edit catalog-v1.json instead. */
import catalog from "./catalog-v1.json" with { type: "json" };
const catalogDocument = catalog;
export const COMPONENT_CATALOG_VERSION = "catalog-v1";
export const COMPOSITION_SCHEMA_VERSION = "site-composition/v1";
function propSchema(value) {
    const properties = value.properties;
    return {
        type: value.type,
        ...(value.required === undefined ? {} : { required: value.required }),
        ...(value.enum_values === undefined ? {} : { enum_values: value.enum_values }),
        ...(value.minimum === undefined ? {} : { minimum: value.minimum }),
        ...(value.maximum === undefined ? {} : { maximum: value.maximum }),
        ...(value.min_items === undefined ? {} : { min_items: value.min_items }),
        ...(value.max_items === undefined ? {} : { max_items: value.max_items }),
        ...(value.max_length === undefined ? {} : { max_length: value.max_length }),
        ...(value.format === undefined ? {} : { format: value.format }),
        ...(value.additional_properties === undefined ? {} : { additional_properties: value.additional_properties }),
        ...(value.items === undefined ? {} : { items: propSchema(value.items) }),
        ...(properties === undefined ? {} : { properties: Object.fromEntries(Object.entries(properties).map(([key, item]) => [key, propSchema(item)])) }),
    };
}
export const COMPONENT_CATALOG = catalogDocument.components.map((component) => ({
    type: component.type,
    category: component.category,
    schemaVersion: component.schema_version,
    allowedSlots: component.allowed_slots,
    maxChildren: component.max_children,
    bindingKind: component.binding_kind,
    authorityClass: component.authority_class,
    propsSchema: Object.fromEntries(Object.entries(component.props).map(([key, prop]) => [key, {
            type: prop.type,
            required: prop.required,
            ...((prop.enum_values ?? []).length === 0 ? {} : { enumValues: prop.enum_values }),
            ...((prop.minimum === null && prop.maximum === null) ? {} : { bounded: { min: prop.minimum ?? undefined, max: prop.maximum ?? undefined } }),
            ...(prop.localized ? { localized: true } : {}),
            authority: prop.authority,
            ...(prop.schema === undefined ? {} : { schema: propSchema(prop.schema) }),
        }])),
}));
export const COMPONENT_TYPES = new Set(COMPONENT_CATALOG.map((component) => component.type));
export const FORBIDDEN_PROP_KEYS = new Set([
    "__proto__", "constructor", "prototype", "innerhtml", "dangerouslysetinnerhtml",
    "style", "class", "classname", "onclick", "onload", "handler", "script", "eval",
    "html", "template", "query", "code", "package", "callback",
]);
export function getComponent(type) {
    return COMPONENT_CATALOG.find((component) => component.type === type);
}
export function validateComponentType(type) {
    return COMPONENT_TYPES.has(type);
}
export const COMPONENT_CATALOG_DOCUMENT = catalogDocument;
