import { renderWorkspacePreview } from "../../../../src/sites/preview-page";

export const dynamic = "force-dynamic";

export default async function WorkspacePreview({
  params,
  searchParams,
}: Readonly<{
  params: Promise<{ workspaceId: string; sitePath?: string[] }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}>) {
  const [{ workspaceId, sitePath }, query] = await Promise.all([params, searchParams]);
  return renderWorkspacePreview(workspaceId, sitePath, query);
}
