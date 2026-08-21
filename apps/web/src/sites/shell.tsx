import type { SiteContext } from "./render";

export function SiteContextShell({ context }: Readonly<{ context: SiteContext }>) {
  return (
    <main>
      <section className="hero" aria-labelledby="site-title">
        <div className="identity">
          <img
            alt="SLAIF — Slovenian AI Factory"
            className="logo"
            height="236"
            src="/slaif-logo.svg"
            width="300"
          />
          <p className="eyebrow">SLAIF Agent-Site</p>
        </div>
        <div className="message">
          <span className="badge">Trusted routing context</span>
          <h1 id="site-title">Site: {context.site_key}</h1>
          <p className="lead">
            This shell proves active site routing only. Editorial content and
            publication are not implemented.
          </p>
          <dl>
            <dt>Canonical revision</dt>
            <dd>{context.canonical_revision}</dd>
            <dt>Default locale</dt>
            <dd>{context.default_locale}</dd>
            <dt>Matched route</dt>
            <dd>
              {context.matched_hostname}
              {context.matched_path_prefix}
            </dd>
          </dl>
        </div>
      </section>
    </main>
  );
}
