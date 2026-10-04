import { notFound } from "next/navigation";

import { AdminShell } from "../../../../../../../src/admin/shell";
import { AgentWorkspaceEditorLanding } from "../../../../../../../src/admin/workspace-editor-landing";

const WORKSPACE_UUID =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export default async function AgentWorkspaceEditorPage({
  params,
}: {
  params: Promise<{ siteId: string; workspaceId: string }>;
}) {
  const { siteId, workspaceId } = await params;
  if (!WORKSPACE_UUID.test(workspaceId)) notFound();
  return (
    <AdminShell selectedSiteId={siteId}>
      <AgentWorkspaceEditorLanding siteId={siteId} workspaceId={workspaceId} />
    </AdminShell>
  );
}
