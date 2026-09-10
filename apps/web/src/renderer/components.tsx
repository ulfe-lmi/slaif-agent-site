/** One pure trusted renderer shared by Puck, public SSR, and workspace preview. */

import { createElement, type ReactElement, type ReactNode } from "react";
import {
  isResponsiveValue,
  RESPONSIVE_LABELS,
  type ComponentDefinition,
} from "@slaif-agent-site/component-catalog";
import type { ThemeRecord } from "@slaif-agent-site/composition-schema";
import type { PageProjection, ProjectionNode } from "../sites/render";
import { RENDERER_STYLESHEET } from "./styles";

interface RenderProps {
  readonly definition: ComponentDefinition;
  readonly props: Record<string, unknown>;
  readonly children?: ReactNode;
  readonly locale: string;
  readonly data?: readonly Record<string, unknown>[];
}

const CLASS_VALUES = new Set([
  "default",
  "full",
  "narrow",
  "sm",
  "md",
  "lg",
  "xl",
  "none",
  "primary",
  "secondary",
  "ghost",
  "vertical",
  "horizontal",
]);

function classValue(value: unknown, fallback: string): string {
  return typeof value === "string" && CLASS_VALUES.has(value) ? value : fallback;
}

function numberValue(
  value: unknown,
  minimum: number,
  maximum: number,
  fallback: number,
) {
  return typeof value === "number" &&
    Number.isInteger(value) &&
    value >= minimum &&
    value <= maximum
    ? value
    : fallback;
}

function designClasses(
  value: unknown,
  prefix: string,
  fallback: string,
  normalize: (value: unknown) => string | number,
): string {
  if (isResponsiveValue(value)) {
    const labels = RESPONSIVE_LABELS.filter((label) => value[label] !== undefined);
    if (labels.length > 0) {
      const first = labels[0]!;
      const classes = [
        `${prefix}--${normalize(value[first])}`,
        ...labels
          .slice(1)
          .map((label) => `${prefix}--${label}-${normalize(value[label])}`),
      ];
      if (value.mobile === undefined) {
        const mobileFallback = value.tablet ?? value.desktop;
        if (mobileFallback !== undefined) {
          classes.push(`${prefix}--mobile-${normalize(mobileFallback)}`);
        }
      }
      return classes.join(" ");
    }
  }
  return `${prefix}--${normalize(value) || fallback}`;
}

function alignment(value: unknown): string {
  return typeof value === "string" &&
    ["start", "center", "end", "stretch"].includes(value)
    ? value
    : "stretch";
}

function token(value: unknown, allowed: Set<string>, fallback: string): string {
  return typeof value === "string" && allowed.has(value) ? value : fallback;
}

