"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";

import { Button, Card, StatusPanel } from "../components/ui/primitives";
import {
  createMembership,
  deactivateMembership,
  loadMembershipAdministration,
  updateMembership,
  type Membership,
  type MembershipBody,
  type PermissionCatalog,
  type RoleCatalog,
} from "./api";

type Data = Awaited<ReturnType<typeof loadMembershipAdministration>>;
const UUID =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function failure(reason: unknown): string {
  const code = reason instanceof Error ? reason.message : "invalid-response";
  if (code === "unauthenticated") return "Your session ended. Sign in and try again.";
  if (code === "denied" || code === "not-found")
    return "Membership administration is unavailable or access is denied.";
  if (code === "conflict")
    return "The membership changed. The current server state has been refreshed.";
  if (code === "invalid")
    return "The server rejected an invalid role, ceiling, user, or override.";
  if (code === "unavailable")
    return "Membership service is temporarily unavailable. Try again later.";
  return "The server returned an unexpected response. No change was assumed.";
}

function overrideBody(
  form: HTMLFormElement,
  roleKey: string,
  ceiling: number,
): MembershipBody {
  const allow: string[] = [];
  const deny: string[] = [];
  for (const [name, value] of new FormData(form)) {
    if (!name.startsWith("permission:") || typeof value !== "string") continue;
    const key = name.slice("permission:".length);
    if (value === "allow") allow.push(key);
    else if (value === "deny") deny.push(key);
  }
  return {
    role_key: roleKey,
    delegation_ceiling: ceiling,
    allow_permissions: allow.sort(),
    deny_permissions: deny.sort(),
  };
}

function PermissionOverrides({
  permissions,
  membership,
}: {
  permissions: PermissionCatalog[];
  membership?: Membership;
}) {
  const assignable = permissions.filter(
    (item) => item.site_assignable && item.permission_key !== "site:publish",
  );
  const unavailable = permissions.filter((item) => !item.site_assignable);
  const groups = Object.groupBy(assignable, (item) => item.category);
  const initial = (key: string) =>
    membership?.allow_permissions.includes(key)
      ? "allow"
      : membership?.deny_permissions.includes(key)
        ? "deny"
        : "inherit";
  return (
    <>
      <fieldset className="permission-group publication-control">
        <legend>Publication authority</legend>
        <p>
          Publication is separate from role and ceiling. Architect ceiling 4 does not
          publish by default.
        </p>
        <label>
          Site publication override
          <select name="permission:site:publish" defaultValue={initial("site:publish")}>
            <option value="inherit">Use role default</option>
            <option value="allow">Explicitly allow</option>
            <option value="deny">Explicitly deny</option>
          </select>
        </label>
      </fieldset>
      <details>
        <summary>Advanced permission overrides</summary>
        <p>
          Each save completely replaces explicit overrides. Neutral uses the selected
          role default.
        </p>
        {Object.entries(groups).map(([group, items]) => (
          <fieldset className="permission-group" key={group}>
            <legend>{group.replaceAll("_", " ")}</legend>
            {items?.map((item) => (
              <label key={item.permission_key}>
                {item.permission_key}
                <select
                  name={`permission:${item.permission_key}`}
                  defaultValue={initial(item.permission_key)}
                >
                  <option value="inherit">Role default</option>
                  <option value="allow">Allow</option>
                  <option value="deny">Deny</option>
                </select>
              </label>
            ))}
          </fieldset>
        ))}
      </details>
      <details>
        <summary>Nonassignable installation and system scopes</summary>
        <p>
          These {unavailable.length} scopes are visible for clarity but can never be
          submitted as membership overrides.
        </p>
        <ul>
          {unavailable.map((item) => (
            <li key={item.permission_key}>
              {item.permission_key} · {item.category}
            </li>
          ))}
        </ul>
      </details>
    </>
  );
}

