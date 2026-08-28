import { BrowserArtifactStore } from "./artifact-store.js";
import { loadWorkerCredential } from "./auth.js";
import { BrowserAttemptExecutor } from "./execution.js";
import { createBrowserWorkerServer, type BrowserWorkerRuntime } from "./http.js";

const host = process.env.BROWSER_WORKER_HOST ?? "0.0.0.0";
const port = Number.parseInt(process.env.BROWSER_WORKER_PORT ?? "3100", 10);

if (!Number.isInteger(port) || port < 1 || port > 65535) {
  throw new Error("Invalid browser-worker configuration.");
}

let runtime: BrowserWorkerRuntime | null = null;
const application = createBrowserWorkerServer(() => runtime);

async function initialize(): Promise<void> {
  let artifactStore: BrowserArtifactStore | null = null;
  try {
    const credential = await loadWorkerCredential(
      process.env.BROWSER_WORKER_SERVICE_CREDENTIAL_FILE ?? "",
    );
    artifactStore = await BrowserArtifactStore.open(
      process.env.BROWSER_WORKER_ARTIFACT_ROOT ?? "",
    );
    const executor = new BrowserAttemptExecutor(
      BrowserAttemptExecutor.configurationFromEnvironment(),
      artifactStore,
    );
    await executor.readiness();
    runtime = Object.freeze({ credential, artifactStore, executor });
  } catch {
    await artifactStore?.close().catch(() => undefined);
  }
}

const shutdown = (): void => {
  application.abortAll();
  application.server.close((error) => {
    void runtime?.artifactStore.close().finally(() => {
      process.exitCode = error === undefined ? 0 : 1;
    });
  });
};

process.once("SIGINT", shutdown);
process.once("SIGTERM", shutdown);
application.server.listen(port, host, () => void initialize());
