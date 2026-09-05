import { cookies, headers } from "next/headers";
import { notFound, redirect } from "next/navigation";
import { normalizeBrowserPreviewRoute } from "@slaif-agent-site/browser-tool-contracts";

import {
  isRedirectProjection,
  redirectProjection,
  resolvePreviewPage,
} from "../../../../src/sites/render";
import { PageProjectionShell } from "../../../../src/sites/shell";

export const dynamic = "force-dynamic";

export default async function WorkspacePreview({
  params,
  searchParams,
}: Readonly<{
  params: Promise<{ workspaceId: string; sitePath?: string[] }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}>) {
  const [{ workspaceId, sitePath }, query, requestHeaders, requestCookies] =
    await Promise.all([params, searchParams, headers(), cookies()]);
  const session =
    requestCookies.get("__Host-slaif_session")?.value ??
    requestCookies.get("slaif_session")?.value;
  const browserToken = requestHeaders.get("x-slaif-browser-preview");
  if (session && browserToken) notFound();
  if (!session && !browserToken) redirect("/login");
  if (
    browserToken &&
    (browserToken.length > 4096 || !/^sbp1(?:\.[A-Za-z0-9_-]+){3}$/u.test(browserToken))
  )
    notFound();
  if (!/^[0-9a-f-]{36}$/i.test(workspaceId)) notFound();
  const path = `/${(sitePath ?? []).join("/")}`;
  const queryEntries = Object.entries(query)
    .flatMap(([key, value]) =>
      Array.isArray(value)
        ? value.map((item) => [key, item] as const)
        : value === undefined
          ? []
          : ([[key, value]] as const),
    )
    .sort(([leftKey, leftValue], [rightKey, rightValue]) =>
      leftKey === rightKey
        ? leftValue.localeCompare(rightValue)
        : leftKey.localeCompare(rightKey),
    );
  const encoded = (value: string) =>
    encodeURIComponent(value)
      .replace(
        /[!'()*]/gu,
        (character) => `%${character.codePointAt(0)?.toString(16).toUpperCase() ?? ""}`,
      )
      .replace(/%20/gu, "+");
  const normalizedQuery = queryEntries
    .map(([key, value]) => `${encoded(key)}=${encoded(value)}`)
    .join("&");
  const browserRoute = normalizeBrowserPreviewRoute(
    normalizedQuery ? `${path}?${normalizedQuery}` : path,
  );
  const browserAuthority = process.env.SLAIF_BROWSER_PREVIEW_AUTHORITY;
  if (
    browserToken &&
    (!browserAuthority || !/^[a-z0-9.-]+(?::[1-9][0-9]{0,4})?$/u.test(browserAuthority))
  )
    notFound();
  const projection = await resolvePreviewPage(
    browserToken ? browserAuthority! : (requestHeaders.get("host") ?? ""),
    browserRoute.split("?", 1)[0] ?? browserRoute,
    workspaceId,
    browserToken ? { browserToken, browserRoute } : { humanSessionToken: session! },
  );
  if (!projection) notFound();
  if (isRedirectProjection(projection)) redirectProjection(projection);
  return <PageProjectionShell projection={projection} />;
}
