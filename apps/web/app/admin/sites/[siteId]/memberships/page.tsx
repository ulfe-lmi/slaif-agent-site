import { MembershipWorkflow } from "../../../../../src/admin/membership-workflows";
import { AdminShell } from "../../../../../src/admin/shell";

export default async function MembershipPage({
  params,
}: {
  params: Promise<{ siteId: string }>;
}) {
  const { siteId } = await params;
  return (
    <AdminShell selectedSiteId={siteId}>
      <MembershipWorkflow siteId={siteId} />
    </AdminShell>
  );
}
