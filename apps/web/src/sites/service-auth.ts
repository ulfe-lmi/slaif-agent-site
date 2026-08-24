import "server-only";

import { constants } from "node:fs";
import { lstat, open } from "node:fs/promises";

const renderToken = loadRenderToken();

async function loadRenderToken(): Promise<string | null> {
  const file = process.env.SLAIF_RENDER_SERVICE_TOKEN_FILE;
  if (!file) return null;
  try {
    const directory = await lstat(file.substring(0, file.lastIndexOf("/")) || "/");
    const uid = typeof process.getuid === "function" ? process.getuid() : -1;
    if (
      !directory.isDirectory() ||
      (directory.mode & 0o777) !== 0o700 ||
      directory.uid !== uid
    )
      return null;
    const handle = await open(file, constants.O_RDONLY | constants.O_NOFOLLOW);
    try {
      const info = await handle.stat();
      if (!info.isFile() || (info.mode & 0o777) !== 0o400 || info.uid !== uid)
        return null;
      const token = await handle.readFile({ encoding: "ascii" });
      return token && token.length >= 32 && token.length <= 256 && !/\s/.test(token)
        ? token
        : null;
    } finally {
      await handle.close();
    }
  } catch {
    return null;
  }
}

export async function renderServiceHeaders(): Promise<Record<string, string>> {
  const token = await renderToken;
  return token ? { "x-slaif-render-token": token } : {};
}
