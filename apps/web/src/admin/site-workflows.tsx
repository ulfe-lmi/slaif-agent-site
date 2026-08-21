"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";

import { Button, Card, StatusPanel } from "../components/ui/primitives";
import {
  archiveSite,
  createSite,
  loadAdmin,
  loadAuthority,
  loadDomains,
  loadSite,
  putDomain,
  removeDomain,
  updateSite,
  type CurrentAuthority,
  type DomainMapping,
  type SiteRecord,
} from "./api";

function message(reason: unknown): string {
  const code = reason instanceof Error ? reason.message : "invalid-response";
  if (code === "unauthenticated") return "Your session ended. Sign in and try again.";
  if (code === "denied" || code === "not-found")
    return "This site is unavailable or you do not have access.";
  if (code === "conflict") return "The site changed. Reload before trying again.";
  if (code === "invalid") return "Check the highlighted values and try again.";
  if (code === "unavailable")
    return "The service is temporarily unavailable. Try again later.";
  return "The server returned an unexpected response. No change was assumed.";
}

function field(data: FormData, name: string): string {
  const value = data.get(name);
  return typeof value === "string" ? value : "";
}

export function NewSiteWorkflow() {
  const pending = useRef(false);
  const [allowed, setAllowed] = useState<boolean | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    void loadAdmin()
      .then(({ sites }) =>
        setAllowed(sites.some((site) => site.platform_administrator)),
      )
      .catch((reason) => setError(message(reason)));
  }, []);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending.current) return;
    pending.current = true;
    setError("");
    const data = new FormData(event.currentTarget);
    try {
      const site = await createSite({
        site_key: field(data, "site_key"),
        display_name: field(data, "display_name"),
        default_locale: field(data, "default_locale"),
      });
      window.location.assign(`/admin/sites/${site.site_id}`);
    } catch (reason) {
      setError(message(reason));
      pending.current = false;
    }
  }
  if (error && allowed === null) return <StatusPanel>{error}</StatusPanel>;
  if (allowed === null) return <p>Loading site creation authority…</p>;
  if (!allowed)
    return (
      <StatusPanel>
        Platform Administrator authority is required to create a site.
      </StatusPanel>
    );
  return (
    <form
      className="admin-form"
      onSubmit={(event) => void submit(event)}
      aria-describedby="new-site-help"
    >
      <h1>Create site</h1>
      <p id="new-site-help">
        Creates an active site. The server validates every value.
      </p>
      <label>
        Site key
        <input name="site_key" required autoComplete="off" />
      </label>
      <label>
        Display name
        <input name="display_name" required autoComplete="organization" />
      </label>
      <label>
        Default locale
        <input name="default_locale" required defaultValue="en" autoComplete="off" />
      </label>
      {error && <StatusPanel>{error}</StatusPanel>}
      <Button type="submit">Create site</Button>
    </form>
  );
}

