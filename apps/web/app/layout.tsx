import type { Metadata } from "next";
import { headers } from "next/headers";

import "@measured/puck/no-external.css";
import "./styles.css";
import { RENDERER_STYLESHEET } from "../src/renderer/styles";

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
      <head>
        <link rel="stylesheet" href={RENDERER_STYLESHEET} />
      </head>
      <body>{children}</body>
    </html>
  );
}
