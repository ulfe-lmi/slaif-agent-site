import { createServer } from "node:http";

import { healthResponse } from "./responses.ts";

const host = process.env.BROWSER_WORKER_HOST ?? "0.0.0.0";
const port = Number.parseInt(process.env.BROWSER_WORKER_PORT ?? "3100", 10);

if (!Number.isInteger(port) || port < 1 || port > 65535) {
  throw new Error("Invalid browser-worker port.");
}

const server = createServer((request, response) => {
  const body = request.method === "GET" ? healthResponse(request.url ?? "") : null;
  response.setHeader("Cache-Control", "no-store");
  response.setHeader("Content-Type", "application/json; charset=utf-8");
  if (body === null) {
    response.writeHead(404);
    response.end('{"status":"not_found"}\n');
    return;
  }
  response.writeHead(200);
  response.end(`${JSON.stringify(body)}\n`);
});

const shutdown = (): void => {
  server.close((error) => {
    process.exitCode = error === undefined ? 0 : 1;
  });
};

process.once("SIGINT", shutdown);
process.once("SIGTERM", shutdown);
server.listen(port, host);
