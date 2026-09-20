/** One pure trusted renderer shared by Puck, public SSR, and workspace preview. */

import { createElement, type ReactElement, type ReactNode } from "react";
import {
  isResponsiveValue,
  RESPONSIVE_LABELS,
  type ComponentDefinition,
} from "@slaif-agent-site/component-catalog";
import type { ThemeRecord } from "@slaif-agent-site/composition-schema";
import type {
  PageProjection,
  ProjectionAncestor,
  ProjectionNode,
  ProjectionRegion,
} from "../sites/render";
import { RENDERER_STYLESHEET } from "./styles";
import { CollectionFilter, CollectionSearch } from "./collection-filter-components";
import {
  itemTitle,
  matchesAllFacets,
  matchesSearch,
  parseCollectionFacets,
  type FilterField,
} from "./bounded-collection-filter";

interface BindingMeta {
  readonly filter_fields: readonly FilterField[];
}

interface RenderProps {
  readonly definition: ComponentDefinition;
  readonly props: Record<string, unknown>;
  readonly children?: ReactNode;
  readonly locale: string;
  readonly data?: readonly Record<string, unknown>[];
  readonly meta?: BindingMeta;
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

// Bounded embed policy (bounded-embed/v1): the trusted renderer rebuilds
// canonical embed URLs exclusively from structured props. The allowlist is
// the reduced-tracking endpoints only (youtube-nocookie, player.vimeo.com,
// www.openstreetmap.org); no autoplay/marketing/tracking parameter is ever
// emitted, and any non-canonical prop set renders the bounded placeholder
// instead of an iframe (fail-closed).
const EMBED_TITLE_MAX_LENGTH = 120;
const EMBED_MAP_LAYERS = new Set(["mapnik", "cyclemap", "transportmap"]);
const EMBED_MAP_DEFAULT_LAYER = "mapnik";

function formatEmbedCoordinate(value: number): string {
  if (Number.isInteger(value)) return String(value);
  const text = value.toFixed(10).replace(/0+$/, "").replace(/\.$/, "");
  if (text === "" || text === "-") return "0";
  return text;
}

function canonicalVideoEmbedUrl(provider: unknown, videoId: unknown): string | null {
  if (typeof provider !== "string" || typeof videoId !== "string") return null;
  if (provider === "youtube-nocookie") {
    if (videoId.length !== 11 || !/^[A-Za-z0-9_-]+$/.test(videoId)) return null;
    return `https://www.youtube-nocookie.com/embed/${videoId}`;
  }
  if (provider === "vimeo") {
    if (videoId.length < 6 || !/^[0-9]+$/.test(videoId)) return null;
    return `https://player.vimeo.com/video/${videoId}`;
  }
  return null;
}

function canonicalMapEmbedUrl(props: Record<string, unknown>): string | null {
  const raw = props.bbox;
  if (typeof raw !== "object" || raw === null) return null;
  const bbox = raw as Record<string, unknown>;
  const values = [bbox.west, bbox.south, bbox.east, bbox.north];
  if (values.some((value) => typeof value !== "number" || !Number.isFinite(value)))
    return null;
  const [west, south, east, north] = values as [number, number, number, number];
  if (Math.abs(west) > 180 || Math.abs(east) > 180) return null;
  if (Math.abs(south) > 85.05112877 || Math.abs(north) > 85.05112877) return null;
  if (!(west < east) || !(south < north)) return null;
  const layer = props.layer === undefined ? EMBED_MAP_DEFAULT_LAYER : props.layer;
  if (typeof layer !== "string" || !EMBED_MAP_LAYERS.has(layer)) return null;
  const bboxText = [west, south, east, north].map(formatEmbedCoordinate).join(",");
  const query: Record<string, string> = { bbox: bboxText };
  if (layer !== EMBED_MAP_DEFAULT_LAYER) query.layer = layer;
  const rendered = Object.keys(query)
    .sort()
    .map((key) => `${key}=${query[key]}`)
    .join("&");
  return `https://www.openstreetmap.org/export/embed.html?${rendered}`;
}

function embedTitle(value: unknown): string | null {
  if (typeof value !== "string" || !value) return null;
  if (value.length > EMBED_TITLE_MAX_LENGTH) return null;
  return value;
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
function VideoEmbed({ props }: RenderProps) {
  const src = canonicalVideoEmbedUrl(props.provider, props.video_id);
  const title = embedTitle(props.title);
  if (src === null || title === null) {
    return (
      <div
        aria-label={title ?? "Video unavailable"}
        className="sl-embed sl-embed--video sl-embed--placeholder"
        role="img"
      />
    );
  }
  return (
    <iframe
      className="sl-embed sl-embed--video"
      src={src}
      title={title}
      loading="lazy"
      referrerPolicy="no-referrer"
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
function CallToAction({ props }: RenderProps) {
  const variant = classValue(props.variant, "primary");
  const body = text(props.text);
  return (
    <section className={`renderer-call-to-action renderer-call-to-action--${variant}`}>
      <h2>{text(props.heading)}</h2>
      {body ? <p>{body}</p> : null}
      <a
        className={`renderer-button renderer-button--${variant}`}
        href={safeHref(props.href)}
      >
        {text(props.label)}
      </a>
    </section>
  );
}
function ContactBlock({ props }: RenderProps) {
  const address = text(props.address);
  const phone = text(props.phone);
  const email = text(props.email);
  const hours = text(props.hours);
  return (
    <section className="renderer-contact">
      <h2>{text(props.organization)}</h2>
      {address ? <p className="renderer-contact-address">{address}</p> : null}
      {phone ? <p className="renderer-contact-phone">{phone}</p> : null}
      {email ? <p className="renderer-contact-email">{email}</p> : null}
      {hours ? <p className="renderer-contact-hours">{hours}</p> : null}
    </section>
  );
}
function MapBlock({ props }: RenderProps) {
  const src = canonicalMapEmbedUrl(props);
  const title = embedTitle(props.title);
  if (src === null || title === null) {
    return (
      <div
        aria-label={title ?? "Map unavailable"}
        className="sl-embed sl-embed--map sl-embed--placeholder"
        role="img"
      />
    );
  }
  return (
    <iframe
      className="sl-embed sl-embed--map"
      src={src}
      title={title}
      loading="lazy"
      referrerPolicy="no-referrer"
    />
  );
}
function RelatedItems({ props, data }: RenderProps) {
  const items: readonly Record<string, unknown>[] = Array.isArray(data) ? data : [];
  if (items.length === 0) return null;
  const heading = text(props.heading);
  return (
    <section className="renderer-related">
      {heading ? <h2>{heading}</h2> : null}
      <ul className="renderer-collection-list">
        {items.map((item, index) => {
          const values =
            typeof item.values === "object" && item.values !== null
              ? (item.values as Record<string, unknown>)
              : {};
          return (
            <li key={text(item.id) || index}>
              <article>
                <h2>{text(values.title ?? item.slug)}</h2>
                <p>{text(values.summary ?? values.description)}</p>
              </article>
            </li>
          );
        })}
      </ul>
    </section>
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

/**
 * Server-safe static variants of the bounded client-filter components.
 *
 * The trusted renderer is shared by RSC surfaces (public canonical, Puck
 * editor canvas), which render the interactive `"use client"`
 * implementations, and by flight-free SSR surfaces (workspace preview
 * route), which deliver a pure server-rendered document with no client
 * bundle and therefore cannot mount client state. The static variants
 * render the exact initial interactive state — empty search query,
 * initial facet values — with identical bounded markup and the same pure
 * fixed-operator logic, so every surface renders one consistent contract;
 * interactivity is simply absent where no client bundle is delivered.
 */
function StaticResultsList({
  items,
}: Readonly<{ items: readonly Record<string, unknown>[] }>) {
  return (
    <ul className="renderer-collection-list">
      {items.map((item, index) => {
        const values =
          typeof item.values === "object" && item.values !== null
            ? (item.values as Record<string, unknown>)
            : {};
        return (
          <li key={text(item.id) || index}>
            <article>
              <h2>{itemTitle(item)}</h2>
              <p>{text(values.summary ?? values.description)}</p>
            </article>
          </li>
        );
      })}
    </ul>
  );
}
function CollectionSearchStatic({ props, data, meta }: RenderProps) {
  const items: readonly Record<string, unknown>[] = Array.isArray(data) ? data : [];
  const filterFields = meta?.filter_fields ?? [];
  const visible = items.filter((item) => matchesSearch(item, filterFields, ""));
  return (
    <div className="renderer-collection-search">
      <label className="renderer-collection-search-field">
        <span>{text(props.placeholder) || "Search"}</span>
        <input
          className="renderer-collection-search-input"
          type="search"
          maxLength={256}
        />
      </label>
      {visible.length === 0 ? (
        <p className="renderer-collection-search-empty">No results</p>
      ) : (
        <StaticResultsList items={visible} />
      )}
    </div>
  );
}
function CollectionFilterStatic({ props, data, meta }: RenderProps) {
  const facets = parseCollectionFacets(props);
  const items: readonly Record<string, unknown>[] = Array.isArray(data) ? data : [];
  const filterFields = meta?.filter_fields ?? [];
  const visible = items.filter((item) => matchesAllFacets(item, filterFields, facets));
  return (
    <div className="renderer-collection-filter">
      {facets.length > 0 ? (
        <div className="renderer-collection-filter-facets">
          {facets.map((facet, index) => (
            <label
              key={`${facet.fieldKey}-${facet.operator}-${index}`}
              className="renderer-collection-filter-facet"
            >
              <span>{`${facet.fieldKey} ${facet.operator}`}</span>
              <input
                className="renderer-collection-filter-input"
                type="text"
                value={facet.value}
                maxLength={4096}
              />
            </label>
          ))}
        </div>
      ) : null}
      {visible.length === 0 ? (
        <p className="renderer-collection-filter-empty">No results</p>
      ) : (
        <StaticResultsList items={visible} />
      )}
    </div>
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
  CallToAction,
  VideoEmbed,
  ContactBlock,
  MapBlock,
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
  CollectionSearch: (props) => <CollectionSearchStatic {...props} />,
  CollectionFilter: (props) => <CollectionFilterStatic {...props} />,
  RelatedItems: (props) => <RelatedItems {...props} />,
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

/**
 * The one documented bounded client-state pattern (local state only, no
 * I/O, no persistence, no URL mutation). These wrappers render the real
 * client-component elements on RSC surfaces; flight-free SSR surfaces
 * use the static variants from RENDERERS instead.
 */
const INTERACTIVE_RENDERERS: Record<string, (props: RenderProps) => ReactElement> = {
  CollectionSearch: (props) => <CollectionSearch {...props} />,
  CollectionFilter: (props) => <CollectionFilter {...props} />,
};

export function renderComponent(
  node: { componentType: string; props: Record<string, unknown>; children?: ReactNode },
  locale: string,
  data?: readonly Record<string, unknown>[],
  meta?: BindingMeta,
  clientState = true,
): ReactElement {
  // Render registry entries as real React elements (never direct function
  // calls): direct calls bypass React's client-component boundary
  // enforcement and would break the bounded client-state components.
  const Renderer =
    clientState && INTERACTIVE_RENDERERS[node.componentType] !== undefined
      ? INTERACTIVE_RENDERERS[node.componentType]
      : RENDERERS[node.componentType];
  if (!Renderer) throw new Error("unknown trusted component");
  return createElement(Renderer, {
    definition: FALLBACK_DEFINITION,
    props: node.props,
    children: node.children,
    locale,
    ...(data === undefined ? {} : { data }),
    ...(meta === undefined ? {} : { meta }),
  });
}

function renderNode(
  node: ProjectionNode,
  locale: string,
  bindings: PageProjection["bindings"],
  bindingMeta: PageProjection["binding_meta"],
  clientState = true,
): ReactElement {
  const children = node.children.map((child) =>
    renderNode(child, locale, bindings, bindingMeta, clientState),
  );
  return (
    <div data-component={node.component_type}>
      {renderComponent(
        { componentType: node.component_type, props: node.props, children },
        locale,
        bindings[node.id],
        bindingMeta[node.id],
        clientState,
      )}
    </div>
  );
}

function regionHref(
  siteKey: string,
  basePath: string,
  currentRoute: string,
  targetRoute: string,
): string {
  // External targets render as-is; they are already §34.2-validated.
  if (targetRoute.startsWith("http://") || targetRoute.startsWith("https://"))
    return targetRoute;
  const target = targetRoute === "/" ? "" : targetRoute.replace(/^\//, "");
  const base = basePath.replace(/\/$/, "");
  // Canonical renders use absolute site-rooted hrefs.
  if (!base.startsWith("/preview/")) {
    return target ? `${base}/${target}` : base;
  }
  // Preview renders use relative hrefs so the private workspace identifier
  // never enters the page HTML (privacy contract).
  const current = currentRoute === "/" ? "" : currentRoute.replace(/^\//, "");
  const depth = current ? current.split("/").length : 0;
  if (depth === 0) {
    return target ? `${siteKey}/${target}` : siteKey;
  }
  // Page URLs never carry a trailing slash, so the browser's relative
  // base directory already excludes the page's own last segment: one
  // fewer "../" hop than the site-path depth.
  const ups = "../".repeat(depth - 1);
  return target ? `${ups}${target}` : `${ups}./`;
}

function SiteLanguageSwitcher({
  projection,
  basePath,
}: Readonly<{ projection: PageProjection; basePath: string }>): ReactElement {
  const locales = [...projection.locales].sort(
    (a, b) => a.position - b.position || a.tag.localeCompare(b.tag),
  );
  return (
    <nav aria-label="Language" className="renderer-region-language">
      {locales.map((locale) => (
        <span key={locale.tag} className="renderer-region-language-item">
          {locale.tag === projection.locale ? (
            <span aria-current="true">{locale.tag}</span>
          ) : locale.switcher_href ? (
            <a
              href={regionHref(
                projection.site.key,
                basePath,
                projection.page.effective_route,
                locale.switcher_href,
              )}
            >
              {locale.tag}
            </a>
          ) : (
            <span className="renderer-region-language-inert" aria-disabled="true">
              {locale.tag}
            </span>
          )}
        </span>
      ))}
    </nav>
  );
}

function SiteBreadcrumbs({
  projection,
  ancestors,
  currentTitle,
  basePath,
}: Readonly<{
  projection: PageProjection;
  ancestors: readonly ProjectionAncestor[];
  currentTitle: string;
  basePath: string;
}>): ReactElement {
  return (
    <nav aria-label="Breadcrumb" className="renderer-region-breadcrumbs">
      <ol>
        {ancestors.map((ancestor) => (
          <li key={ancestor.effective_route}>
            <a
              href={regionHref(
                projection.site.key,
                basePath,
                projection.page.effective_route,
                ancestor.effective_route,
              )}
            >
              {ancestor.title}
            </a>
          </li>
        ))}
        <li aria-current="page">{currentTitle}</li>
      </ol>
    </nav>
  );
}

function SiteRegionShell({
  region,
  projection,
  basePath,
}: Readonly<{
  region: ProjectionRegion;
  projection: PageProjection;
  basePath: string;
}>): ReactElement {
  const isHeader = region.region_key === "header";
  const className = isHeader
    ? `renderer-region renderer-region-header renderer-region-header--${region.variant}`
    : `renderer-region renderer-region-footer renderer-region-footer--${region.variant}`;
  const links = (
    <nav aria-label={isHeader ? "Site" : "Footer"} className="renderer-region-links">
      <ul>
        {region.entries.map((entry) => (
          <li key={entry.href}>
            <a
              href={regionHref(
                projection.site.key,
                basePath,
                projection.page.effective_route,
                entry.href,
              )}
            >
              {entry.label}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  );
  if (isHeader) {
    return (
      <header className={className}>
        <div className="renderer-region-inner">
          <a
            className="renderer-region-brand"
            href={regionHref(
              projection.site.key,
              basePath,
              projection.page.effective_route,
              "/",
            )}
          >
            {projection.site.key}
          </a>
          {region.entries.length > 0 ? links : null}
          <SiteLanguageSwitcher projection={projection} basePath={basePath} />
        </div>
      </header>
    );
  }
  return (
    <footer className={className}>
      <div className="renderer-region-inner">
        {region.entries.length > 0 ? links : null}
        {region.note ? <p className="renderer-region-note">{region.note}</p> : null}
      </div>
    </footer>
  );
}

export function renderProjection(
  projection: PageProjection,
  basePath?: string,
  clientState = true,
): ReactElement {
  const base = basePath ?? `/s/${projection.site.key}`;
  const header = projection.regions.find((region) => region.region_key === "header");
  const footer = projection.regions.find((region) => region.region_key === "footer");
  return (
    <>
      <link rel="stylesheet" href={RENDERER_STYLESHEET} />
      <div className="renderer-page">
        {header ? (
          <SiteRegionShell region={header} projection={projection} basePath={base} />
        ) : null}
        <main
          className={`renderer-surface ${themeClasses(projection.page_style)}`}
          lang={projection.locale}
          data-render-mode={projection.render_mode}
          aria-labelledby="page-title"
        >
          {projection.ancestors.length > 0 ? (
            <SiteBreadcrumbs
              projection={projection}
              ancestors={projection.ancestors}
              currentTitle={projection.page.title}
              basePath={base}
            />
          ) : null}
          <h1 id="page-title">{projection.page.title}</h1>
          {projection.composition.nodes.map((node) =>
            renderNode(
              node,
              projection.locale,
              projection.bindings,
              projection.binding_meta,
              clientState,
            ),
          )}
        </main>
        {footer ? (
          <SiteRegionShell region={footer} projection={projection} basePath={base} />
        ) : null}
      </div>
    </>
  );
}
