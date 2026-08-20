import type { Metadata } from "next";
import { headers } from "next/headers";

import "./styles.css";

export const metadata: Metadata = {
  title: "SLAIF Agent-Site — deployment skeleton",
  description: "Pre-alpha deployment status for the SLAIF Agent-Site skeleton.",
};

export default async function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  await headers();
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
