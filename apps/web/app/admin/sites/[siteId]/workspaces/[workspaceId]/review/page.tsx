import { cookies } from "next/headers";
import { notFound } from "next/navigation";

import { AdminShell } from "../../../../../../../src/admin/shell";
import { WorkspaceReviewView } from "../../../../../../../src/admin/workspace-review";
import { fetchReviewDocument } from "../../../../../../../src/sites/review-page";

const WORKSPACE_UUID =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export default async function WorkspaceReviewPage({
  params,
}: {
  params: Promise<{ siteId: string; workspaceId: string }>;
}) {
  const { siteId, workspaceId } = await params;
  if (!WORKSPACE_UUID.test(workspaceId)) notFound();
  const cookieStore = await cookies();
  const sessionCookie =
    cookieStore.get("__Host-slaif_session") ?? cookieStore.get("slaif_session");
  const document = await fetchReviewDocument(
    workspaceId,
    sessionCookie ? { name: sessionCookie.name, value: sessionCookie.value } : null,
  );
  return (
    <AdminShell selectedSiteId={siteId}>
      <WorkspaceReviewView
        siteId={siteId}
        workspaceId={workspaceId}
        document={document}
      />
    </AdminShell>
  );
}
