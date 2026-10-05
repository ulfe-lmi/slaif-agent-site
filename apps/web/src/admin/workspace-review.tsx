import type { ReactNode } from "react";
import type { ReviewDocument } from "../sites/review-projection";
import { Card, StatusBadge, StatusPanel } from "../components/ui/primitives";
import { AcceptAction } from "./accept-action";

/**
 * 082/2 human review surface + 083/1 real accept action. Every value is
 * rendered from the trusted read-model document; the only action control
 * is the accept control (present only for REVIEW + COMPLETE snapshot + no
 * drift) — no discard, no Puck launch, no publish shortcut. The top-N
 * bound keeps the resource-diff rendering finite while the exact counts
 * stay visible.
 */

const DIFF_TOP_N = 10;
const FIELD_PREVIEW_BYTES = 256;

type FamilyDiff = {
  added: readonly unknown[];
  modified: readonly {
    id: string;
    fields: Record<string, { before: unknown; after: unknown }>;
  }[];
  deleted: readonly unknown[];
};

const FAMILY_LABELS: Record<string, string> = {
  pages: "Pages",
  composition_nodes: "Composition nodes",
  items: "Items",
  fields: "Fields",
  content_types: "Content types",
  translations: "Translations",
  relations: "Relations",
  collection_views: "Collection views",
  theme: "Theme",
  navigation: "Navigation",
  navigation_items: "Navigation items",
  redirects: "Redirects",
  media_assets: "Media assets",
  global_regions: "Global regions",
  locales: "Locales",
  proposed_side_effects: "Proposed side effects",
};

const FAMILY_ORDER = Object.keys(FAMILY_LABELS);

