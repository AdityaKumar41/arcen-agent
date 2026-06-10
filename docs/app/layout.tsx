import type { Metadata } from "next";
import { SiteHeader } from "../components/site-header";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Arcen Agent Docs",
    template: "%s | Arcen Agent Docs"
  },
  description:
    "Documentation for Arcen Agent: install, configure, deploy, extend, and operate the self-improving AI agent.",
  metadataBase: new URL("https://arcen-cli.arcenpay.com"),
  openGraph: {
    title: "Arcen Agent Docs",
    description:
      "Install, configure, deploy, extend, and operate Arcen Agent.",
    images: ["/banner.png"]
  }
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <SiteHeader />
        {children}
      </body>
    </html>
  );
}