export function SiteSettingsWorkflow({ siteId }: { siteId: string }) {
  const pending = useRef(false);
  const requestSequence = useRef(0);
  const [site, setSite] = useState<SiteRecord | null>(null);
  const [authority, setAuthority] = useState<CurrentAuthority | null>(null);
  const [domains, setDomains] = useState<DomainMapping[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [recent, setRecent] = useState(false);
  async function refresh() {
    const sequence = ++requestSequence.current;
    const [loadedSite, loadedAuthority, loadedDomains, admin] = await Promise.all([
      loadSite(siteId),
      loadAuthority(siteId),
      loadDomains(siteId),
      loadAdmin(),
    ]);
    if (sequence !== requestSequence.current) return;
    setSite(loadedSite);
    setAuthority(loadedAuthority);
    setDomains(loadedDomains);
    setRecent(admin.session.recent_auth);
  }
  useEffect(() => {
    void refresh().catch((reason) => setError(message(reason)));
  }, [siteId]);
  async function act(operation: () => Promise<unknown>, success: string) {
    if (pending.current) return;
    pending.current = true;
    setError("");
    setNotice("");
    try {
      await operation();
      await refresh();
      setNotice(success);
    } catch (reason) {
      setError(message(reason));
    } finally {
      pending.current = false;
    }
  }
  if (!site || !authority)
    return (
      <>{error ? <StatusPanel>{error}</StatusPanel> : <p>Loading site settings…</p>}</>
    );
  const profile =
    authority.platform_administrator ||
    authority.effective_permissions.includes("site-policy:manage");
  const domainManage =
    authority.platform_administrator ||
    authority.effective_permissions.includes("site-domain:manage");
  return (
    <div className="workflow-stack">
      <h1>{site.display_name} settings</h1>
      <p>
        <a href={`/admin/sites/${siteId}`}>Back to overview</a>
      </p>
      {error && <StatusPanel>{error}</StatusPanel>}
      {notice && <StatusPanel>{notice}</StatusPanel>}
      <Card>
        <h2>Profile</h2>
        {profile ? (
          <form
            className="admin-form"
            onSubmit={(event) => {
              event.preventDefault();
              const data = new FormData(event.currentTarget);
              void act(
                () =>
                  updateSite(siteId, {
                    display_name: field(data, "display_name"),
                    default_locale: field(data, "default_locale"),
                  }),
                "Profile updated.",
              );
            }}
          >
            <label>
              Display name
              <input name="display_name" required defaultValue={site.display_name} />
            </label>
            <label>
              Default locale
              <input
                name="default_locale"
                required
                defaultValue={site.default_locale}
              />
            </label>
            <Button type="submit">Save profile</Button>
          </form>
        ) : (
          <p>Read-only: site-policy management permission is required.</p>
        )}
      </Card>
      <Card>
        <h2>Domain mappings</h2>
        <p>Mappings configure routing only; they do not automate DNS.</p>
        <ul className="domain-list">
          {domains.map((item) => (
            <li key={item.domain_id}>
              <strong>
                {item.hostname}
                {item.path_prefix}
              </strong>
              {item.is_primary ? " · primary" : ""}
              {domainManage && (
                <span className="admin-actions">
                  {!item.is_primary && (
                    <Button
                      type="button"
                      onClick={() =>
                        void act(
                          () =>
                            putDomain(
                              siteId,
                              {
                                hostname: item.hostname,
                                path_prefix: item.path_prefix,
                                is_primary: true,
                              },
                              item.domain_id,
                            ),
                          "Primary domain replaced.",
                        )
                      }
                    >
                      Make primary
                    </Button>
                  )}
                  <Button
                    type="button"
                    onClick={() =>
                      void act(
                        () => removeDomain(siteId, item.domain_id),
                        "Domain removed.",
                      )
                    }
                  >
                    Remove
                  </Button>
                </span>
              )}
            </li>
          ))}
        </ul>
        {domainManage ? (
          <form
            className="admin-form admin-form-inline"
            onSubmit={(event) => {
              event.preventDefault();
              const data = new FormData(event.currentTarget);
              void act(
                () =>
                  putDomain(siteId, {
                    hostname: field(data, "hostname"),
                    path_prefix: field(data, "path_prefix"),
                    is_primary: data.get("is_primary") === "on",
                  }),
                "Domain saved.",
              );
            }}
          >
            <label>
              Hostname
              <input name="hostname" required />
            </label>
            <label>
              Path prefix
              <input name="path_prefix" required defaultValue="/" />
            </label>
            <label className="check-label">
              <input name="is_primary" type="checkbox" /> Primary mapping
            </label>
            <Button type="submit">Add domain</Button>
          </form>
        ) : (
          <p>Read-only: domain management permission is required.</p>
        )}
      </Card>
      {authority.platform_administrator && (
        <Card>
          <h2>Archive site</h2>
          <p>
            Archive disables routing and future mutations. It does not delete the site
            or its rows.
          </p>
          <Dialog.Root modal={false}>
            <Dialog.Trigger asChild>
              <Button type="button">Archive {site.display_name}</Button>
            </Dialog.Trigger>
            <Dialog.Portal>
              <Dialog.Overlay className="site-switcher-overlay" />
              <Dialog.Content className="site-switcher-dialog">
                <Dialog.Title>Archive {site.display_name}?</Dialog.Title>
                <Dialog.Description>
                  This does not delete data. Explicit confirmation and a recent
                  authenticated session are required.
                </Dialog.Description>
                {!recent && (
                  <StatusPanel>
                    Your authentication is not recent. Sign in again before archiving.
                  </StatusPanel>
                )}
                <div className="admin-actions">
                  <Dialog.Close asChild>
                    <Button type="button">Cancel</Button>
                  </Dialog.Close>
                  <Button
                    type="button"
                    disabled={!recent}
                    onClick={() =>
                      void act(
                        () => archiveSite(siteId),
                        "Site archived. Routing is disabled.",
                      )
                    }
                  >
                    Confirm archive
                  </Button>
                </div>
              </Dialog.Content>
            </Dialog.Portal>
          </Dialog.Root>
        </Card>
      )}
    </div>
  );
}
