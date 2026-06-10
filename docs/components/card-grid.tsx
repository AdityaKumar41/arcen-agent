import Link from "next/link";
import type { NavItem } from "../lib/navigation";

export interface CardGridProps {
  items: NavItem[];
}

export function CardGrid({ items }: CardGridProps) {
  return (
    <div className="card-grid">
      {items.map(item => {
        const Icon = item.icon;
        return (
          <Link href={item.href} key={item.href} className="doc-card">
            <Icon aria-hidden="true" />
            <span>{item.title}</span>
            <p>{item.description}</p>
          </Link>
        );
      })}
    </div>
  );
}
