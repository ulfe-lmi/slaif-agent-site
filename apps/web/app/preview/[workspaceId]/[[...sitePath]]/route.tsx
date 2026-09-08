import { renderToReadableStream } from "react-dom/server.edge";
import { NextResponse, type NextRequest } from "next/server";

import {
  resolveWorkspacePreview,
  type WorkspacePreviewResolution,
} from "../../../../src/sites/preview-page";
import { PageProjectionShell } from "../../../../src/sites/shell";

export const dynamic = "force-dynamic";

function queryRecord(request: NextRequest) {
  const query: Record<string, string | string[]> = {};
  for (const [key, value] of request.nextUrl.searchParams.entries()) {
    const existing = query[key];
    query[key] =
      existing === undefined
        ? value
        : Array.isArray(existing)
          ? [...existing, value]
          : [existing, value];
  }
  return query;
}

function notFoundResponse() {
  return new NextResponse(null, { status: 404 });
}

async function renderResolution(
  request: NextRequest,
  resolution: WorkspacePreviewResolution,
) {
  if (resolution.kind === "login") {
    return NextResponse.redirect(new URL("/login", request.url), 307);
  }
  if (resolution.kind === "not_found") return notFoundResponse();
  if (resolution.kind === "redirect") {
    return NextResponse.redirect(
      new URL(resolution.projection.redirect.target, request.url),
      resolution.projection.redirect.status_code,
    );
  }
  const stream = await renderToReadableStream(
    <html lang={resolution.projection.locale}>
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>{resolution.projection.page.title}</title>
      </head>
      <body>
        <PageProjectionShell projection={resolution.projection} />
      </body>
    </html>,
  );
  return new NextResponse(stream, {
    headers: { "Content-Type": "text/html; charset=utf-8" },
  });
}

export async function GET(
  request: NextRequest,
  {
    params,
  }: {
    params: Promise<{ workspaceId: string; sitePath?: string[] }>;
  },
) {
  const { workspaceId, sitePath } = await params;
  const resolution = await resolveWorkspacePreview(
    workspaceId,
    sitePath,
    queryRecord(request),
    {
      requestHeaders: request.headers,
      session:
        request.cookies.get("__Host-slaif_session")?.value ??
        request.cookies.get("slaif_session")?.value,
      browserToken: request.headers.get("x-slaif-browser-preview"),
    },
  );
  return renderResolution(request, resolution);
}
