import type { ComponentProps, ReactNode } from "react";

export function Button(props: ComponentProps<"button">) {
  return <button {...props} />;
}

export function Card({ children }: { children: ReactNode }) {
  return <article className="admin-card">{children}</article>;
}

export function StatusBadge({ children }: { children: ReactNode }) {
  return <span className="admin-badge">{children}</span>;
}

export function StatusPanel({ children }: { children: ReactNode }) {
  return (
    <div className="admin-status" role="status">
      {children}
    </div>
  );
}

export function Skeleton() {
  return <div className="skeleton" aria-hidden="true" />;
}
