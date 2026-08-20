"use client";

import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import {
  csrfCookie,
  logout,
  session,
  setupStatus,
  submitLogin,
  submitSetup,
  type SessionSummary,
} from "./client";

const failure = "The request could not be completed. Check the details and try again.";

function formString(data: FormData, name: string): string {
  const value = data.get(name);
  return typeof value === "string" ? value : "";
}

export function SetupForm() {
  const [message, setMessage] = useState("Checking setup status…");
  const [pending, setPending] = useState(false);
  useEffect(() => {
    void setupStatus().then(
      (value) =>
        setMessage(
          value.initialized
            ? "Setup is closed. Sign in instead."
            : value.setup_available
              ? "Setup token ready."
              : "Ask the operator to issue a setup token.",
        ),
      () => setMessage(failure),
    );
  }, []);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending) return;
    setPending(true);
    setMessage("Creating administrator…");
    const data = new FormData(event.currentTarget);
    try {
      const response = await submitSetup({
        setup_token: formString(data, "setup_token"),
        username: formString(data, "username"),
        password: formString(data, "password"),
        display_name: formString(data, "display_name"),
        email: formString(data, "email") || null,
      });
      if (!response.ok) throw new Error("denied");
      window.location.assign("/admin");
    } catch {
      setMessage(failure);
      setPending(false);
    }
  }
  return (
    <AuthLayout title="Create the first administrator" message={message}>
      <form onSubmit={(event) => void submit(event)} aria-describedby="form-status">
        <Field
          label="Setup token"
          name="setup_token"
          type="password"
          autoComplete="off"
        />
        <Field label="Username" name="username" autoComplete="username" />
        <Field label="Display name" name="display_name" autoComplete="name" />
        <Field
          label="Email (optional)"
          name="email"
          type="email"
          autoComplete="email"
          required={false}
        />
        <Field
          label="Password"
          name="password"
          type="password"
          autoComplete="new-password"
        />
        <button disabled={pending} type="submit">
          {pending ? "Creating…" : "Create administrator"}
        </button>
      </form>
    </AuthLayout>
  );
}

export function LoginForm() {
  const [message, setMessage] = useState("Use your local administrator credentials.");
  const [pending, setPending] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending) return;
    setPending(true);
    setMessage("Signing in…");
    const data = new FormData(event.currentTarget);
    try {
      const response = await submitLogin(
        formString(data, "username"),
        formString(data, "password"),
      );
      if (!response.ok) throw new Error("denied");
      window.location.assign("/admin");
    } catch {
      setMessage(failure);
      setPending(false);
    }
  }
  return (
    <AuthLayout title="Sign in" message={message}>
      <form onSubmit={(event) => void submit(event)} aria-describedby="form-status">
        <Field label="Username" name="username" autoComplete="username" />
        <Field
          label="Password"
          name="password"
          type="password"
          autoComplete="current-password"
        />
        <button disabled={pending} type="submit">
          {pending ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </AuthLayout>
  );
}

export function AdminSession() {
  const [value, setValue] = useState<SessionSummary | null>(null);
  const [message, setMessage] = useState("Checking your session…");
  const [pending, setPending] = useState(false);
  useEffect(() => {
    void session().then(
      (item) => {
        setValue(item);
        setMessage("Authenticated session active.");
      },
      () => {
        window.location.replace("/login");
      },
    );
  }, []);
  async function signOut() {
    if (pending) return;
    setPending(true);
    setMessage("Signing out…");
    try {
      const secure = window.location.protocol === "https:";
      csrfCookie(document.cookie, secure);
      const response = await logout(document.cookie, secure);
      if (response.status !== 204) throw new Error("denied");
      window.location.replace("/login");
    } catch {
      setMessage(failure);
      setPending(false);
    }
  }
  return (
    <AuthLayout title="Administrator" message={message}>
      {value && (
        <dl>
          <div>
            <dt>Account</dt>
            <dd>{value.user_account_id}</dd>
          </div>
          <div>
            <dt>Recent authentication</dt>
            <dd>{value.recent_auth ? "Yes" : "No"}</dd>
          </div>
          <div>
            <dt>Session expires</dt>
            <dd>{new Date(value.absolute_expires_at).toLocaleString()}</dd>
          </div>
        </dl>
      )}
      <button disabled={pending || !value} onClick={() => void signOut()} type="button">
        Sign out
      </button>
    </AuthLayout>
  );
}

function Field({
  label,
  name,
  type = "text",
  autoComplete,
  required = true,
}: {
  label: string;
  name: string;
  type?: string;
  autoComplete: string;
  required?: boolean;
}) {
  return (
    <label>
      {label}
      <input name={name} type={type} autoComplete={autoComplete} required={required} />
    </label>
  );
}

function AuthLayout({
  title,
  message,
  children,
}: {
  title: string;
  message: string;
  children: React.ReactNode;
}) {
  return (
    <main>
      <header className="compact-header">
        <a href="/" aria-label="SLAIF Agent-Site home">
          <img
            src="/slaif-logo.svg"
            alt="SLAIF — Slovenian AI Factory"
            width="150"
            height="118"
          />
        </a>
      </header>
      <section className="auth-card" aria-labelledby="page-title">
        <h1 id="page-title">{title}</h1>
        <p id="form-status" role="status" aria-live="polite">
          {message}
        </p>
        {children}
        <p>
          <a href="/">Back to home</a>
        </p>
      </section>
    </main>
  );
}
