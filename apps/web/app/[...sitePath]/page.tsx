import { headers } from "next/headers";
import { notFound } from "next/navigation";

import { resolveCanonicalPage, resolveSiteContext } from "../../src/sites/render";
import { PageProjectionShell, SiteContextShell } from "../../src/sites/shell";

export const dynamic = "force-dynamic";

export default async function SiteShell({
  params,
}: Readonly<{ params: Promise<{ sitePath: string[] }> }>) {
  const [{ sitePath }, requestHeaders] = await Promise.all([params, headers()]);
  const authority = requestHeaders.get("host") ?? "";
  const path = `/${sitePath.join("/")}`;
  const projection = await resolveCanonicalPage(authority, path);
  if (!projection) {
    const context = await resolveSiteContext(authority, path);
    if (!context) notFound();
    return <SiteContextShell context={context} />;
  }

  return <PageProjectionShell projection={projection} />;
}
