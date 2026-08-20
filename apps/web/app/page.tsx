export default function Home() {
  return (
    <main>
      <section className="hero" aria-labelledby="page-title">
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
          <span className="badge">Self-hosted human control</span>
          <h1 id="page-title">Set up or sign in locally.</h1>
          <p className="lead">
            Create the first administrator with the one-time token shown by the
            bootstrap container, then manage the authenticated session through the
            same-origin Control API.
          </p>
          <nav aria-label="Authentication">
            <a className="button-link" href="/setup">
              First-time setup
            </a>
            <a className="button-link secondary" href="/login">
              Administrator sign in
            </a>
          </nav>
        </div>
      </section>
      <section className="grid" aria-label="Product status">
        <article>
          <p className="number">01</p>
          <h2>Implemented now</h2>
          <p>
            Local first-administrator setup, login, session inspection, logout, isolated
            services, and human-controlled foundations.
          </p>
        </article>
        <article>
          <p className="number">02</p>
          <h2>Still deliberately absent</h2>
          <p>
            OIDC, MFA, rate limiting, durable authentication audit, sites, workspaces,
            editing, review, and publication.
          </p>
        </article>
        <article>
          <p className="number">03</p>
          <h2>Human governed</h2>
          <p>
            Backend authorization remains authoritative. This interface never publishes
            or grants agent capabilities.
          </p>
        </article>
      </section>
    </main>
  );
}