function MembershipForm({
  roles,
  permissions,
  membership,
  onSubmit,
  label,
  disabled = false,
}: {
  roles: RoleCatalog[];
  permissions: PermissionCatalog[];
  membership?: Membership;
  onSubmit: (body: MembershipBody) => void;
  label: string;
  disabled?: boolean;
}) {
  const first = membership?.role_key ?? roles[0]?.role_key ?? "";
  const [roleKey, setRoleKey] = useState(first);
  const selectedRole = roles.find((item) => item.role_key === roleKey);
  const max = selectedRole?.default_delegation_ceiling ?? 0;
  const [ceiling, setCeiling] = useState(
    Math.min(membership?.delegation_ceiling ?? max, max),
  );
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit(overrideBody(event.currentTarget, roleKey, ceiling));
  }
  return (
    <form className="admin-form" onSubmit={submit}>
      <label>
        Built-in role
        <select
          name="role_key"
          value={roleKey}
          onChange={(event) => {
            const next = event.target.value;
            const nextMax =
              roles.find((item) => item.role_key === next)
                ?.default_delegation_ceiling ?? 0;
            setRoleKey(next);
            setCeiling((current) => Math.min(current, nextMax));
          }}
        >
          {roles.map((role) => (
            <option key={role.role_key} value={role.role_key}>
              {role.label}
            </option>
          ))}
        </select>
      </label>
      <p>
        {selectedRole?.description} Default permissions:{" "}
        {selectedRole?.default_permissions.length ?? 0}. Maximum ceiling: {max}.
      </p>
      <label>
        Explicit delegation ceiling
        <select
          name="delegation_ceiling"
          value={ceiling}
          onChange={(event) => setCeiling(Number(event.target.value))}
        >
          {Array.from({ length: max + 1 }, (_, value) => (
            <option key={value} value={value}>
              {value}
            </option>
          ))}
        </select>
      </label>
      <PermissionOverrides
        permissions={permissions}
        {...(membership ? { membership } : {})}
      />
      <Button type="submit" disabled={disabled}>
        {label}
      </Button>
    </form>
  );
}

function MembershipCard({
  item,
  data,
  canManage,
  busy,
  mutate,
}: {
  item: Membership;
  data: Data;
  canManage: boolean;
  busy: boolean;
  mutate: (
    operation: () => Promise<unknown>,
    success: string,
    close?: () => void,
  ) => void;
}) {
  const self = item.user_account_id === data.session.user_account_id;
  return (
    <li className="membership-card">
      <dl>
        <div>
          <dt>User UUID</dt>
          <dd>{item.user_account_id}</dd>
        </div>
        <div>
          <dt>Role/status</dt>
          <dd>
            {item.role_key} · {item.status}
          </dd>
        </div>
        <div>
          <dt>Ceiling</dt>
          <dd>
            {item.delegation_ceiling} explicit / {item.effective_delegation_ceiling}{" "}
            effective
          </dd>
        </div>
        <div>
          <dt>Version</dt>
          <dd>{item.version}</dd>
        </div>
        <div>
          <dt>Global fact</dt>
          <dd>
            {item.platform_administrator
              ? "Platform Administrator"
              : "Site member only"}
          </dd>
        </div>
        <div>
          <dt>Overrides</dt>
          <dd>
            {item.allow_permissions.length} allow / {item.deny_permissions.length} deny
            · {item.effective_permissions.length} effective
          </dd>
        </div>
      </dl>
      {canManage && !self && (
        <div className="admin-actions">
          <Dialog.Root>
            <Dialog.Trigger asChild>
              <Button type="button">Edit membership</Button>
            </Dialog.Trigger>
            <Dialog.Portal>
              <Dialog.Overlay className="site-switcher-overlay" />
              <Dialog.Content className="site-switcher-dialog membership-dialog">
                <Dialog.Title>Edit {item.user_account_id}</Dialog.Title>
                <Dialog.Description>
                  Saving replaces the complete role, ceiling, and explicit override set
                  using expected version {item.version}.
                </Dialog.Description>
                <MembershipForm
                  roles={data.roles}
                  permissions={data.permissions}
                  membership={item}
                  label="Save membership"
                  disabled={busy}
                  onSubmit={(body) =>
                    mutate(
                      () =>
                        updateMembership(
                          data.authority.site_id,
                          item.user_account_id,
                          item.version,
                          item.status,
                          body,
                        ),
                      "Membership updated.",
                    )
                  }
                />
                <Dialog.Close asChild>
                  <Button type="button">Cancel</Button>
                </Dialog.Close>
              </Dialog.Content>
            </Dialog.Portal>
          </Dialog.Root>
          {item.status === "ACTIVE" && (
            <Dialog.Root>
              <Dialog.Trigger asChild>
                <Button type="button">Deactivate</Button>
              </Dialog.Trigger>
              <Dialog.Portal>
                <Dialog.Overlay className="site-switcher-overlay" />
                <Dialog.Content className="site-switcher-dialog">
                  <Dialog.Title>Deactivate {item.user_account_id}?</Dialog.Title>
                  <Dialog.Description>
                    This preserves the membership row, history, role, and overrides. It
                    does not delete the user or membership.
                  </Dialog.Description>
                  <div className="admin-actions">
                    <Dialog.Close asChild>
                      <Button type="button">Cancel</Button>
                    </Dialog.Close>
                    <Button
                      type="button"
                      disabled={busy}
                      onClick={() =>
                        mutate(
                          () =>
                            deactivateMembership(
                              data.authority.site_id,
                              item.user_account_id,
                              item.version,
                            ),
                          "Membership deactivated.",
                        )
                      }
                    >
                      Confirm deactivation
                    </Button>
                  </div>
                </Dialog.Content>
              </Dialog.Portal>
            </Dialog.Root>
          )}
        </div>
      )}
      {self && (
        <p>
          Current account: self-mutation controls are not presented; the server also
          denies self-change.
        </p>
      )}
    </li>
  );
}

