"use client";

import { type ReactNode, useEffect, useState } from "react";

import { csrfCookie, logout } from "../auth/client";
import {
  Button,
  Card,
  Skeleton,
  StatusBadge,
  StatusPanel,
} from "../components/ui/primitives";
import {
  loadAdmin,
  loadAuthority,
  type CurrentAuthority,
  type CurrentSite,
} from "./api";
import { CspModal } from "./csp-modal";
import { AgentSessions } from "./agent-sessions";

function SiteSwitcher({ sites }: { sites: CurrentSite[] }) {
  return (
    <CspModal
      title="Choose an authorized site"
      description="Site selection is kept in the address and checked again by the server."
      trigger={<Button type="button">Choose site</Button>}
    >
      {({ close }) => (
        <>
          {sites.length ? (
            <ul className="site-switcher-list">
              {sites.map((site) => (
                <li key={site.site_id}>
                  <a href={`/admin/sites/${site.site_id}`} onClick={close}>
                    {site.display_name} · {site.status}
                  </a>
                </li>
              ))}
            </ul>
          ) : (
            <p>No authorized sites</p>
          )}
          <Button type="button" onClick={close}>
            Close
          </Button>
        </>
      )}
    </CspModal>
  );
}

function Navigation({ global }: { global: boolean }) {
  return (
    <nav className="admin-nav" aria-label="Administration">
      <a href="/admin">Dashboard</a>
      <a href="/admin#sites">Sites</a>
      <a href="/admin#permissions">Users &amp; Permissions</a>
      {global && <StatusBadge>Platform governance</StatusBadge>}
      {[
        "Content",
        "Models",
        "Pages",
        "Structure",
        "Design",
        "Media",
        "Reviews",
        "Audit",
      ].map((item) => (
        <span aria-disabled="true" key={item}>
          {item} · planned
        </span>
      ))}
      {global && <a href="#ai-sessions">AI Sessions</a>}
    </nav>
  );
}

