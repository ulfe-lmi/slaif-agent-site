import { AdminShell } from "../../../../../../../src/admin/shell";
import { CompositionEditor } from "../../../../../../../src/admin/composition-editor";

export default async function CompositionEditorPage({
  params,
}: {
  params: Promise<{ siteId: string; pageId: string }>;
}) {
  const { siteId, pageId } = await params;
  return (
    <AdminShell selectedSiteId={siteId}>
      <CompositionEditor siteId={siteId} pageId={pageId} />
    </AdminShell>
  );
}