function themeGroup(theme: ThemeRecord, name: string): Record<string, unknown> {
  const value = (theme as unknown as Record<string, unknown>)[name];
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function themeClasses(theme: ThemeRecord): string {
  const palette = themeGroup(theme, "palette");
  const typography = themeGroup(theme, "typography");
  const layout = themeGroup(theme, "layout");
  const shape = themeGroup(theme, "shape");
  return [
    `renderer-theme-palette--${token(palette.preset, new Set(["ocean", "meadow", "ember"]), "ocean")}`,
    `renderer-theme-family--${token(typography.family, new Set(["system", "serif", "mono"]), "system")}`,
    `renderer-theme-scale--${token(typography.scale, new Set(["compact", "balanced", "spacious"]), "balanced")}`,
    `renderer-theme-weight--${token(typography.weight, new Set(["regular", "medium", "bold"]), "regular")}`,
    `renderer-theme-width--${token(layout.content_width, new Set(["sm", "md", "lg", "xl"]), "md")}`,
    `renderer-theme-spacing--${token(layout.spacing, new Set(["sm", "md", "lg"]), "md")}`,
    `renderer-theme-gap--${token(layout.grid_gap, new Set(["sm", "md", "lg"]), "md")}`,
    `renderer-theme-radius--${token(shape.radius, new Set(["none", "sm", "md", "lg", "full"]), "md")}`,
    `renderer-theme-shadow--${token(shape.shadow, new Set(["none", "sm", "md", "lg"]), "sm")}`,
  ].join(" ");
}

const GAP_VALUES = new Set(["none", "sm", "md", "lg"]);
const WIDTH_VALUES = new Set(["sm", "md", "lg", "xl"]);
const DIRECTION_VALUES = new Set(["vertical", "horizontal"]);
const SIZE_VALUES = new Set(["xs", "sm", "md", "lg", "xl"]);
const ASPECT_RATIO_VALUES = new Set(["auto", "16:9", "4:3", "1:1"]);

function text(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function safeHref(value: unknown): string {
  if (typeof value !== "string" || !value || value.startsWith("//")) return "/";
  return value.startsWith("/") ? value : "/";
}

function aspectRatioClass(value: unknown): string {
  return token(value, ASPECT_RATIO_VALUES, "auto").replace(":", "-");
}

function Section({ props, children }: RenderProps) {
  return (
    <section
      className={`renderer-section ${designClasses(props.variant, "renderer-section", "default", (value) => token(value, new Set(["default", "full", "narrow"]), "default"))} ${designClasses(props.alignment, "renderer-align", "stretch", alignment)}`}
    >
      {children}
    </section>
  );
}
function Container({ props, children }: RenderProps) {
  return (
    <div
      className={`renderer-container ${designClasses(props.width, "renderer-container", "md", (value) => token(value, WIDTH_VALUES, "md"))} ${designClasses(props.alignment, "renderer-align", "stretch", alignment)}`}
    >
      {children}
    </div>
  );
}
function Columns({ props, children }: RenderProps) {
  return (
    <div
      className={`renderer-columns ${designClasses(props.count, "renderer-columns", "2", (value) => numberValue(value, 1, 4, 2))} ${designClasses(props.gap, "renderer-gap", "md", (value) => token(value, GAP_VALUES, "md"))} ${designClasses(props.alignment, "renderer-align", "stretch", alignment)}`}
    >
      {children}
    </div>
  );
}
function Grid({ props, children }: RenderProps) {
  return (
    <div
      className={`renderer-grid ${designClasses(props.columns, "renderer-grid", "1", (value) => numberValue(value, 1, 12, 1))} ${designClasses(props.gap, "renderer-gap", "md", (value) => token(value, GAP_VALUES, "md"))} ${designClasses(props.alignment, "renderer-align", "stretch", alignment)}`}
    >
      {children}
    </div>
  );
}
function Stack({ props, children }: RenderProps) {
  return (
    <div
      className={`renderer-stack ${designClasses(props.direction, "renderer-stack", "vertical", (value) => token(value, DIRECTION_VALUES, "vertical"))} ${designClasses(props.gap, "renderer-stack-gap", "md", (value) => token(value, GAP_VALUES, "md"))} ${designClasses(props.alignment, "renderer-align", "stretch", alignment)}`}
    >
      {children}
    </div>
  );
}
function Spacer({ props }: RenderProps) {
  return (
    <div
      aria-hidden="true"
      className={`renderer-spacer ${designClasses(props.size, "renderer-spacer", "md", (value) => token(value, SIZE_VALUES, "md"))}`}
    />
  );
}
function Heading({ props }: RenderProps) {
  const level =
    typeof props.level === "number" && props.level >= 1 && props.level <= 6
      ? Math.trunc(props.level)
      : 2;
  return createElement(
    `h${level}`,
    {
      className: `renderer-heading ${designClasses(props.alignment, "renderer-align", "start", alignment)}`,
    },
    text(props.text),
  );
}

function RichText({ props }: RenderProps) {
  const value = props.content;
  if (typeof value === "string") return <p className="renderer-richtext">{value}</p>;
  const blocks = Array.isArray(value)
    ? value
    : typeof value === "object" && value !== null
      ? [value]
      : [];
  return (
    <div className="renderer-richtext">
      {blocks.map((block, index) => {
        if (typeof block === "string") return <p key={index}>{block}</p>;
        if (typeof block !== "object" || block === null)
          throw new Error("invalid rich text");
        const record = block as Record<string, unknown>;
        const children = Array.isArray(record.children) ? record.children : [];
        const content = children.map((child, childIndex) => {
          if (typeof child === "string") return <span key={childIndex}>{child}</span>;
          if (typeof child !== "object" || child === null)
            throw new Error("invalid rich text child");
          const leaf = child as Record<string, unknown>;
          const node = <span key={childIndex}>{text(leaf.text)}</span>;
          if (leaf.bold === true) return <strong key={childIndex}>{node}</strong>;
          if (leaf.italic === true) return <em key={childIndex}>{node}</em>;
          return node;
        });
        if (record.type === "heading") return <h3 key={index}>{content}</h3>;
        if (record.type === "quote")
          return <blockquote key={index}>{content}</blockquote>;
        if (record.type === "paragraph" || record.type === undefined)
          return <p key={index}>{content}</p>;
        throw new Error("unknown rich text block");
      })}
    </div>
  );
}

function Image({ props }: RenderProps) {
  const mediaId = text(props.mediaId);
  if (!mediaId || !/^[0-9a-f-]{36}$/i.test(mediaId))
    throw new Error("invalid media reference");
  return (
    <div
      aria-label={text(props.alt)}
      className={`renderer-image-placeholder ${designClasses(props.aspectRatio, "renderer-image-placeholder", "auto", aspectRatioClass)}`}
      role="img"
    />
  );
}
function Button({ props }: RenderProps) {
  return (
    <a
      className={`renderer-button ${designClasses(props.variant, "renderer-button", "primary", (value) => classValue(value, "primary"))}`}
      href={safeHref(props.href)}
    >
      {text(props.label)}
    </a>
  );
}
function Quote({ props }: RenderProps) {
  return (
    <blockquote className="renderer-quote">
      <p>{text(props.text)}</p>
      {props.attribution ? <cite>{text(props.attribution)}</cite> : null}
    </blockquote>
  );
}
function Hero({ props, children }: RenderProps) {
  return (
    <section className="renderer-hero">
      <h2>{text(props.heading)}</h2>
      {props.subheading ? <p>{text(props.subheading)}</p> : null}
      {children}
    </section>
  );
}
function Header({ children }: RenderProps) {
  return <header className="renderer-header">{children}</header>;
}
function Footer({ children }: RenderProps) {
  return <footer className="renderer-footer">{children}</footer>;
}
function Breadcrumbs({ props }: RenderProps) {
  return (
    <nav aria-label="Breadcrumb" className="renderer-breadcrumbs">
      <ol>
        {(Array.isArray(props.items) ? props.items : []).map((item, index) => (
          <li key={index}>{text(item)}</li>
        ))}
      </ol>
    </nav>
  );
}
function LanguageSwitcher({ props, locale }: RenderProps) {
  return (
    <nav aria-label="Language" className="renderer-language">
      {(Array.isArray(props.locales) ? props.locales : [locale]).map((item, index) => (
        <span key={index}>{text(item)}</span>
      ))}
    </nav>
  );
}

function Collection({
  props,
  data,
  mode,
}: RenderProps & { readonly mode: "list" | "grid" | "detail" }) {
  const items =
    data ??
    (Array.isArray(props.items)
      ? props.items.filter(
          (item): item is Record<string, unknown> =>
            typeof item === "object" && item !== null,
        )
      : []);
  if (mode === "detail") {
    const item = items[0];
    const values =
      item && typeof item.values === "object" && item.values !== null
        ? (item.values as Record<string, unknown>)
        : {};
    return (
      <article className="renderer-collection-detail">
        {item ? (
          <>
            <h2>{text(values.title ?? item.slug)}</h2>
            <p>{text(values.summary ?? values.description)}</p>
          </>
        ) : null}
      </article>
    );
  }
  const gridClasses =
    mode === "grid"
      ? designClasses(props.columns, "renderer-collection-grid", "3", (value) =>
          numberValue(value, 1, 6, 3),
        )
      : "";
  return (
    <div
      className={`renderer-collection renderer-collection--${mode}${gridClasses ? ` ${gridClasses}` : ""}`}
    >
      {items.map((item, index) => (
        <article key={text(item.id) || index}>
          {(() => {
            const values =
              typeof item.values === "object" && item.values !== null
                ? (item.values as Record<string, unknown>)
                : {};
            return (
              <>
                <h2>{text(values.title ?? item.slug)}</h2>
                <p>{text(values.summary ?? values.description)}</p>
              </>
            );
          })()}
        </article>
      ))}
    </div>
  );
}
function Statistics({ props }: RenderProps) {
  const items = Array.isArray(props.items) ? props.items : [];
  return (
    <dl className="renderer-statistics">
      {items.map((item, index) => {
        const value =
          typeof item === "object" && item !== null
            ? (item as Record<string, unknown>)
            : {};
        return (
          <div key={index}>
            <dt>{text(value.label)}</dt>
            <dd>{text(value.value)}</dd>
          </div>
        );
      })}
    </dl>
  );
}
function Timeline({ props }: RenderProps) {
  const items = Array.isArray(props.items) ? props.items : [];
  return (
    <ol className="renderer-timeline">
      {items.map((item, index) => {
        const value =
          typeof item === "object" && item !== null
            ? (item as Record<string, unknown>)
            : {};
        return (
          <li key={index}>
            <h2>{text(value.title)}</h2>
            <p>{text(value.description)}</p>
          </li>
        );
      })}
    </ol>
  );
}
function FAQ({ props }: RenderProps) {
  const items = Array.isArray(props.items) ? props.items : [];
  return (
    <section className="renderer-faq">
      {items.map((item, index) => {
        const value =
          typeof item === "object" && item !== null
            ? (item as Record<string, unknown>)
            : {};
        return (
          <details key={index}>
            <summary>{text(value.question)}</summary>
            <p>{text(value.answer)}</p>
          </details>
        );
      })}
    </section>
  );
}

const RENDERERS: Record<string, (props: RenderProps) => ReactElement> = {
  Section,
  Container,
  Columns,
  Grid,
  Stack,
  Spacer,
  Heading,
  RichText,
  Image,
  Button,
  Quote,
  Hero,
  Statistics,
  Timeline,
  FAQ,
  Header,
  Footer,
  Breadcrumbs,
  LanguageSwitcher,
  CollectionList: (props) => <Collection {...props} mode="list" />,
  CollectionGrid: (props) => <Collection {...props} mode="grid" />,
  CollectionDetail: (props) => <Collection {...props} mode="detail" />,
};

const FALLBACK_DEFINITION: ComponentDefinition = {
  type: "trusted",
  category: "basic",
  schemaVersion: "1",
  allowedSlots: [],
  maxChildren: 0,
  propsSchema: {},
  bindingKind: "none",
  authorityClass: "content",
};

export function renderComponent(
  node: { componentType: string; props: Record<string, unknown>; children?: ReactNode },
  locale: string,
  data?: readonly Record<string, unknown>[],
): ReactElement {
  const renderer = RENDERERS[node.componentType];
  if (!renderer) throw new Error("unknown trusted component");
  return renderer({
    definition: FALLBACK_DEFINITION,
    props: node.props,
    children: node.children,
    locale,
    ...(data === undefined ? {} : { data }),
  });
}

function renderNode(
  node: ProjectionNode,
  locale: string,
  bindings: PageProjection["bindings"],
): ReactElement {
  const children = node.children.map((child) => renderNode(child, locale, bindings));
  return (
    <div data-component={node.component_type}>
      {renderComponent(
        { componentType: node.component_type, props: node.props, children },
        locale,
        bindings[node.id],
      )}
    </div>
  );
}

export function renderProjection(projection: PageProjection): ReactElement {
  return (
    <>
      <link rel="stylesheet" href={RENDERER_STYLESHEET} />
      <main
        className={`renderer-surface ${themeClasses(projection.theme)}`}
        lang={projection.locale}
        data-render-mode={projection.render_mode}
        aria-labelledby="page-title"
      >
        <h1 id="page-title">{projection.page.title}</h1>
        {projection.composition.nodes.map((node) =>
          renderNode(node, projection.locale, projection.bindings),
        )}
      </main>
    </>
  );
}
