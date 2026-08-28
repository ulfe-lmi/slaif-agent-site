export const healthResponse = (
  path: string,
  ready = false,
): Readonly<Record<string, unknown>> | null => {
  if (path === "/health/live") {
    return Object.freeze({ service: "browser-worker", status: "ok" });
  }
  if (path === "/health/ready") {
    return Object.freeze({
      components: ready
        ? Object.freeze([
            "artifact-store",
            "chromium-sandbox",
            "request-confinement",
            "worker-service-auth",
          ])
        : Object.freeze([]),
      service: "browser-worker",
      status: ready ? "ready" : "unavailable",
    });
  }
  return null;
};
