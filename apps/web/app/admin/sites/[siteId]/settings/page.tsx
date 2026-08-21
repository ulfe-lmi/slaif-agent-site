import { SiteSettingsWorkflow } from "../../../../../src/admin/site-workflows";

export default async function SiteSettingsPage({
  params,
}: {
  params: Promise<{ siteId: string }>;
}) {
  const { siteId } = await params;
  return (
    <main className="admin-main">
      <SiteSettingsWorkflow siteId={siteId} />
    </main>
  );
}
