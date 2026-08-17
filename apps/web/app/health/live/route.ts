const BODY = Object.freeze({ status: "ok", service: "web" });

export function GET(): Response {
  return Response.json(BODY, {
    headers: { "Cache-Control": "no-store" },
    status: 200,
  });
}
