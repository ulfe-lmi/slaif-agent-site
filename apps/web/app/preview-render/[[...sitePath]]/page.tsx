import { headers } from "next/headers";
import { notFound } from "next/navigation";

import { renderWorkspacePreview } from "../../../src/sites/preview-page";

export const dynamic = "force-dynamic";

export default async function InternalWorkspacePreview({
  params,
  searchParams,
}: Readonly<{
  params: Promise<{ sitePath?: string[] }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}>) {
  const [requestHeaders, { sitePath }, query] = await Promise.all([
    headers(),
    params,
    searchParams,
  ]);
  const workspaceId = requestHeaders.get("x-slaif-preview-workspace");
  if (!workspaceId || requestHeaders.get("x-slaif-internal-preview") !== "1") {
    notFound();
  }
  return renderWorkspacePreview(workspaceId, sitePath, query);
}
