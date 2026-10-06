"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { StatusPanel } from "../components/ui/primitives";
import type { ReviewDocument } from "../sites/review-projection";
import { discardWorkspace } from "./api";
import { CspModal } from "./csp-modal";

/**
 * 083/2 real human discard (R4). The control is present ONLY when the
 * read model reports status REVIEW or CONFLICTED with a bound COMPLETE
 * snapshot; there is deliberately NO drift gate (discard is the drift
 * remedy). The server-side checks (R2) remain the authority. The
 * confirmation dialog requires the acknowledgement; after the 202 the
 * existing workspace read route is polled and the transient/terminal
 * states render with stable human-facing text.
 */

const POLL_INTERVAL_MS = 2000;
const POLL_LIMIT = 90;

const CONFLICT_BANNER =
  "Promotion conflict: the canonical content changed while the promotion was in flight. This workspace cannot be re-frozen in place (freeze is available only from ACTIVE). Available remedies: discard this workspace's pending work, or create a fresh workspace and re-apply the changes.";

const TRANSIENT_STATUS: Record<string, string> = {
  DISCARD_QUEUED:
    "Discard queued — the review worker is preparing to remove the pending work.",
  DISCARDING: "Discard in progress — the pending workspace work is being removed.",
};

const TERMINAL_STATUS: Record<string, string> = {
  DISCARDED:
    "Discarded — the pending workspace work has been removed. The canonical site content is unchanged.",
};

export function DiscardAction({
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
          if (next !== null && (next in TERMINAL_STATUS || next === "POLL_TIMEOUT")) {
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
      await discardWorkspace(siteId, workspaceId, {
        acknowledge_discard: true,
      });
      // The observed state replaces the dialog subtree (CspModal is
      // unmounted); no separate close step is needed.
      setObserved("DISCARD_QUEUED");
      void pollWorkspace(POLL_LIMIT);
    } catch {
      setError(
        "The discard request was rejected. The workspace is unchanged; retry from this page.",
      );
    } finally {
      setSubmitting(false);
    }
  }, [ack, submitting, siteId, workspaceId, pollWorkspace]);

  const canDiscard =
    (status === "REVIEW" || status === "CONFLICTED") && snapshot.status === "COMPLETE";

  if (canDiscard) {
    const polling = observed !== null;
    return (
      <div className="review-discard">
        {status === "CONFLICTED" ? (
          <StatusPanel>
            <p className="review-conflict-banner">{CONFLICT_BANNER}</p>
          </StatusPanel>
        ) : null}
        <CspModal
          contentClassName="site-switcher-dialog review-discard-dialog"
          title="Discard this workspace's pending work?"
          description="The pending (unpublished) work is removed permanently. The canonical site content is untouched."
          trigger={
            <button
              className="review-action-secondary"
              disabled={submitting}
              onClick={() => setAck(false)}
            >
              Discard pending work
            </button>
          }
        >
          {({ close }) => (
            <>
              <p>
                The frozen review and every pending change in this workspace will be
                discarded. This cannot be undone from this workspace.
              </p>
              <label className="review-discard-ack">
                <input
                  type="checkbox"
                  checked={ack}
                  disabled={submitting}
                  onChange={(event) => setAck(event.target.checked)}
                />
                I understand that discarding deletes the pending workspace work and that
                the canonical site content is untouched.
              </label>
              {error !== null ? (
                <p role="alert" className="review-discard-error">
                  {error}
                </p>
              ) : null}
              <div className="review-discard-actions">
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
                  className="review-action-secondary"
                  disabled={!ack || submitting}
                  onClick={() => void submit()}
                >
                  {submitting ? "Submitting…" : "Discard"}
                </button>
              </div>
            </>
          )}
        </CspModal>
        {polling ? (
          <DiscardStatusPanel observed={observed ?? "DISCARD_QUEUED"} />
        ) : null}
      </div>
    );
  }

  if (status in TRANSIENT_STATUS || status in TERMINAL_STATUS) {
    return <DiscardStatusPanel observed={status} />;
  }

  // Any other state (ACTIVE, ACCEPTED, FREEZING, ACCEPT_QUEUED,
  // PROMOTING, ...): no discard control.
  return null;
}

function DiscardStatusPanel({ observed }: { observed: string }) {
  if (observed === "POLL_TIMEOUT") {
    return (
      <StatusPanel>
        Still working — reload the page to see the current state.
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
