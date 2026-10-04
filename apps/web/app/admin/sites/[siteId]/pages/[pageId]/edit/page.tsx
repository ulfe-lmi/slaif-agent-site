import { AdminShell } from "../../../../../../../src/admin/shell";
import { CompositionEditor } from "../../../../../../../src/admin/composition-editor";

const WORKSPACE_UUID =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export default async function CompositionEditorPage({
  params,
  searchParams,
}: {
  params: Promise<{ siteId: string; pageId: string }>;
  searchParams: Promise<{ workspace?: string; workspaceTitle?: string }>;
}) {
  const [parsedParams, parsedSearch] = await Promise.all([params, searchParams]);
  const { siteId, pageId } = parsedParams;
  const workspaceId =
    typeof parsedSearch.workspace === "string" &&
    WORKSPACE_UUID.test(parsedSearch.workspace)
      ? parsedSearch.workspace
      : null;
  const workspaceTitle =
    workspaceId && typeof parsedSearch.workspaceTitle === "string"
      ? parsedSearch.workspaceTitle.slice(0, 128)
      : null;
  return (
    <AdminShell selectedSiteId={siteId}>
      <CompositionEditor
        siteId={siteId}
        pageId={pageId}
        workspaceId={workspaceId}
        workspaceTitle={workspaceTitle}
      />
    </AdminShell>
  );
}
