/* global process */

export default class SafeReporter {
  /**
   * @param {import("@playwright/test/reporter").TestCase} test
   * @param {import("@playwright/test/reporter").TestResult} result
   */
  onTestEnd(test, result) {
    const project = test.parent.project()?.name ?? "unknown";
    const status = result.status === "passed" ? "PASSED" : "FAILED";
    const stage = test.annotations.find((annotation) => annotation.type === "stage");
    process.stdout.write(
      `browser-e2e: ${status} project=${project} contract=${test.title} stage=${stage?.description ?? "unknown"}\n`,
    );
  }

  /** @param {import("@playwright/test/reporter").FullResult} result */
  onEnd(result) {
    process.stdout.write(
      `browser-e2e: ${result.status === "passed" ? "OK" : "FAILED"}\n`,
    );
  }
}
