"use client";

import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { StatusPanel } from "../components/ui/primitives";
import type { ReviewDocument } from "../sites/review-projection";
import { acceptWorkspace } from "./api";
import { CspModal } from "./csp-modal";

/**
 * 083/1 real human accept (R4). The control is present ONLY when the read
 * model reports status='REVIEW' with a COMPLETE snapshot and no canonical
 * drift; the server-side checks (R3.2.4) remain the authority.  The
 * confirmation dialog requires the summary acknowledgement; after the 202
 * the existing workspace read route is polled and the transient/terminal
 * states render with stable human-facing text.  No discard control exists.
 */

const POLL_INTERVAL_MS = 2000;
const POLL_LIMIT = 90;

function shortDigest(digest: string): string {
  return `${digest.slice(0, 12)}…${digest.slice(-8)}`;
}

const TRANSIENT_STATUS: Record<string, string> = {
  ACCEPT_QUEUED: "Acceptance queued — the review worker is preparing the promotion.",
  PROMOTING: "Promotion in progress — the canonical content is being committed.",
};

const TERMINAL_STATUS: Record<string, string> = {
  ACCEPTED: "Accepted — the canonical content now matches the frozen snapshot.",
  CONFLICTED:
    "Promotion conflict: the canonical content changed while the promotion was in flight. Re-review is required: freeze a new snapshot and accept again.",
};

export function AcceptAction({
  siteId,
  workspaceId,
  document,
}: {
  siteId: string;
  workspaceId: string;
  document: ReviewDocument;
}) {
  const status = document.metadata.workspace.status;
  const snapshot = document.snapshot;
  const digest = snapshot.digest;
  const [ack, setAck] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [observed, setObserved] = useState<string | null>(null);
  const pollTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const cancelledRef = useRef(false);

  useEffect(() => {
    cancelledRef.current = false;
    return () => {
      cancelledRef.current = true;
      if (pollTimerRef.current !== null) clearTimeout(pollTimerRef.current);
    };
  }, []);

  const pollWorkspace = useCallback(
    async (remaining: number) => {
      if (cancelledRef.current || remaining <= 0) {
        setObserved((current) => current ?? "POLL_TIMEOUT");
        return;
      }
      await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
      if (cancelledRef.current) return;
      try {
        const response = await fetch(
          `/api/control/v1/sites/${encodeURIComponent(siteId)}/workspaces/${encodeURIComponent(
            workspaceId,
          )}`,
          { method: "GET", credentials: "same-origin" },
        );
        if (response.ok) {
          const body = (await response.json()) as { status?: string };
          const next = typeof body.status === "string" ? body.status : null;
          if (
            next !== null &&
            (next in TERMINAL_STATUS || next === "REVIEW" || next === "POLL_TIMEOUT")
          ) {
            setObserved(next);
            return;
          }
          if (next !== null) setObserved(next);
        }
      } catch {
        // Keep polling; the read route may be transiently unavailable.
      }
      pollTimerRef.current = setTimeout(
        () => void pollWorkspace(remaining - 1),
        POLL_INTERVAL_MS,
      );
    },
    [siteId, workspaceId],
  );

  const submit = useCallback(async () => {
    if (!ack || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      await acceptWorkspace(siteId, workspaceId, {
        snapshot_id: snapshot.id,
        digest,
        acknowledge_summary: true,
      });
      // The observed state replaces the dialog subtree (CspModal is
      // unmounted); no separate close step is needed.
      setObserved("ACCEPT_QUEUED");
      void pollWorkspace(POLL_LIMIT);
    } catch {
      setError(
        "The accept request was rejected. The workspace is unchanged; retry from this page.",
      );
    } finally {
      setSubmitting(false);
    }
  }, [ack, submitting, siteId, workspaceId, snapshot.id, digest, pollWorkspace]);

  const canAccept =
    status === "REVIEW" &&
    snapshot.status === "COMPLETE" &&
    document.drift.equal === true;

  if (canAccept) {
    const polling = observed !== null;
    return (
      <div className="review-accept">
        {/*
         * CspModal (Radix with modal=false): the app's CSP-safe dialog.
         * A modal Radix Dialog creates inline-styled focus guards that
         * the strict style-src 'self' policy blocks; the site switcher
         * and membership dialogs use the same CspModal pattern.
         */}
        <CspModal
          contentClassName="site-switcher-dialog review-accept-dialog"
          title="Accept this snapshot?"
          description="The frozen snapshot becomes the canonical content of this site. This is a human-governed publication."
          trigger={
            <button
              className="review-action-primary"
              disabled={submitting}
              onClick={() => setAck(false)}
            >
              Accept snapshot
            </button>
          }
        >
          {({ close }) => (
            <>
              <p>
                Snapshot digest: <code title={digest}>{shortDigest(digest)}</code>
              </p>
              <label className="review-accept-ack">
                <input
                  type="checkbox"
                  checked={ack}
                  disabled={submitting}
                  onChange={(event) => setAck(event.target.checked)}
                />
                I have reviewed the frozen snapshot summary and acknowledge that
                accepting publishes it as the canonical site content.
              </label>
              {error !== null ? (
                <p role="alert" className="review-accept-error">
                  {error}
                </p>
              ) : null}
              <div className="review-accept-actions">
                <button
                  type="button"
                  disabled={submitting}
                  onClick={() => {
                    setAck(false);
                    close();
                  }}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  className="review-action-primary"
                  disabled={!ack || submitting}
                  onClick={() => void submit()}
                >
                  {submitting ? "Submitting…" : "Accept"}
                </button>
              </div>
            </>
          )}
        </CspModal>
        {polling ? <AcceptStatusPanel observed={observed ?? "ACCEPT_QUEUED"} /> : null}
      </div>
    );
  }

  if (status in TRANSIENT_STATUS || status in TERMINAL_STATUS) {
    return <AcceptStatusPanel observed={status} />;
  }

  // REVIEW with drift (or any other state): the re-review message renders
  // instead of the control (the drift banner carries the detail).
  return null;
}

function AcceptStatusPanel({ observed }: { observed: string }): ReactNode {
  if (observed === "POLL_TIMEOUT" || observed === "REVIEW") {
    return (
      <StatusPanel>
        {observed === "REVIEW"
          ? "The acceptance did not complete and the workspace is back in review. Re-freeze and accept again."
          : "Still working — reload the page to see the current state."}
      </StatusPanel>
    );
  }
  return (
    <StatusPanel>
      <span role="status">
        {TRANSIENT_STATUS[observed] ?? TERMINAL_STATUS[observed] ?? observed}
      </span>
    </StatusPanel>
  );
}

export { shortDigest as acceptShortDigest };
