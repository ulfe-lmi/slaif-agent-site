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
  resolveWorkspaceReview,
  type WorkspaceReviewResolution,
} from "../../../../src/sites/review-page";

export const dynamic = "force-dynamic";

/**
 * Raw-bytes pre-read bound: strictly bounds the raw input of any
 * decodable body (worst admitted generated form of the largest admitted
 * control inventory, see bounded-collection-filter.ts).
 */
const POST_FORM_MAX_CONTENT_BYTES = POST_FORM_MAX_RAW_BYTES;

function notFoundResponse() {
  return new NextResponse(null, { status: 404 });
}

function reviewBanner(banner: {
  digest: string;
  baseSiteRevision: number;
  currentSiteRevision: number;
  equal: boolean;
  revisionWatermark: number;
}) {
  return (
    <div
      aria-live="polite"
      className="review-banner"
      data-review-digest={banner.digest}
      data-review-equal={banner.equal ? "true" : "false"}
    >
      <p className="review-banner__title">FROZEN SNAPSHOT — read-only review</p>
      <dl className="review-banner__facts">
        <div>
          <dt>Digest</dt>
          <dd>
            <code>{banner.digest}</code>
          </dd>
        </div>
        <div>
          <dt>Base site revision</dt>
          <dd>{banner.baseSiteRevision}</dd>
        </div>
        <div>
          <dt>Current site revision</dt>
          <dd>{banner.currentSiteRevision}</dd>
        </div>
        <div>
          <dt>Revision watermark</dt>
          <dd>{banner.revisionWatermark}</dd>
        </div>
      </dl>
      {banner.equal ? (
        <p className="review-banner__drift">Canonical unchanged since freeze.</p>
      ) : (
        <p className="review-banner__drift review-banner__drift--warn">
          Canonical drifted after freeze — acceptance is blocked. The frozen review
          remains visible.
        </p>
      )}
    </div>
  );
}

async function renderResolution(
  request: NextRequest,
  resolution: WorkspaceReviewResolution,
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
    if (resolution.target.startsWith("/")) {
      // Same-origin editorial redirect: a relative Location the public
      // client resolves against its own request origin.  The framework
      // bind address is not the public origin, and untrusted
      // Host/forwarded headers must not grant new authority.
      return new NextResponse(null, {
        status: resolution.status_code,
        headers: { Location: resolution.target },
      });
    }
    // Validated HTTPS external target: absolute and unchanged.
    return NextResponse.redirect(
      new URL(resolution.target, request.url),
      resolution.status_code,
    );
  }
  const stream = await renderToReadableStream(
    <html lang={resolution.projection.locale}>
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>{resolution.projection.page.title}</title>
        {/*
         * The review document is flight-free (no client bundle): the
         * renderer chrome comes from /renderer-v1.css (projection shell);
         * the banner is the only review-specific chrome and its styles
         * live in the dedicated /review-v1.css asset.
         */}
        <link rel="stylesheet" href="/review-v1.css" />
      </head>
      <body>
        {/*
         * The review contract is a flight-free server-rendered document
         * of the immutable snapshot: no client bundle, no edit
         * affordances, no Puck link. The banner is the only review
         * chrome (server-rendered, no client JS).
         */}
        {reviewBanner(resolution.banner)}
        {renderProjection(
          resolution.projection,
          `/review/${workspaceId}/s/${resolution.projection.site.key}`,
          false,
          defaultControlStates(resolution.projection),
        )}
      </body>
    </html>,
  );
  // The privacy headers (private no-store, noindex) are delivered at the
  // edge by the same NGINX map the preview contract uses.
  return new NextResponse(stream, {
    headers: {
      "Content-Type": "text/html; charset=utf-8",
    },
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
  const sessionCookie =
    request.cookies.get("__Host-slaif_session") ?? request.cookies.get("slaif_session");
  const resolution = await resolveWorkspaceReview(workspaceId, sitePath, {
    requestHeaders: request.headers,
    sessionCookie: sessionCookie
      ? { name: sessionCookie.name, value: sessionCookie.value }
      : null,
  });
  return renderResolution(request, resolution, workspaceId);
}

/**
 * 083/5-b same-path read-only POST: bounded private search/filter
 * submission over the IMMUTABLE frozen review document. Human session
 * only; the body carries control state only — snapshot/site/workspace
 * authority stays with the resolver, field/operator/item definitions
 * come from the frozen projection. Every malformed, oversized,
 * duplicate or unknown input is the uniform 404. No write, no
 * persistence, no new endpoint: the response is the identical frozen
 * document re-rendered with the single posted control's bounded result
 * set.
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
  const sessionCookie =
    request.cookies.get("__Host-slaif_session") ?? request.cookies.get("slaif_session");
  const resolution = await resolveWorkspaceReview(workspaceId, sitePath, {
    requestHeaders: request.headers,
    sessionCookie: sessionCookie
      ? { name: sessionCookie.name, value: sessionCookie.value }
      : null,
  });
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
        <link rel="stylesheet" href="/review-v1.css" />
      </head>
      <body>
        {reviewBanner(resolution.banner)}
        {/*
         * Identical frozen document re-rendered with the posted
         * control's bounded filtered items and the submitted values.
         */}
        {renderProjection(
          projection,
          `/review/${workspaceId}/s/${projection.site.key}`,
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
