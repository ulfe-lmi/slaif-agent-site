import { MembershipWorkflow } from "../../../../../src/admin/membership-workflows";

export default async function MembershipPage({
  params,
}: {
  params: Promise<{ siteId: string }>;
}) {
  const { siteId } = await params;
  return <MembershipWorkflow siteId={siteId} />;
}
