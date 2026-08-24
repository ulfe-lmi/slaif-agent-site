/** One pure trusted renderer shared by Puck, public SSR, and workspace preview. */

import { createElement, type ReactElement, type ReactNode } from "react";
import type { ComponentDefinition } from "@slaif-agent-site/component-catalog";
import type { PageProjection, ProjectionNode } from "../sites/render";

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

function text(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function safeHref(value: unknown): string {
  if (typeof value !== "string" || !value || value.startsWith("//")) return "/";
  if (value.startsWith("/")) return value;
  try {
    const parsed = new URL(value);
    return parsed.protocol === "https:" ? parsed.toString() : "/";
  } catch {
    return "/";
  }
}

function Section({ props, children }: RenderProps) {
  return (
    <section
      className={`renderer-section renderer-section--${classValue(props.variant, "default")}`}
    >
      {children}
    </section>
  );
}
function Container({ props, children }: RenderProps) {
  return (
    <div
      className={`renderer-container renderer-container--${classValue(props.width, "md")}`}
    >
      {children}
    </div>
  );
}
function Columns({ props, children }: RenderProps) {
  const count =
    typeof props.count === "number" && props.count >= 1 && props.count <= 4
      ? props.count
      : 2;
  return (
    <div className={`renderer-columns renderer-columns--${count}`}>{children}</div>
  );
}
function Grid({ props, children }: RenderProps) {
  const columns =
    typeof props.columns === "number" && props.columns >= 1 && props.columns <= 12
      ? props.columns
      : 1;
  return <div className={`renderer-grid renderer-grid--${columns}`}>{children}</div>;
}
function Stack({ props, children }: RenderProps) {
  return (
    <div
      className={`renderer-stack renderer-stack--${classValue(props.direction, "vertical")} renderer-stack-gap--${classValue(props.gap, "md")}`}
    >
      {children}
    </div>
  );
}
function Spacer({ props }: RenderProps) {
  return (
    <div
      aria-hidden="true"
      className={`renderer-spacer renderer-spacer--${classValue(props.size, "md")}`}
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
    { className: "renderer-heading" },
    text(props.text),
  );
}

function RichText({ props }: RenderProps) {
  const value = props.content;
  if (typeof value === "string") return <p className="renderer-richtext">{value}</p>;
  if (!Array.isArray(value)) return <p className="renderer-richtext" />;
  return (
    <div className="renderer-richtext">
      {value.map((block, index) => {
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
    <img
      className="renderer-image"
      src={`/media/${encodeURIComponent(mediaId)}`}
      alt={text(props.alt)}
      loading="lazy"
    />
  );
}
function Button({ props }: RenderProps) {
  return (
    <a
      className={`renderer-button renderer-button--${classValue(props.variant, "primary")}`}
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
    <section className="renderer-hero" aria-labelledby="renderer-hero-heading">
      <h2 id="renderer-hero-heading">{text(props.heading)}</h2>
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
    return (
      <article className="renderer-collection-detail">
        {item ? (
          <>
            <h2>{text(item.title ?? item.slug)}</h2>
            <p>{text(item.summary ?? item.description)}</p>
          </>
        ) : null}
      </article>
    );
  }
  return (
    <div className={`renderer-collection renderer-collection--${mode}`}>
      {items.map((item, index) => (
        <article key={text(item.id) || index}>
          <h2>{text(item.title ?? item.slug)}</h2>
          <p>{text(item.summary ?? item.description)}</p>
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
    <div data-component={node.component_type} data-node-id={node.id}>
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
    <main
      data-render-mode={projection.render_mode}
      data-site-id={projection.site.id}
      aria-labelledby="page-title"
    >
      <h1 id="page-title">{projection.page.title}</h1>
      {projection.composition.nodes.map((node) =>
        renderNode(node, projection.locale, projection.bindings),
      )}
    </main>
  );
}