function previewValue(value: unknown): string {
  let text: string;
  try {
    text = typeof value === "string" ? value : JSON.stringify(value);
  } catch {
    text = String(value);
  }
  if (text.length > FIELD_PREVIEW_BYTES) {
    text = `${text.slice(0, FIELD_PREVIEW_BYTES)}…`;
  }
  return text;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function Section({
  id,
  title,
  children,
}: {
  id: string;
  title: string;
  children: ReactNode;
}) {
  return (
    <section aria-labelledby={id} className="review-section">
      <h2 id={id}>{title}</h2>
      {children}
    </section>
  );
}

function SummaryList({ entries }: { entries: [string, ReactNode][] }) {
  return (
    <dl className="review-summary-list">
      {entries.map(([label, value]) => (
        <div key={label}>
          <dt>{label}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}

function objectEntries(value: unknown): [string, unknown][] {
  if (!isRecord(value)) return [];
  return Object.entries(value).sort(([a], [b]) => a.localeCompare(b));
}

function summarizeUnknown(value: unknown): ReactNode {
  if (value === null || value === undefined) return "—";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  if (Array.isArray(value)) return `${value.length} entries`;
  if (isRecord(value)) {
    return (
      <SummaryList
        entries={objectEntries(value).map(([key, item]) => [
          key,
          summarizeUnknown(item),
        ])}
      />
    );
  }
  if (typeof value === "bigint") return value.toString();
  if (typeof value === "symbol") return value.description ?? "symbol";
  return "[unsupported value]";
}

function SnapshotIdentity({ document }: { document: ReviewDocument }) {
  const snapshot = document.snapshot;
  return (
    <Card>
      <SummaryList
        entries={[
          ["Digest", <code key="d">{snapshot.digest}</code>],
          ["State version", snapshot.state_version],
          ["Status", snapshot.status],
          ["Revision watermark", String(snapshot.revision_watermark)],
          ["Base site revision", String(snapshot.base_site_revision)],
          ["Created at", snapshot.created_at],
          ["Created by", snapshot.created_by],
        ]}
      />
      <h3>Versions</h3>
      <SummaryList
        entries={objectEntries(snapshot.versions).map(([key, version]) => [
          key,
          String(version),
        ])}
      />
    </Card>
  );
}

function DriftBanner({ document }: { document: ReviewDocument }) {
  const drift = document.drift;
  return drift.equal ? (
    <StatusPanel>
      Canonical unchanged since freeze (revision {drift.current_site_revision}).
    </StatusPanel>
  ) : (
    <StatusPanel>
      Canonical drifted after freeze (base {drift.base_site_revision}, current{" "}
      {drift.current_site_revision}) — acceptance is blocked until re-freeze (enforced
      server-side); the frozen review remains visible.
    </StatusPanel>
  );
}

function TimelineSection({ document }: { document: ReviewDocument }) {
  if (document.timeline.length === 0) {
    return <p>No operations recorded for this frozen workspace.</p>;
  }
  return (
    <table className="review-table">
      <thead>
        <tr>
          <th scope="col">Operation</th>
          <th scope="col">Type</th>
          <th scope="col">Resources</th>
          <th scope="col">Created at</th>
        </tr>
      </thead>
      <tbody>
        {document.timeline.map((entry) => (
          <tr key={entry.operation_id}>
            <td>
              <code>{entry.operation_id}</code>
            </td>
            <td>{entry.operation_type}</td>
            <td>{entry.resource.join(", ") || "—"}</td>
            <td>{entry.created_at}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function ModifiedRow({ row }: { row: unknown }) {
  if (!isRecord(row) || !isRecord(row["fields"])) {
    return <>{previewValue(row)}</>;
  }
  const fields = row["fields"] as Record<string, { before: unknown; after: unknown }>;
  return (
    <>
      <code>{String(row["id"])}</code>:{" "}
      {Object.entries(fields)
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([field, change]) => (
          <span key={field} className="review-diff-field">
            {field}: {previewValue(change.before)} → {previewValue(change.after)}
          </span>
        ))}
    </>
  );
}

function DiffFamily({
  family,
  diff,
}: {
  family: string;
  diff: FamilyDiff | undefined;
}) {
  if (!diff) return null;
  const buckets: {
    name: "added" | "modified" | "deleted";
    rows: readonly unknown[];
  }[] = [
    { name: "added", rows: diff.added },
    { name: "modified", rows: diff.modified },
    { name: "deleted", rows: diff.deleted },
  ];
  const empty = buckets.every((bucket) => bucket.rows.length === 0);
  if (empty) return null;
  return (
    <div className="review-diff-family">
      <h3>
        {FAMILY_LABELS[family] ?? family}{" "}
        <small>
          (added {diff.added.length}, modified {diff.modified.length}, deleted{" "}
          {diff.deleted.length})
        </small>
      </h3>
      {buckets.map((bucket) =>
        bucket.rows.length === 0 ? null : (
          <div key={bucket.name}>
            <h4>
              {bucket.name}
              {bucket.rows.length > DIFF_TOP_N ? ` (showing first ${DIFF_TOP_N})` : ""}
            </h4>
            <ul>
              {bucket.rows.slice(0, DIFF_TOP_N).map((row, index) => (
                <li key={index}>
                  {bucket.name === "modified" ? (
                    <ModifiedRow row={row} />
                  ) : (
                    previewValue(row)
                  )}
                </li>
              ))}
            </ul>
          </div>
        ),
      )}
    </div>
  );
}

function ResourceDiffSection({ document }: { document: ReviewDocument }) {
  const families = FAMILY_ORDER.filter((family) =>
    isRecord(document.resource_diff)
      ? family in (document.resource_diff as Record<string, unknown>)
      : false,
  );
  const visible = families.filter((family) =>
    isRecord(document.resource_diff)
      ? ((document.resource_diff as Record<string, FamilyDiff>)[family] ?? {}).added
          ?.length !== 0 ||
        ((document.resource_diff as Record<string, FamilyDiff>)[family] ?? {}).modified
          ?.length !== 0 ||
        ((document.resource_diff as Record<string, FamilyDiff>)[family] ?? {}).deleted
          ?.length !== 0
      : false,
  );
  if (visible.length === 0) {
    return <p>No resource changes captured in this snapshot.</p>;
  }
  return (
    <div>
      {visible.map((family) => (
        <DiffFamily
          key={family}
          family={family}
          diff={(document.resource_diff as Record<string, FamilyDiff>)[family]}
        />
      ))}
      <p className="review-diff-note">
        Field-level diff is bounded to one level; values longer than{" "}
        {FIELD_PREVIEW_BYTES} characters are truncated.
      </p>
    </div>
  );
}

function SummariesSection({ document }: { document: ReviewDocument }) {
  const groups: [string, unknown][] = [
    ["Models", document.summaries["model"]],
    ["Fields", document.summaries["fields"]],
    ["Mappings", document.summaries["mappings"]],
    ["Items & relations", document.summaries["items"]],
    ["Resource inventory", document.summaries["resource_inventory"]],
    [
      "Composition by component type",
      document.summaries["composition_by_component_type"],
    ],
    ["Theme", document.summaries["theme"]],
    ["Navigation", document.summaries["navigation"]],
    ["Redirects", document.summaries["redirects"]],
    ["Media", document.summaries["media"]],
    ["Responsive", document.summaries["responsive"]],
  ];
  return (
    <div>
      {groups.map(([label, value]) => (
        <div key={label} className="review-summary-group">
          <h3>{label}</h3>
          {summarizeUnknown(value)}
        </div>
      ))}
    </div>
  );
}

function ValidationSection({ document }: { document: ReviewDocument }) {
  return (
    <div>
      <h3>Frozen validation report</h3>
      <pre className="review-validation-report">
        {JSON.stringify(document.validation.report, null, 2)}
      </pre>
      <h3>Warnings</h3>
      {document.validation.warnings.length === 0 ? (
        <p>No warnings.</p>
      ) : (
        <ul>
          {document.validation.warnings.map((warning, index) => (
            <li key={index}>{previewValue(warning)}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

function EvidenceSection({ document }: { document: ReviewDocument }) {
  if (document.evidence.runs.length === 0) {
    return <p>No browser runs captured in this snapshot.</p>;
  }
  return (
    <div>
      {document.evidence.artifacts.map((entry) => (
        <div key={entry.run_id} className="review-evidence-run">
          <h3>
            Run <code>{entry.run_id}</code>
          </h3>
          {entry.artifacts.length === 0 ? (
            <p>No private artifacts retained for this run.</p>
          ) : (
            <ul className="review-evidence-artifacts">
              {entry.artifacts.map((artifact) => (
                <li key={artifact.artifact_id}>
                  {artifact.kind === "screenshot" &&
                  artifact.mime_type === "image/png" ? (
                    <img
                      alt={`Frozen run ${entry.run_id} screenshot ${artifact.artifact_id}`}
                      className="review-evidence-thumbnail"
                      loading="lazy"
                      src={`/api/agent/v1/preview-runs/${entry.run_id}/artifacts/${artifact.artifact_id}`}
                    />
                  ) : null}{" "}
                  <a
                    href={`/api/agent/v1/preview-runs/${entry.run_id}/artifacts/${artifact.artifact_id}`}
                  >
                    {artifact.kind}
                  </a>{" "}
                  <small>{artifact.mime_type ?? "unknown type"}</small>
                </li>
              ))}
            </ul>
          )}
        </div>
      ))}
    </div>
  );
}

function MetadataSection({ document }: { document: ReviewDocument }) {
  const metadata = document.metadata;
  const revoked = metadata.capabilities.filter(
    (capability): capability is Record<string, unknown> =>
      isRecord(capability) && capability["revoked_at"] !== null,
  );
  return (
    <div>
      <h3>Workspace</h3>
      <SummaryList
        entries={[
          ["Title", metadata.workspace.title],
          ["Actor type", metadata.workspace.actor_type],
          ["Status", <StatusBadge key="s">{metadata.workspace.status}</StatusBadge>],
        ]}
      />
      <h3>Revoked capabilities after freeze</h3>
      {revoked.length === 0 ? (
        <p>No capability rows for this workspace.</p>
      ) : (
        <ul>
          {revoked.map((capability) => (
            <li key={String(capability["id"])}>
              <code>{String(capability["id"])}</code>{" "}
              {Array.isArray(capability["scopes"])
                ? (capability["scopes"] as string[]).join(", ")
                : ""}{" "}
              (revoked {String(capability["revoked_at"])})
            </li>
          ))}
        </ul>
      )}
      <h3>Quota policy</h3>
      {summarizeUnknown(metadata.quota_policy)}
      <h3>Agent, session, and browser metadata</h3>
      {summarizeUnknown(metadata.agent_session_browser)}
    </div>
  );
}

export function WorkspaceReviewView({
  siteId,
  workspaceId,
  document,
}: {
  siteId: string;
  workspaceId: string;
  document: ReviewDocument | null;
}) {
  if (!document) {
    return (
      <section aria-labelledby="workspace-review-title" className="review-surface">
        <h1 id="workspace-review-title">Workspace review</h1>
        <StatusPanel>
          This workspace has no frozen review snapshot available to you.
        </StatusPanel>
        <a href={`/admin/sites/${siteId}/workspaces/${workspaceId}/edit`}>
          Back to workspace
        </a>
      </section>
    );
  }
  return (
    <section aria-labelledby="workspace-review-title" className="review-surface">
      <h1 id="workspace-review-title">
        {document.metadata.workspace.title} — frozen review
      </h1>
      <p>
        Site {document.metadata.site.key} · workspace{" "}
        <StatusBadge>{document.metadata.workspace.status}</StatusBadge>
      </p>
      <div className="review-actions">
        <a className="review-action-primary" href={`/review/${workspaceId}/`}>
          View rendered site
        </a>{" "}
        <a href={`/admin/sites/${siteId}/workspaces/${workspaceId}/edit`}>
          Back to workspace
        </a>
      </div>
      <SnapshotIdentity document={document} />
      <DriftBanner document={document} />
      <AcceptAction siteId={siteId} workspaceId={workspaceId} document={document} />
      <Section id="review-timeline" title="Semantic timeline">
        <TimelineSection document={document} />
      </Section>
      <Section id="review-diff" title="Resource diff">
        <ResourceDiffSection document={document} />
      </Section>
      <Section id="review-summaries" title="Summaries">
        <SummariesSection document={document} />
      </Section>
      <Section id="review-validation" title="Validation">
        <ValidationSection document={document} />
      </Section>
      <Section id="review-evidence" title="Browser evidence">
        <EvidenceSection document={document} />
      </Section>
      <Section id="review-metadata" title="Metadata">
        <MetadataSection document={document} />
      </Section>
    </section>
  );
}
