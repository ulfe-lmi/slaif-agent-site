import { headers } from "next/headers";
import { notFound } from "next/navigation";

import { resolveSiteContext } from "../src/sites/render";
import { SiteContextShell } from "../src/sites/shell";

function isLoopbackAuthority(authority: string): boolean {
  try {
    const parsed = new URL(`http://${authority}`);
    return (
      parsed.username === "" &&
      parsed.password === "" &&
      parsed.pathname === "/" &&
      ["localhost", "127.0.0.1", "[::1]"].includes(parsed.hostname.toLowerCase())
    );
  } catch {
    return false;
  }
}

export default async function Home() {
  const authority = (await headers()).get("host") ?? "";
  if (!isLoopbackAuthority(authority)) {
    const context = await resolveSiteContext(authority, "/");
    if (!context) notFound();
    return <SiteContextShell context={context} />;
  }
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
            Secure local administrator setup and server-side sessions, trusted
            multi-site identity and routing, and Platform Administrator site/domain
            APIs. Site-scoped built-in RBAC and membership APIs share explicit
            route-policy declarations, while publication authority stays separate from
            delegation ceilings.
          </p>
        </article>
        <article>
          <p className="number">02</p>
          <h2>Still deliberately absent</h2>
          <p>
            Site and membership UI, invitations, custom roles, content models and site
            content, workspaces and agent capabilities, editing/Puck, review, and
            publication execution.
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
