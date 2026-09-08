import { cookies, headers } from "next/headers";
import { notFound, redirect } from "next/navigation";
import { normalizeBrowserPreviewRoute } from "@slaif-agent-site/browser-tool-contracts";

import {
  isRedirectProjection,
  redirectProjection,
  resolvePreviewPage,
  type PageProjection,
  type RedirectProjection,
} from "./render";
import { PageProjectionShell } from "./shell";

type PreviewQuery = Record<string, string | string[] | undefined>;
type PreviewRequestContext = {
  requestHeaders: { get(name: string): string | null };
  session: string | undefined;
  browserToken: string | null;
};

export type WorkspacePreviewResolution =
  | { kind: "login" }
  | { kind: "not_found" }
  | { kind: "page"; projection: PageProjection }
  | { kind: "redirect"; projection: RedirectProjection };

export async function resolveWorkspacePreview(
  workspaceId: string,
  sitePath: string[] | undefined,
  query: PreviewQuery,
  requestContext?: PreviewRequestContext,
): Promise<WorkspacePreviewResolution> {
  const [requestHeaders, requestCookies] = requestContext
    ? [requestContext.requestHeaders, null]
    : await Promise.all([headers(), cookies()]);
  const session =
    requestContext?.session ??
    requestCookies?.get("__Host-slaif_session")?.value ??
    requestCookies?.get("slaif_session")?.value;
  const browserToken =
    requestContext?.browserToken ?? requestHeaders.get("x-slaif-browser-preview");
  if (session && browserToken) return { kind: "not_found" };
  if (!session && !browserToken) return { kind: "login" };
  if (
    browserToken &&
    (browserToken.length > 4096 || !/^sbp1(?:\.[A-Za-z0-9_-]+){3}$/u.test(browserToken))
  )
    return { kind: "not_found" };
  if (!/^[0-9a-f-]{36}$/i.test(workspaceId)) return { kind: "not_found" };
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
    return { kind: "not_found" };
  const projection = await resolvePreviewPage(
    browserToken ? browserAuthority! : (requestHeaders.get("host") ?? ""),
    browserRoute.split("?", 1)[0] ?? browserRoute,
    workspaceId,
    browserToken ? { browserToken, browserRoute } : { humanSessionToken: session! },
  );
  if (!projection) return { kind: "not_found" };
  if (isRedirectProjection(projection)) return { kind: "redirect", projection };
  return { kind: "page", projection };
}

export async function renderWorkspacePreview(
  workspaceId: string,
  sitePath: string[] | undefined,
  query: PreviewQuery,
) {
  const resolution = await resolveWorkspacePreview(workspaceId, sitePath, query);
  if (resolution.kind === "login") redirect("/login");
  if (resolution.kind === "not_found") notFound();
  if (resolution.kind === "redirect") redirectProjection(resolution.projection);
  return <PageProjectionShell projection={resolution.projection} />;
}
