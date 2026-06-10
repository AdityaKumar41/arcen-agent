import { ArrowRight, BookOpen, Rocket, TerminalSquare } from "lucide-react";
import Link from "next/link";
import { CardGrid } from "../components/card-grid";
import { navGroups } from "../lib/navigation";

const featured = [
  ...navGroups[0].items,
  navGroups[1].items[0],
  navGroups[1].items[1],
  navGroups[2].items[0]
];

export default function HomePage() {
  return (
    <>
      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">MDX documentation for Arcen Agent</p>
          <h1>Arcen Agent</h1>
          <p>
            Install, configure, operate, and extend the self-improving AI agent
            from one deployable documentation site.
          </p>
          <div className="hero-actions">
            <Link href="/docs/getting-started/quickstart" className="primary-action">
              <Rocket aria-hidden="true" />
              Start quickstart
            </Link>
            <Link href="/docs/deployment/vercel" className="secondary-action">
              Deploy docs
              <ArrowRight aria-hidden="true" />
            </Link>
          </div>
          <div className="quick-links" aria-label="Common doc entry points">
            <Link href="/docs/user-guide/cli" className="secondary-action">
              <TerminalSquare aria-hidden="true" />
              CLI
            </Link>
            <Link href="/docs/features/skills" className="secondary-action">
              <BookOpen aria-hidden="true" />
              Skills
            </Link>
          </div>
        </div>
        <div className="hero-media">
          <img src="/banner.png" alt="Arcen Agent terminal banner" />
          <pre className="terminal-card">{`curl -fsSL https://arcen-cli.arcenpay.com/install.sh | bash
arcen setup
arcen`}</pre>
        </div>
      </section>

      <section className="home-section">
        <div className="section-heading">
          <h2>Find the next useful page</h2>
          <p>
            The docs are organized around the actual workflows in this repo:
            starting a session, connecting messaging platforms, adding tools,
            deploying services, and contributing safely.
          </p>
        </div>
        <CardGrid items={featured} />
      </section>
    </>
  );
}
