import { renderReady } from "../../../src/sites/render";

const readyBody = Object.freeze({
  components: [{ component: "render", status: "ok" }],
  service: "web",
  status: "ready",
});

const unavailableBody = Object.freeze({
  components: [{ component: "render", status: "unavailable" }],
  service: "web",
  status: "not_ready",
});

export async function GET(): Promise<Response> {
  const ready = await renderReady();
  return Response.json(ready ? readyBody : unavailableBody, {
    headers: { "Cache-Control": "no-store" },
    status: ready ? 200 : 503,
  });
}
