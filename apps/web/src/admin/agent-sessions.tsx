"use client";

import { useEffect, useState } from "react";

import { Button, Card, StatusPanel } from "../components/ui/primitives";
import {
  createAgentCapability,
  createAgentWorkspace,
  listAgentCapabilities,
  listAgentWorkspaces,
  revokeAgentCapability,
  type AgentCapability,
  type AgentWorkspace,
} from "./api";

const PRESETS = [
  ["L1_CONTENT_EDITOR", "L1 · Content editor"],
  ["L2_SITE_EDITOR", "L2 · Site editor"],
  ["L3_SITE_DESIGNER", "L3 · Site designer"],
  ["L4_SITE_ARCHITECT", "L4 · Site architect"],
] as const;

export function AgentSessions({ siteId }: { siteId: string }) {
  const [title, setTitle] = useState("Editorial agent session");
  const [preset, setPreset] =
    useState<(typeof PRESETS)[number][0]>("L4_SITE_ARCHITECT");
  const [duration, setDuration] = useState(1);
  const [quota, setQuota] = useState(1000);
  const [origin, setOrigin] = useState("");
  const [constraints, setConstraints] = useState("");
  const [workspaces, setWorkspaces] = useState<AgentWorkspace[]>([]);
  const [capabilities, setCapabilities] = useState<Record<string, AgentCapability[]>>(
    {},
  );
  const [token, setToken] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    try {
      const items = await listAgentWorkspaces(siteId);
      setWorkspaces(items);
      const entries = await Promise.all(
        items.map(
          async (item) =>
            [
              item.workspace_id,
              await listAgentCapabilities(siteId, item.workspace_id),
            ] as const,
        ),
      );
      setCapabilities(Object.fromEntries(entries));
    } catch {
      setError("Session data is temporarily unavailable.");
    }
  }
  useEffect(() => {
    void refresh();
  }, [siteId]);

  async function create() {
    setError(null);
    setToken(null);
    try {
      const workspace = await createAgentWorkspace(siteId, {
        title,
        delegation_preset: preset,
        duration_hours: duration,
        request_quota: quota,
        source_origins: origin ? [origin] : [],
        resource_constraints: constraints
          ? (JSON.parse(constraints) as Record<string, unknown>)
          : {},
      });
      const capability = await createAgentCapability(siteId, workspace.workspace_id);
      setToken(capability.token ?? null);
      await refresh();
    } catch {
      setError("The Agent session could not be created.");
    }
  }
  async function revoke(workspaceId: string, capabilityId: string) {
    try {
      await revokeAgentCapability(siteId, workspaceId, capabilityId);
      await refresh();
    } catch {
      setError("The capability could not be revoked.");
    }
  }
  return (
    <section aria-labelledby="agent-sessions-heading" className="agent-sessions">
      <h2 id="agent-sessions-heading">AI Sessions</h2>
      <p>
        Create and monitor bounded site Agent workspaces. Secrets are displayed once.
      </p>
      {error && <StatusPanel>{error}</StatusPanel>}
      <Card>
        <label htmlFor="agent-session-title">Session title</label>
        <input
          id="agent-session-title"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          maxLength={128}
        />
        <label htmlFor="agent-session-preset">Delegation preset</label>
        <select
          id="agent-session-preset"
          value={preset}
          onChange={(event) =>
            setPreset(event.target.value as (typeof PRESETS)[number][0])
          }
        >
          {PRESETS.map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
        <label htmlFor="agent-session-duration">TTL (hours)</label>
        <input
          id="agent-session-duration"
          type="number"
          min={1}
          max={8}
          value={duration}
          onChange={(event) => setDuration(Number(event.target.value))}
        />
        <label htmlFor="agent-session-quota">Request quota</label>
        <input
          id="agent-session-quota"
          type="number"
          min={1}
          max={10000}
          value={quota}
          onChange={(event) => setQuota(Number(event.target.value))}
        />
        <details>
          <summary>Advanced source and resource restrictions</summary>
          <label htmlFor="agent-session-origin">Approved HTTP(S) origin</label>
          <input
            id="agent-session-origin"
            value={origin}
            onChange={(event) => setOrigin(event.target.value)}
            placeholder="https://example.com"
          />
          <label htmlFor="agent-session-constraints">Resource constraints (JSON)</label>
          <input
            id="agent-session-constraints"
            value={constraints}
            onChange={(event) => setConstraints(event.target.value)}
            placeholder='{"max_content_types":100}'
          />
        </details>
        <Button type="button" onClick={() => void create()}>
          Create Agent session
        </Button>
        {token && (
          <div className="one-time-secret" role="alert">
            <strong>Copy this token now; it will not be shown again.</strong>
            <code>{token}</code>
            <span>
              <Button
                type="button"
                onClick={() => void navigator.clipboard.writeText(token)}
              >
                Copy token
              </Button>{" "}
              <Button type="button" onClick={() => setToken(null)}>
                Dismiss
              </Button>
            </span>
          </div>
        )}
      </Card>
      <Card>
        <h3>Session status</h3>
        {workspaces.length ? (
          <ul>
            {workspaces.map((workspace) => (
              <li key={workspace.workspace_id}>
                <strong>{workspace.title}</strong> · {workspace.delegation_preset} ·{" "}
                {workspace.status} · expires{" "}
                {new Date(workspace.expires_at).toLocaleString()}
                <ul>
                  {(capabilities[workspace.workspace_id] ?? []).map((capability) => (
                    <li key={capability.capability_id}>
                      <code>{capability.capability_id}</code> ·{" "}
                      {capability.status ?? (capability.revoked ? "REVOKED" : "ACTIVE")}{" "}
                      {!capability.revoked && capability.status !== "EXPIRED" && (
                        <Button
                          type="button"
                          onClick={() =>
                            void revoke(
                              workspace.workspace_id,
                              capability.capability_id,
                            )
                          }
                        >
                          Revoke
                        </Button>
                      )}
                    </li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>
        ) : (
          <p>No Agent workspaces have been created.</p>
        )}
      </Card>
    </section>
  );
}
