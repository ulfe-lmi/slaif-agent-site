const rendererTestModule = new URL(
  "../../apps/web/tests/renderer-behavior.test.ts",
  import.meta.url,
).href;

await import(/* @vite-ignore */ rendererTestModule);
