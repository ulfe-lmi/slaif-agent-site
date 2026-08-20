export const CONTROL = "/api/control/v1" as const;

export type SessionSummary = {
  recent_auth: boolean;
  absolute_expires_at: string;
};

async function request(path: string, init?: RequestInit): Promise<Response> {
  return fetch(`${CONTROL}${path}`, {
    ...init,
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
}

export async function setupStatus(): Promise<{
  initialized: boolean;
  setup_available: boolean;
}> {
  const response = await request("/setup/status");
  if (!response.ok) throw new Error("unavailable");
  return response.json() as Promise<{ initialized: boolean; setup_available: boolean }>;
}

export function submitSetup(body: {
  setup_token: string;
  username: string;
  password: string;
  display_name: string;
  email: string | null;
}): Promise<Response> {
  return request("/setup", { method: "POST", body: JSON.stringify(body) });
}

export function submitLogin(username: string, password: string): Promise<Response> {
  return request("/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export async function session(): Promise<SessionSummary> {
  const response = await request("/session", { method: "GET" });
  if (!response.ok) throw new Error("unauthenticated");
  const value = (await response.json()) as Record<string, unknown>;
  if (
    typeof value.recent_auth !== "boolean" ||
    typeof value.absolute_expires_at !== "string"
  ) {
    throw new Error("invalid-response");
  }
  return {
    recent_auth: value.recent_auth,
    absolute_expires_at: value.absolute_expires_at,
  };
}

export function csrfCookie(cookie: string, secure = false): string {
  const expected = secure ? "__Host-slaif_csrf" : "slaif_csrf";
  const alternate = secure ? "slaif_csrf" : "__Host-slaif_csrf";
  const values = new Map<string, string>();
  for (const fragment of cookie.split(";")) {
    const pair = fragment.trim();
    const separator = pair.indexOf("=");
    if (separator <= 0 || separator !== pair.lastIndexOf("=")) throw new Error("csrf");
    const name = pair.slice(0, separator);
    if (values.has(name)) throw new Error("csrf");
    values.set(name, pair.slice(separator + 1));
  }
  if (values.has(alternate)) throw new Error("csrf");
  const value = values.get(expected);
  if (!value) throw new Error("csrf");
  return value;
}

export function logout(cookie: string, secure = false): Promise<Response> {
  const csrf = csrfCookie(cookie, secure);
  return request("/logout", { method: "POST", headers: { "X-CSRF-Token": csrf } });
}