export function MembershipWorkflow({ siteId }: { siteId: string }) {
  const [data, setData] = useState<Data | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const pending = useRef(false);
  const sequence = useRef(0);
  const errorRef = useRef<HTMLDivElement>(null);
  async function refresh() {
    const current = ++sequence.current;
    const loaded = await loadMembershipAdministration(siteId);
    if (current === sequence.current) setData(loaded);
  }
  useEffect(() => {
    void refresh().catch((reason) => setError(failure(reason)));
  }, [siteId]);
  useEffect(() => {
    if (error) errorRef.current?.focus();
  }, [error]);
  async function mutate(operation: () => Promise<unknown>, success: string) {
    if (pending.current) return;
    pending.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await operation();
      await refresh();
      setNotice(success);
    } catch (reason) {
      setError(failure(reason));
      if (reason instanceof Error && reason.message === "conflict") void refresh();
    } finally {
      pending.current = false;
      setBusy(false);
    }
  }
  if (!data)
    return (
      <main className="admin-main">
        <h1>Memberships</h1>
        {error ? (
          <div ref={errorRef} tabIndex={-1}>
            <StatusPanel>{error}</StatusPanel>
          </div>
        ) : (
          <p>Loading roles, permissions, and memberships…</p>
        )}
      </main>
    );
  const canManage =
    data.authority.platform_administrator ||
    (data.authority.effective_permissions.includes("membership:manage") &&
      data.authority.effective_permissions.includes("role:manage"));
  return (
    <main className="admin-main">
      <h1>{data.authority.display_name} memberships</h1>
      <p>
        <a href={`/admin/sites/${siteId}`}>Back to site overview</a>
      </p>
      <p>
        Manage existing user UUIDs only. This creates no user, invitation, email,
        password, or login.
      </p>
      {error && (
        <div ref={errorRef} tabIndex={-1}>
          <StatusPanel>{error}</StatusPanel>
        </div>
      )}
      {notice && <StatusPanel>{notice}</StatusPanel>}
      {!canManage && (
        <StatusPanel>
          Read-only: both membership and role management permissions are required.
        </StatusPanel>
      )}
      {canManage && (
        <Card>
          <h2>Add existing user</h2>
          <AddMembershipEditor data={data} busy={busy} mutate={mutate} />
        </Card>
      )}
      <section>
        <h2>Current membership records</h2>
        {data.memberships.length ? (
          <ul className="membership-list">
            {data.memberships.map((item) => (
              <MembershipCard
                key={item.user_account_id}
                item={item}
                data={data}
                canManage={canManage}
                busy={busy}
                mutate={(operation, success) => void mutate(operation, success)}
              />
            ))}
          </ul>
        ) : (
          <StatusPanel>No membership rows exist for this site.</StatusPanel>
        )}
      </section>
    </main>
  );
}

function AddMembershipEditor({
  data,
  busy,
  mutate,
}: {
  data: Data;
  busy: boolean;
  mutate: (operation: () => Promise<unknown>, success: string) => Promise<void>;
}) {
  const [target, setTarget] = useState("");
  const [invalid, setInvalid] = useState(false);
  return (
    <div className="add-membership">
      <label>
        Existing user UUID
        <input
          value={target}
          onChange={(event) => {
            setTarget(event.target.value);
            setInvalid(false);
          }}
          required
          pattern="[0-9a-fA-F-]{36}"
          autoComplete="off"
          aria-describedby="existing-user-help"
        />
      </label>
      <p id="existing-user-help">
        The UUID must already belong to a provisioned account; no invitation or login is
        created.
      </p>
      {invalid && <StatusPanel>Enter a valid existing user UUID.</StatusPanel>}
      <MembershipForm
        roles={data.roles}
        permissions={data.permissions}
        label={busy ? "Adding…" : "Add membership"}
        disabled={busy}
        onSubmit={(body) => {
          if (!UUID.test(target)) {
            setInvalid(true);
            return;
          }
          void mutate(
            () => createMembership(data.authority.site_id, target, body),
            "Membership added.",
          );
        }}
      />
    </div>
  );
}