export function AdminShell({
  children,
  selectedSiteId,
}: {
  children?: ReactNode;
  selectedSiteId?: string;
}) {
  const [sites, setSites] = useState<CurrentSite[] | null>(null);
  const [authority, setAuthority] = useState<CurrentAuthority | null>(null);
  const [sessionSummary, setSessionSummary] = useState<{
    recent_auth: boolean;
    absolute_expires_at: string;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    void loadAdmin()
      .then(async (value) => {
        setSites(value.sites);
        setSessionSummary(value.session);
        if (selectedSiteId) {
          if (value.sites.some((site) => site.site_id === selectedSiteId)) {
            setAuthority(await loadAuthority(selectedSiteId));
          } else {
            setError("This site is unavailable or you do not have access.");
          }
        }
      })
      .catch((reason: unknown) => {
        if (reason instanceof Error && reason.message === "unauthenticated")
          window.location.replace("/login");
        else
          setError(
            reason instanceof Error && reason.message === "not-found"
              ? "This site is unavailable or you do not have access."
              : "Administration data is temporarily unavailable.",
          );
      });
  }, [selectedSiteId]);
  const global = Boolean(sites?.some((site) => site.platform_administrator));
  async function signOut() {
    try {
      const secure = window.location.protocol === "https:";
      csrfCookie(document.cookie, secure);
      await logout(document.cookie, secure);
      window.location.replace("/login");
    } catch {
      setError("Sign out could not be completed.");
    }
  }
  return (
    <div className="admin-shell" data-admin-background-root>
      <a className="skip-link" href="#admin-main">
        Skip to main content
      </a>
      <header className="admin-topbar">
        <a className="admin-brand" href="/admin">
          <img src="/slaif-logo.svg" alt="" width="48" height="38" />
          SLAIF Agent-Site
        </a>
        <div className="admin-actions">
          <nav className="mobile-nav" aria-label="Administration">
            <SiteSwitcher sites={sites ?? []} />
          </nav>
          <Button type="button" onClick={() => void signOut()}>
            Sign out
          </Button>
        </div>
      </header>
      <div className="admin-layout">
        <aside className="admin-sidebar">
          <SiteSwitcher sites={sites ?? []} />
          <Navigation global={global} />
        </aside>
        <main className="admin-main" id="admin-main">
          {children ?? (
            <>
              <h1>{authority ? authority.display_name : "Administration dashboard"}</h1>
              {error && <StatusPanel>{error}</StatusPanel>}
              {!sites && !error && (
                <>
                  <p>Loading authorized administration data…</p>
                  <Skeleton />
                </>
              )}
              {sites && !selectedSiteId && (
                <>
                  <div className="admin-cards">
                    <Card>
                      <h2>Authorized sites</h2>
                      <p>
                        {sites.length} server-filtered site
                        {sites.length === 1 ? "" : "s"}.
                      </p>
                    </Card>
                    <Card>
                      <h2>Current session</h2>
                      <p>Authenticated session active.</p>
                      <p>Account: Local administrator</p>
                      <p>
                        Recent authentication:{" "}
                        {sessionSummary?.recent_auth ? "yes" : "no"}
                      </p>
                      <p>
                        Expires{" "}
                        {sessionSummary
                          ? new Date(
                              sessionSummary.absolute_expires_at,
                            ).toLocaleString()
                          : "—"}
                      </p>
                    </Card>
                    <Card>
                      <h2>Implemented scope</h2>
                      <p>
                        Site overview, profile, domain, creation, and protected archive
                        workflows.
                      </p>
                    </Card>
                  </div>
                  <section id="sites">
                    <h2>Sites</h2>
                    {global && (
                      <p>
                        <a href="/admin/sites/new">Create a site</a>
                      </p>
                    )}
                    {sites.length ? (
                      <ul className="site-list">
                        {sites.map((site) => (
                          <li key={site.site_id}>
                            <a href={`/admin/sites/${site.site_id}`}>
                              <strong>{site.display_name}</strong>
                              <br />
                              {site.status} ·{" "}
                              {site.platform_administrator
                                ? "Platform Administrator"
                                : site.role_key}
                            </a>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <StatusPanel>
                        No active site memberships are available.
                      </StatusPanel>
                    )}
                  </section>
                </>
              )}
              {authority && (
                <>
                  <p>
                    <StatusBadge>{authority.status}</StatusBadge>{" "}
                    {authority.platform_administrator
                      ? "Platform Administrator"
                      : authority.role_key}
                  </p>
                  <div className="admin-cards">
                    <Card>
                      <h2>Site identity</h2>
                      <p>Key: {authority.site_key}</p>
                      <p>Locale: {authority.default_locale}</p>
                    </Card>
                    <Card>
                      <h2>Revision</h2>
                      <p>Canonical revision {authority.canonical_revision}</p>
                    </Card>
                    <Card>
                      <h2>Authority</h2>
                      <p>
                        {authority.platform_administrator
                          ? "Global governance authority; no synthetic membership."
                          : `${authority.effective_permissions.length} effective permissions.`}
                      </p>
                      <p>
                        <a href={`/admin/sites/${authority.site_id}/settings`}>
                          Open site settings
                        </a>
                      </p>
                      {(authority.platform_administrator ||
                        (authority.effective_permissions.includes(
                          "membership:manage",
                        ) &&
                          authority.effective_permissions.includes("role:manage"))) && (
                        <p>
                          <a href={`/admin/sites/${authority.site_id}/memberships`}>
                            Manage memberships
                          </a>
                        </p>
                      )}
                    </Card>
                  </div>
                  <p>
                    <a href={`/s/${authority.site_key}/`}>Open public local route</a>
                  </p>
                  {authority.effective_permissions.includes("workspace:create") && (
                    <div id="ai-sessions">
                      <AgentSessions siteId={authority.site_id} />
                    </div>
                  )}
                </>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
}
