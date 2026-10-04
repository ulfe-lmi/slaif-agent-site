"use client";

import { useEffect, useState } from "react";

import { Card, StatusPanel } from "../components/ui/primitives";
import {
  getAgentWorkspace,
  listEditorPages,
  setEditorWorkspace,
  type EditorPageRecord,
} from "./api";

export function AgentWorkspaceEditorLanding({
  siteId,
  workspaceId,
}: {
  siteId: string;
  workspaceId: string;
}) {
  const [title, setTitle] = useState<string | null>(null);
  const [pages, setPages] = useState<EditorPageRecord[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setEditorWorkspace(workspaceId);
    let cancelled = false;
    async function load() {
      try {
        const [workspace, loadedPages] = await Promise.all([
          getAgentWorkspace(siteId, workspaceId),
          listEditorPages(siteId),
        ]);
        if (cancelled) return;
        setTitle(workspace.title);
        setPages(loadedPages);
      } catch {
        if (!cancelled) setError("This Agent workspace is not available for editing.");
      }
    }
    void load();
    return () => {
      cancelled = true;
      setEditorWorkspace(null);
    };
  }, [siteId, workspaceId]);

  return (
    <section
      className="agent-workspace-landing"
      aria-labelledby="agent-workspace-landing-title"
    >
      <p className="eyebrow">Trusted visual editor</p>
      <h1 id="agent-workspace-landing-title">
        Agent workspace{title ? `: ${title}` : ""}
      </h1>
      <span className="agent-workspace-banner__marker">Agent workspace</span>
      <p>
        Select the page to open in Puck. You are editing the exact Agent workspace;
        saving stores the workspace/draft and never publishes.
      </p>
      {error && <StatusPanel>{error}</StatusPanel>}
      {!error && (
        <Card>
          {pages === null ? (
            <p>Loading the Agent workspace pages…</p>
          ) : pages.length ? (
            <ul>
              {pages.map((page) => (
                <li key={page.id}>
                  <a
                    className="agent-workspace-page"
                    href={`/admin/sites/${siteId}/pages/${page.id}/edit?workspace=${workspaceId}&workspaceTitle=${encodeURIComponent(
                      title ?? "",
                    )}`}
                  >
                    <strong>{page.title}</strong> <code>{page.slug}</code> — Edit in
                    Puck
                  </a>
                </li>
              ))}
            </ul>
          ) : (
            <p>This Agent workspace has no pages yet.</p>
          )}
        </Card>
      )}
    </section>
  );
}
