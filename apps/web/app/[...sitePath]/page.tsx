import { headers } from "next/headers";
import { notFound } from "next/navigation";

import { resolveSiteContext } from "../../src/sites/render";
import { SiteContextShell } from "../../src/sites/shell";

export const dynamic = "force-dynamic";

export default async function SiteShell({
  params,
}: Readonly<{ params: Promise<{ sitePath: string[] }> }>) {
  const [{ sitePath }, requestHeaders] = await Promise.all([params, headers()]);
  const authority = requestHeaders.get("host") ?? "";
  const path = `/${sitePath.join("/")}`;
  const context = await resolveSiteContext(authority, path);
  if (!context) notFound();

  return <SiteContextShell context={context} />;
}
