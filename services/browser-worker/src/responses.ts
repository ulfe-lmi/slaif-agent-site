export const healthResponse = (
  path: string,
): Readonly<Record<string, unknown>> | null => {
  if (path === "/health/live") {
    return Object.freeze({ service: "browser-worker", status: "ok" });
  }
  if (path === "/health/ready") {
    return Object.freeze({
      components: [],
      service: "browser-worker",
      status: "ready",
    });
  }
  return null;
};
