import path from "node:path";
import { createHash } from "node:crypto";
import { readFileSync, readdirSync } from "node:fs";

const repositoryRoot = path.join(import.meta.dirname, "../..");

function versionedBuildInputs() {
  const paths = [
    "package.json",
    "pnpm-lock.yaml",
    "pnpm-workspace.yaml",
    "tsconfig.base.json",
    "tsconfig.json",
    "apps/web/next.config.mjs",
    "apps/web/package.json",
    "apps/web/tsconfig.json",
    "docs/assets/slaif-logo.svg",
  ];
  for (const directory of [
    "apps/web/app",
    "apps/web/public",
    "apps/web/src",
    "packages",
  ]) {
    const absolute = path.join(repositoryRoot, directory);
    for (const entry of readdirSync(absolute, {
      recursive: true,
      withFileTypes: true,
    })) {
      if (entry.isFile()) {
        const relative = path.relative(
          repositoryRoot,
          path.join(entry.parentPath, entry.name),
        );
        if (!relative.split(path.sep).some((part) => part === "dist")) {
          paths.push(relative);
        }
      }
    }
  }
  return [...new Set(paths)].sort();
}

function deterministicBuildId() {
  const digest = createHash("sha256");
  for (const relative of versionedBuildInputs()) {
    digest.update(relative);
    digest.update("\0");
    digest.update(readFileSync(path.join(repositoryRoot, relative)));
    digest.update("\0");
  }
  return digest.digest("hex").slice(0, 32);
}

// Reproducible client-reference manifests (OAP 078-7-b, defect D1).
//
// Next.js emits one `*_client-reference-manifest.js` asset per app route as
// `globalThis.__RSC_MANIFEST[...]={<json>};`. The JSON object key order is the
// runtime insertion order of the webpack module-graph walk (the generated
// flight client entry imports its client references in module-processing
// order, which can interleave differently across builds on loaded machines),
// so the emitted bytes are not reproducible even when the manifest entries
// are identical. The supply-chain reproducibility gate byte-compares these
// files (they are outside the gate's normalization set).
//
// The plugin re-emits every such asset in a canonical form: object keys
// sorted at every level, compact JSON separators, arrays kept in emitted
// order. The manifest is consumed only through property lookups
// (`__RSC_MANIFEST[page]`, `.ssrModuleMapping[id]`, `.clientModules[resource]`,
// `.entryCSSFiles[resource]`), so canonical key order changes no renderer
// behavior. Stage 4500 runs after PROCESS_ASSETS_STAGE_ANALYSE (4000), where
// Next's ClientReferenceManifestPlugin emits the manifests, and before
// PROCESS_ASSETS_STAGE_REPORT (5000), so the canonical bytes are what gets
// written.

const CLIENT_REFERENCE_MANIFEST_ASSET_RE = /_client-reference-manifest\.js$/;
const MANIFEST_WRAPPER_RE =
  /^globalThis\.__RSC_MANIFEST=\(globalThis\.__RSC_MANIFEST\|\|\{\}\);globalThis\.__RSC_MANIFEST\["((?:[^"\\]|\\.)*)"\]=(\{.*\});$/s;

function canonicalizeManifestValue(value) {
  if (Array.isArray(value)) {
    return value.map(canonicalizeManifestValue);
  }
  if (value !== null && typeof value === "object") {
    const canonical = {};
    for (const key of Object.keys(value).sort()) {
      canonical[key] = canonicalizeManifestValue(value[key]);
    }
    return canonical;
  }
  return value;
}

function canonicalManifestSource(source) {
  const text = source.toString("utf-8");
  const match = MANIFEST_WRAPPER_RE.exec(text);
  if (!match) {
    throw new Error(
      "reproducible client-reference manifest: unexpected wrapper format; " +
        "refusing to emit non-canonical bytes",
    );
  }
  const pageKey = JSON.parse(`"${match[1]}"`);
  const manifest = canonicalizeManifestValue(JSON.parse(match[2]));
  return (
    "globalThis.__RSC_MANIFEST=(globalThis.__RSC_MANIFEST||{});" +
    `globalThis.__RSC_MANIFEST[${JSON.stringify(pageKey)}]` +
    `=${JSON.stringify(manifest)};`
  );
}

function deterministicClientReferenceManifests(RawSource) {
  const name = "DeterministicClientReferenceManifests";
  return {
    apply(compiler) {
      compiler.hooks.compilation.tap(name, (compilation) => {
        compilation.hooks.processAssets.tap({ name, stage: 4500 }, (assets) => {
          for (const [assetName, source] of Object.entries(assets)) {
            if (!CLIENT_REFERENCE_MANIFEST_ASSET_RE.test(assetName)) {
              continue;
            }
            compilation.updateAsset(
              assetName,
              new RawSource(canonicalManifestSource(source.source())),
            );
          }
        });
      });
    },
  };
}

/** @type {import('next').NextConfig} */
const nextConfig = {
  generateBuildId: async () => deterministicBuildId(),
  images: { unoptimized: true },
  output: "standalone",
  outputFileTracingRoot: path.join(import.meta.dirname, "../.."),
  poweredByHeader: false,
  reactStrictMode: true,
  webpack: (config, options) => {
    if (!options.dev) {
      config.plugins = [
        ...(config.plugins ?? []),
        deterministicClientReferenceManifests(options.webpack.sources.RawSource),
      ];
    }
    return config;
  },
};

export default nextConfig;
