import Link from "next/link";
import type { ReactNode } from "react";
import { flatNavItems, navGroups } from "../lib/navigation";

export interface DocsShellProps {
  children: ReactNode;
}

export function DocsShell({ children }: DocsShellProps) {
  return (
    <div className="docs-layout">
      <aside className="docs-sidebar" aria-label="Documentation navigation">
        <div className="sidebar-sticky">
          {navGroups.map(group => (
            <section className="sidebar-group" key={group.title}>
              <h2>{group.title}</h2>
              <nav>
                {group.items.map(item => {
                  const Icon = item.icon;
                  return (
                    <Link href={item.href} key={item.href} className="sidebar-link">
                      <Icon aria-hidden="true" />
                      <span>{item.title}</span>
                    </Link>
                  );
                })}
              </nav>
            </section>
          ))}
        </div>
      </aside>
      <main className="docs-main">
        <article className="prose">{children}</article>
      </main>
      <aside className="docs-index" aria-label="Page index">
        <div className="index-card">
          <p>Docs map</p>
          {flatNavItems.slice(0, 8).map(item => (
            <Link href={item.href} key={item.href}>
              {item.title}
            </Link>
          ))}
        </div>
      </aside>
    </div>
  );
}
