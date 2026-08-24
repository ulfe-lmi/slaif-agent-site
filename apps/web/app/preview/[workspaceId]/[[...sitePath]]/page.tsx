import { cookies, headers } from "next/headers";
import { notFound, redirect } from "next/navigation";

import { resolvePreviewPage } from "../../../../src/sites/render";
import { PageProjectionShell } from "../../../../src/sites/shell";

export const dynamic = "force-dynamic";

export default async function WorkspacePreview({
  params,
}: Readonly<{
  params: Promise<{ workspaceId: string; sitePath?: string[] }>;
}>) {
  const [{ workspaceId, sitePath }, requestHeaders, requestCookies] = await Promise.all(
    [params, headers(), cookies()],
  );
  const session =
    requestCookies.get("__Host-slaif_session")?.value ??
    requestCookies.get("slaif_session")?.value;
  if (!session) redirect("/login");
  if (!/^[0-9a-f-]{36}$/i.test(workspaceId)) notFound();
  const path = `/${(sitePath ?? []).join("/")}`;
  const projection = await resolvePreviewPage(
    requestHeaders.get("host") ?? "",
    path,
    workspaceId,
    session,
  );
  if (!projection) notFound();
  return <PageProjectionShell projection={projection} />;
}
