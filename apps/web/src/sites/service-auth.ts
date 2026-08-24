import "server-only";

import { readFile } from "node:fs/promises";

export async function renderServiceHeaders(): Promise<Record<string, string>> {
  const file = process.env.SLAIF_RENDER_SERVICE_TOKEN_FILE;
  if (!file) return {};
  try {
    const token = (await readFile(file, "ascii")).trim();
    if (!token || /\s/.test(token)) return {};
    return { "x-slaif-render-token": token };
  } catch {
    return {};
  }
}
