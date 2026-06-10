import { Github, MessageSquareText, Search } from "lucide-react";
import Link from "next/link";

export function SiteHeader() {
  return (
    <header className="site-header">
      <Link href="/" className="brand" aria-label="Arcen Agent documentation home">
        <span className="brand-mark">A</span>
        <span>
          <strong>Arcen Agent</strong>
          <small>Docs</small>
        </span>
      </Link>
      <nav className="top-nav" aria-label="Primary navigation">
        <Link href="/docs">Docs</Link>
        <Link href="/docs/getting-started/quickstart">Quickstart</Link>
        <Link href="/docs/deployment/vercel">Deploy</Link>
      </nav>
      <div className="header-actions">
        <Link href="/docs/reference/commands" className="icon-button" aria-label="Search docs">
          <Search aria-hidden="true" />
        </Link>
        <a
          href="https://github.com/AdityaKumar41/arcen-agent"
          className="icon-button"
          aria-label="GitHub repository"
        >
          <Github aria-hidden="true" />
        </a>
        <a href="https://arcenpay.com" className="header-cta">
          <MessageSquareText aria-hidden="true" />
          ArcenPay
        </a>
      </div>
    </header>
  );
}
