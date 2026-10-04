/* global process */

const DETAIL_MAX_CHARS = 300;

/**
 * Bounded, secret-safe failure detail: the first lines of the error message,
 * trimmed and hard-capped.  For the spec's observation-collector assertion
 * (`expect(failures()).toEqual([])`) this surfaces the classified failure
 * tokens (e.g. `console-...`, `http-...`, `network`, `page`) which carry no
 * URLs, secrets, or user input by construction.
 *
 * @param {import("@playwright/test/reporter").TestError | null | undefined} error
 * @returns {string}
 */
function safeDetail(error) {
  if (!error || !error.message) return "unknown";
  const lines = error.message
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line !== "")
    .slice(0, 8);
  return lines.join(" | ").slice(0, DETAIL_MAX_CHARS);
}

export default class SafeReporter {
  /**
   * @param {import("@playwright/test/reporter").TestCase} test
   * @param {import("@playwright/test/reporter").TestResult} result
   */
  onTestEnd(test, result) {
    const project = test.parent.project()?.name ?? "unknown";
    const status = result.status === "passed" ? "PASSED" : "FAILED";
    const stage = test.annotations.find((annotation) => annotation.type === "stage");
    const location = result.error?.location;
    const safeLocation = location
      ? ` line=${location.line} column=${location.column}`
      : "";
    const detail =
      result.status === "passed" ? "" : ` detail=${safeDetail(result.error)}`;
    process.stdout.write(
      `browser-e2e: ${status} project=${project} contract=${test.title} stage=${stage?.description ?? "unknown"}${safeLocation}${detail}\n`,
    );
  }

  /** @param {import("@playwright/test/reporter").FullResult} result */
  onEnd(result) {
    process.stdout.write(
      `browser-e2e: ${result.status === "passed" ? "OK" : "FAILED"}\n`,
    );
  }
}
