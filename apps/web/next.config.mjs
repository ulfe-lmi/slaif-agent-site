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
  for (const directory of ["apps/web/app", "packages"]) {
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

/** @type {import('next').NextConfig} */
const nextConfig = {
  generateBuildId: async () => deterministicBuildId(),
  images: { unoptimized: true },
  output: "standalone",
  outputFileTracingRoot: path.join(import.meta.dirname, "../.."),
  poweredByHeader: false,
  reactStrictMode: true,
};

export default nextConfig;
