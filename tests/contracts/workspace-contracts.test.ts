import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import * as apiClient from "@slaif-agent-site/api-client";
import * as browserToolContracts from "@slaif-agent-site/browser-tool-contracts";
import * as componentCatalog from "@slaif-agent-site/component-catalog";
import * as compositionSchema from "@slaif-agent-site/composition-schema";
import * as contentModelSchema from "@slaif-agent-site/content-model-schema";
import * as scopeCatalog from "@slaif-agent-site/scope-catalog";
import * as testFixtures from "@slaif-agent-site/test-fixtures";
import { describe, expect, it } from "vitest";

interface PackageManifest {
  dependencies?: Record<string, string>;
  devDependencies?: Record<string, string>;
  exports?: unknown;
  files?: unknown;
  license?: unknown;
  name?: unknown;
  optionalDependencies?: Record<string, string>;
  peerDependencies?: Record<string, string>;
  private?: unknown;
  scripts?: Record<string, string>;
  type?: unknown;
  types?: unknown;
  version?: unknown;
}

const repositoryRoot = resolve(import.meta.dirname, "../..");
const boundaries = [
  {
    slug: "api-client",
    expectedName: "@slaif-agent-site/api-client",
    packageModule: apiClient,
  },
  {
    slug: "browser-tool-contracts",
    expectedName: "@slaif-agent-site/browser-tool-contracts",
    packageModule: browserToolContracts,
  },
  {
    slug: "component-catalog",
    expectedName: "@slaif-agent-site/component-catalog",
    packageModule: componentCatalog,
  },
  {
    slug: "composition-schema",
    expectedName: "@slaif-agent-site/composition-schema",
    packageModule: compositionSchema,
  },
  {
    slug: "content-model-schema",
    expectedName: "@slaif-agent-site/content-model-schema",
    packageModule: contentModelSchema,
  },
  {
    slug: "scope-catalog",
    expectedName: "@slaif-agent-site/scope-catalog",
    packageModule: scopeCatalog,
  },
  {
    slug: "test-fixtures",
    expectedName: "@slaif-agent-site/test-fixtures",
    packageModule: testFixtures,
  },
] as const;

function loadManifest(slug: string): PackageManifest {
  const contents = readFileSync(
    resolve(repositoryRoot, "packages", slug, "package.json"),
    "utf8",
  );
  const document: unknown = JSON.parse(contents);
  expect(document).toBeTypeOf("object");
  expect(document).not.toBeNull();
  return document as PackageManifest;
}

describe("workspace contract package boundaries", () => {
  it("exports seven exact, unique, serializable scaffold identities", () => {
    const names = boundaries.map(({ expectedName, packageModule }) => {
      expect(Object.keys(packageModule)).toEqual(["packageMetadata"]);
      expect(packageModule.packageMetadata).toEqual({
        name: expectedName,
        status: "pre-alpha-scaffold",
        version: "0.0.0",
      });
      expect(Object.isFrozen(packageModule.packageMetadata)).toBe(true);
      expect(JSON.parse(JSON.stringify(packageModule.packageMetadata))).toEqual(
        packageModule.packageMetadata,
      );
      expect(
        Object.values(packageModule).some((value) => typeof value === "function"),
      ).toBe(false);
      return packageModule.packageMetadata.name;
    });

    expect(names).toHaveLength(7);
    expect(new Set(names).size).toBe(7);
    expect(names).toEqual(boundaries.map(({ expectedName }) => expectedName));
  });

  it("keeps every package private, exact, dependency-free, and buildable", () => {
    for (const { expectedName, slug } of boundaries) {
      const manifest = loadManifest(slug);
      expect(manifest).toMatchObject({
        name: expectedName,
        version: "0.0.0",
        private: true,
        license: "Apache-2.0",
        type: "module",
        files: ["dist"],
        exports: {
          ".": {
            types: "./dist/index.d.ts",
            import: "./dist/index.js",
          },
        },
        types: "./dist/index.d.ts",
        scripts: {
          build: "tsc --project tsconfig.json",
          typecheck: "tsc --project tsconfig.json --noEmit",
        },
      });
      expect(manifest.dependencies).toBeUndefined();
      expect(manifest.devDependencies).toBeUndefined();
      expect(manifest.optionalDependencies).toBeUndefined();
      expect(manifest.peerDependencies).toBeUndefined();
    }
  });
});
