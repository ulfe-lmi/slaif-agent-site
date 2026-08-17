const BODY = Object.freeze({
  components: [],
  service: "web",
  status: "ready",
});

export function GET(): Response {
  return Response.json(BODY, {
    headers: { "Cache-Control": "no-store" },
    status: 200,
  });
}
