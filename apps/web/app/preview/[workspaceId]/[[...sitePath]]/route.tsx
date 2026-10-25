import { renderToReadableStream } from "react-dom/server.edge";
import { NextResponse, type NextRequest } from "next/server";

import {
  POST_FORM_MAX_RAW_BYTES,
  defaultControlStates,
  decodePostedForm,
  selectPostedControls,
} from "../../../../src/renderer/bounded-collection-filter";
import { renderProjection } from "../../../../src/renderer/components";
import {
  resolveWorkspacePreview,
  type WorkspacePreviewResolution,
} from "../../../../src/sites/preview-page";

export const dynamic = "force-dynamic";

/**
 * Raw-bytes pre-read bound: strictly bounds the raw input of any
 * decodable body (worst admitted generated form of the largest admitted
 * control inventory, see bounded-collection-filter.ts).
 */
const POST_FORM_MAX_CONTENT_BYTES = POST_FORM_MAX_RAW_BYTES;

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
  workspaceId: string,
) {
  if (resolution.kind === "login") {
    // Same-origin login destination: a relative Location that the
    // public client resolves against its own request origin.  No
    // absolute URL is derived (the framework bind address is not the
    // public origin, and untrusted Host/forwarded headers must not
    // grant new authority).
    return new NextResponse(null, {
      status: 307,
      headers: { Location: "/login" },
    });
  }
  if (resolution.kind === "not_found") return notFoundResponse();
  if (resolution.kind === "redirect") {
    const target = resolution.projection.redirect.target;
    if (target.startsWith("/")) {
      // Same-origin editorial redirect: a relative Location the public
      // client resolves against its own request origin.  The framework
      // bind address is not the public origin, and untrusted
      // Host/forwarded headers must not grant new authority.
      return new NextResponse(null, {
        status: resolution.projection.redirect.status_code,
        headers: { Location: target },
      });
    }
    // Validated HTTPS external target: absolute and unchanged.
    return NextResponse.redirect(
      new URL(target, request.url),
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
        {/*
         * The preview contract is a flight-free server-rendered document:
         * no client bundle, so the bounded client-state components render
         * their static same-path POST form variants here (trusted
         * projection control states at their initial values).
         */}
        {renderProjection(
          resolution.projection,
          `/preview/${workspaceId}/s/${resolution.projection.site.key}`,
          false,
          defaultControlStates(resolution.projection),
        )}
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
  return renderResolution(request, resolution, workspaceId);
}

/**
 * 083/5-b same-path read-only POST: bounded private search/filter
 * submission for the flight-free preview document. Human session only
 * (the bound browser worker never submits forms); the body carries
 * control state only — site/workspace/snapshot/field authority is
 * re-derived from the resolver and the trusted projection. Every
 * malformed, oversized, duplicate or unknown input is the uniform 404.
 * No write, no persistence, no new endpoint: the response is the
 * identical document re-rendered with the posted control
 * states' bounded result sets (every bound control is re-derived from
 * the trusted projection).
 */
export async function POST(
  request: NextRequest,
  {
    params,
  }: {
    params: Promise<{ workspaceId: string; sitePath?: string[] }>;
  },
) {
  const { workspaceId, sitePath } = await params;
  if (request.headers.get("x-slaif-browser-preview")) return notFoundResponse();
  const contentType = request.headers.get("content-type") ?? "";
  if (!contentType.startsWith("application/x-www-form-urlencoded")) {
    return notFoundResponse();
  }
  const contentLength = request.headers.get("content-length");
  if (
    contentLength !== null &&
    (!/^[0-9]+$/.test(contentLength) ||
      Number(contentLength) > POST_FORM_MAX_CONTENT_BYTES)
  ) {
    return notFoundResponse();
  }
  // Bound the ACTUAL streamed bytes, not only the declared length
  // (absent/chunked/dishonest Content-Length all stay bounded): stop
  // reading once the raw cap is exceeded.
  if (!request.body) return notFoundResponse();
  const textDecoder = new TextDecoder("utf-8", { fatal: false });
  let body = "";
  let bytesRead = 0;
  const reader = request.body.getReader();
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      bytesRead += value.byteLength;
      if (bytesRead > POST_FORM_MAX_CONTENT_BYTES) {
        await reader.cancel();
        return notFoundResponse();
      }
      body += textDecoder.decode(value, { stream: true });
    }
  } catch {
    return notFoundResponse();
  }
  body += textDecoder.decode();
  const fields = decodePostedForm(body);
  if (fields === null) return notFoundResponse();
  const resolution = await resolveWorkspacePreview(
    workspaceId,
    sitePath,
    queryRecord(request),
    {
      requestHeaders: request.headers,
      session:
        request.cookies.get("__Host-slaif_session")?.value ??
        request.cookies.get("slaif_session")?.value,
      browserToken: null, // human session only: bound reads stay GET
    },
  );
  if (resolution.kind !== "page") return notFoundResponse();
  const selection = selectPostedControls(resolution.projection, fields);
  if (selection === null) return notFoundResponse();
  const bindings: Record<string, readonly Record<string, unknown>[]> = {
    ...resolution.projection.bindings,
  };
  for (const [nodeId, state] of selection.states) {
    bindings[nodeId] = state.filtered;
  }
  const projection = { ...resolution.projection, bindings };
  const stream = await renderToReadableStream(
    <html lang={projection.locale}>
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>{projection.page.title}</title>
      </head>
      <body>
        {/*
         * Identical flight-free document re-rendered with the posted
         * control's bounded filtered items and the submitted values.
         */}
        {renderProjection(
          projection,
          `/preview/${workspaceId}/s/${projection.site.key}`,
          false,
          selection.states,
        )}
      </body>
    </html>,
  );
  return new NextResponse(stream, {
    headers: { "Content-Type": "text/html; charset=utf-8" },
  });
}
