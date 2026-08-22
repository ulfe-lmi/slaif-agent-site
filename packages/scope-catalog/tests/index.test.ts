import { describe, expect, it } from "vitest";
import {
  AGENT_READ_SCOPES,
  AGENT_L1_WRITE_SCOPES,
  AGENT_L2_WRITE_SCOPES,
  AGENT_L3_WRITE_SCOPES,
  AGENT_L4_WRITE_SCOPES,
  DELEGATION_LEVELS,
} from "../src";

describe("AGENT_READ_SCOPES", () => {
  it("contains exactly the architecture read scopes", () => {
    expect([...AGENT_READ_SCOPES]).toEqual([
      "site:read",
      "content-model:read",
      "content-item:read",
      "collection-view:read",
      "page:read",
      "composition:read",
      "navigation:read",
      "translation:read",
      "media:read",
      "theme:read",
      "redirect:read",
      "component-catalog:read",
      "preview:inspect",
      "validation:read",
    ]);
    expect(AGENT_READ_SCOPES).toHaveLength(14);
  });
});

describe("AGENT_L1_WRITE_SCOPES", () => {
  it("contains exactly the L1 write scopes", () => {
    expect(AGENT_L1_WRITE_SCOPES).toHaveLength(10);
    expect([...AGENT_L1_WRITE_SCOPES]).toContain("content-item:create");
    expect([...AGENT_L1_WRITE_SCOPES]).toContain("seo:write");
  });
});

describe("AGENT_L2_WRITE_SCOPES", () => {
  it("contains exactly the L2 write scopes", () => {
    expect(AGENT_L2_WRITE_SCOPES).toHaveLength(19);
    expect([...AGENT_L2_WRITE_SCOPES]).toContain("page:create");
    expect([...AGENT_L2_WRITE_SCOPES]).toContain("relationship:write");
  });
});

describe("AGENT_L3_WRITE_SCOPES", () => {
  it("contains exactly the L3 write scopes", () => {
    expect(AGENT_L3_WRITE_SCOPES).toHaveLength(8);
    expect([...AGENT_L3_WRITE_SCOPES]).toContain("composition:write");
    expect([...AGENT_L3_WRITE_SCOPES]).toContain("theme-tokens:write");
  });
});

describe("AGENT_L4_WRITE_SCOPES", () => {
  it("contains exactly the L4 write scopes", () => {
    expect(AGENT_L4_WRITE_SCOPES).toHaveLength(18);
    expect([...AGENT_L4_WRITE_SCOPES]).toContain("content-model:create");
    expect([...AGENT_L4_WRITE_SCOPES]).toContain("site-reset:workspace");
  });
});

describe("DELEGATION_LEVELS", () => {
  it("maps levels 1-4 with cumulative scope sets", () => {
    const keys = Object.keys(DELEGATION_LEVELS).map(Number).sort();
    expect(keys).toEqual([1, 2, 3, 4]);

    // Cumulative: each level includes all scopes from previous levels.
    expect(DELEGATION_LEVELS[1].length).toBe(
      AGENT_READ_SCOPES.length + AGENT_L1_WRITE_SCOPES.length,
    );
    expect(DELEGATION_LEVELS[2].length).toBe(
      DELEGATION_LEVELS[1].length + AGENT_L2_WRITE_SCOPES.length,
    );
    expect(DELEGATION_LEVELS[3].length).toBe(
      DELEGATION_LEVELS[2].length + AGENT_L3_WRITE_SCOPES.length,
    );
    expect(DELEGATION_LEVELS[4].length).toBe(
      DELEGATION_LEVELS[3].length + AGENT_L4_WRITE_SCOPES.length,
    );
  });

  it("level 4 contains every scope from all levels", () => {
    const allScopes = new Set<string>([
      ...AGENT_READ_SCOPES,
      ...AGENT_L1_WRITE_SCOPES,
      ...AGENT_L2_WRITE_SCOPES,
      ...AGENT_L3_WRITE_SCOPES,
      ...AGENT_L4_WRITE_SCOPES,
    ]);
    expect(new Set(DELEGATION_LEVELS[4])).toEqual(allScopes);
  });

  it("no forbidden scopes appear in any level", () => {
    const forbidden = [
      "site:create",
      "site:archive",
      "site:delete",
      "workspace:create",
      "workspace:freeze",
      "workspace:accept",
      "capability:create",
      "site:publish",
      "membership:manage",
      "schema:migrate",
    ];
    for (const level of [1, 2, 3, 4] as const) {
      for (const scope of DELEGATION_LEVELS[level]) {
        expect(forbidden).not.toContain(scope);
      }
    }
  });
});
