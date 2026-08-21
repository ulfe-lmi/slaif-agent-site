import { SiteSettingsWorkflow } from "../../../../../src/admin/site-workflows";
import { AdminShell } from "../../../../../src/admin/shell";

export default async function SiteSettingsPage({
  params,
}: {
  params: Promise<{ siteId: string }>;
}) {
  const { siteId } = await params;
  return (
    <AdminShell selectedSiteId={siteId}>
      <SiteSettingsWorkflow siteId={siteId} />
    </AdminShell>
  );
}
