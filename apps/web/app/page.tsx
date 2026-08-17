const repository = "https://github.com/ulfe-lmi/slaif-agent-site";

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
          <span className="badge">Pre-alpha deployment skeleton</span>
          <h1 id="page-title">The runtime boundary is online.</h1>
          <p className="lead">
            This page proves the self-hosted container, edge, health, and empty database
            foundation can start together. It is not a website editor yet.
          </p>
          <div className="status" role="status">
            <span aria-hidden="true" className="status-dot" />
            Skeleton web service ready
          </div>
        </div>
      </section>

      <section className="grid" aria-label="Implementation status">
        <article>
          <p className="number">01</p>
          <h2>Implemented now</h2>
          <p>
            Isolated process containers, generated local database credentials,
            safe-empty bootstrap, internal health checks, and NGINX routing.
          </p>
        </article>
        <article>
          <p className="number">02</p>
          <h2>Deliberately deferred</h2>
          <p>
            Authentication, administrators, sites, workspaces, editing, browser
            automation, review, publication, and production TLS.
          </p>
        </article>
        <article>
          <p className="number">03</p>
          <h2>Human-governed direction</h2>
          <p>
            Agents will work in isolated reviewable workspaces; publication will remain
            a human-controlled action.
          </p>
        </article>
      </section>

      <nav aria-label="Project documentation">
        <a href={`${repository}#readme`}>Project overview</a>
        <a href={`${repository}/blob/main/docs/DEPLOYMENT.md`}>Deployment guide</a>
        <a href={`${repository}/blob/main/ARCHITECTURE.md`}>Architecture</a>
      </nav>
    </main>
  );
}
