"use client";

/**
 * Trusted React renderer for the component catalog.
 *
 * Architecture reference: ARCHITECTURE-for-agents.md §7. Every component
 * renders from validated props only. No raw HTML, no inline styles, no
 * arbitrary JavaScript execution. All styling uses CSS classes.
 */

import type { ComponentDefinition } from "@slaif-agent-site/component-catalog";

interface RenderProps {
  readonly definition: ComponentDefinition;
  readonly props: Record<string, unknown>;
  readonly children?: React.ReactNode;
  readonly locale: string;
}

function Section({ props, children }: RenderProps) {
  const variant = (props.variant as string) ?? "default";
  return (
    <section className={`renderer-section renderer-section--${variant}`}>
      {children}
    </section>
  );
}

function Container({ props, children }: RenderProps) {
  const width = (props.width as string) ?? "md";
  return (
    <div className={`renderer-container renderer-container--${width}`}>{children}</div>
  );
}

function Columns({ props, children }: RenderProps) {
  const count = (props.count as number) ?? 2;
  return (
    <div className={`renderer-columns renderer-columns--${count}`}>{children}</div>
  );
}

function Heading({ props }: RenderProps) {
  const level = Math.min(6, Math.max(1, (props.level as number) ?? 1));
  const text = (props.text as string) ?? "";

  if (level === 1) return <h1 className="renderer-heading">{text}</h1>;
  if (level === 2) return <h2 className="renderer-heading">{text}</h2>;
  if (level === 3) return <h3 className="renderer-heading">{text}</h3>;
  if (level === 4) return <h4 className="renderer-heading">{text}</h4>;
  if (level === 5) return <h5 className="renderer-heading">{text}</h5>;
  return <h6 className="renderer-heading">{text}</h6>;
}

function RichText({ props }: RenderProps) {
  return (
    <div className="renderer-richtext">
      {typeof props.content === "string" ? props.content : ""}
    </div>
  );
}

function Image({ props }: RenderProps) {
  return (
    <img
      className="renderer-image"
      src={typeof props.mediaId === "string" ? `/media/${props.mediaId}` : ""}
      alt={typeof props.alt === "string" ? props.alt : ""}
      loading="lazy"
    />
  );
}

function Button({ props }: RenderProps) {
  const variant = (props.variant as string) ?? "primary";
  return (
    <a
      className={`renderer-button renderer-button--${variant}`}
      href={typeof props.href === "string" ? props.href : "#"}
    >
      {typeof props.label === "string" ? props.label : ""}
    </a>
  );
}

function Quote({ props }: RenderProps) {
  return (
    <blockquote className="renderer-quote">
      <p>{typeof props.text === "string" ? props.text : ""}</p>
      {props.attribution ? (
        <cite>{typeof props.attribution === "string" ? props.attribution : ""}</cite>
      ) : null}
    </blockquote>
  );
}

function Hero({ props, children }: RenderProps) {
  return (
    <div className="renderer-hero">
      <h1 className="renderer-hero__heading">
        {typeof props.heading === "string" ? props.heading : ""}
      </h1>
      {props.subheading ? (
        <p className="renderer-hero__subheading">
          {typeof props.subheading === "string" ? props.subheading : ""}
        </p>
      ) : null}
      {children}
    </div>
  );
}

function Header({ children }: RenderProps) {
  return <header className="renderer-header">{children}</header>;
}

function Footer({ children }: RenderProps) {
  return <footer className="renderer-footer">{children}</footer>;
}

const RENDERERS: Record<string, (props: RenderProps) => React.ReactElement> = {
  Section,
  Container,
  Columns,
  Heading,
  RichText,
  Image,
  Button,
  Quote,
  Hero,
  Header,
  Footer,
};

export function renderComponent(
  node: {
    componentType: string;
    props: Record<string, unknown>;
    children?: React.ReactNode;
  },
  locale: string,
): React.ReactElement | null {
  const definition = RENDERERS[node.componentType];
  if (!definition) return null;
  const fallback: ComponentDefinition = {
    type: node.componentType,
    category: "basic",
    schemaVersion: "1",
    allowedSlots: [],
    maxChildren: 0,
    propsSchema: {},
  };
  return definition({
    definition: fallback,
    props: node.props,
    children: node.children,
    locale,
  });
}
