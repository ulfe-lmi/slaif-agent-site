import { AdminShell } from "../../../../src/admin/shell";

export default async function AdminSitePage({
  params,
}: {
  params: Promise<{ siteId: string }>;
}) {
  const { siteId } = await params;
  return <AdminShell selectedSiteId={siteId} />;
}
