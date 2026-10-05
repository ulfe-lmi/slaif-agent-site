import { renderToReadableStream } from "react-dom/server.edge";
import { NextResponse, type NextRequest } from "next/server";

import {
  resolveWorkspaceReview,
  type WorkspaceReviewResolution,
} from "../../../../src/sites/review-page";
import { PageProjectionShell } from "../../../../src/sites/shell";

export const dynamic = "force-dynamic";

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
          Canonical drifted after freeze — acceptance is blocked until re-freeze
          (enforced at 083/1); the frozen review remains visible.
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
    return NextResponse.redirect(new URL("/login", request.url), 307);
  }
  if (resolution.kind === "not_found") return notFoundResponse();
  if (resolution.kind === "redirect") {
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
        <PageProjectionShell
          projection={resolution.projection}
          basePath={`/review/${workspaceId}/s/${resolution.projection.site.key}`}
          clientState={false}
        />
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
