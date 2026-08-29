"use client";

import { useEffect, useState } from "react";
import { Button, Card, StatusPanel } from "../components/ui/primitives";
import {
  createAgentCapability,
  createAgentWorkspace,
  listAgentCapabilities,
  revokeAgentCapability,
  type AgentCapability,
} from "./api";

export function AgentSessions({ siteId }: { siteId: string }) {
  const [title, setTitle] = useState("Editorial agent session");
  const [workspaceId, setWorkspaceId] = useState<string | null>(null);
  const [capabilities, setCapabilities] = useState<AgentCapability[]>([]);
  const [token, setToken] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  async function refresh(id = workspaceId) {
    if (!id) return;
    try {
      setCapabilities(await listAgentCapabilities(siteId, id));
    } catch {
      setError("Session data is temporarily unavailable.");
    }
  }
  useEffect(() => {
    void refresh();
  }, [workspaceId]);
  async function create() {
    setError(null);
    setToken(null);
    try {
      const workspace = await createAgentWorkspace(siteId, {
        title,
        delegation_preset: "L4_SITE_ARCHITECT",
        duration_hours: 1,
      });
      setWorkspaceId(workspace.workspace_id);
      const capability = await createAgentCapability(siteId, workspace.workspace_id);
      setToken(capability.token ?? null);
      await refresh(workspace.workspace_id);
    } catch {
      setError("The Agent session could not be created.");
    }
  }
  async function revoke(id: string) {
    if (!workspaceId) return;
    try {
      await revokeAgentCapability(siteId, workspaceId, id);
      await refresh();
    } catch {
      setError("The capability could not be revoked.");
    }
  }
  return (
    <section aria-labelledby="agent-sessions-heading" className="agent-sessions">
      <h2 id="agent-sessions-heading">AI Sessions</h2>
      <p>
        Create a bounded site Agent workspace. The capability secret is displayed once.
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
        <p>Level 4 Site Architect · one hour · site-bound</p>
        <Button type="button" onClick={() => void create()}>
          Create Agent session
        </Button>
        {token && (
          <div className="one-time-secret" role="alert">
            <strong>Copy this token now; it will not be shown again.</strong>
            <code>{token}</code>
          </div>
        )}
      </Card>
      {workspaceId && (
        <Card>
          <h3>Capabilities</h3>
          {capabilities.length ? (
            <ul>
              {capabilities.map((capability) => (
                <li key={capability.capability_id}>
                  <code>{capability.capability_id}</code> ·{" "}
                  {capability.revoked ? "revoked" : "active"}{" "}
                  {!capability.revoked && (
                    <Button
                      type="button"
                      onClick={() => void revoke(capability.capability_id)}
                    >
                      Revoke
                    </Button>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p>No capabilities issued.</p>
          )}
        </Card>
      )}
    </section>
  );
}
