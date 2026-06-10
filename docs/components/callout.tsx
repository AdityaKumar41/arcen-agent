import { AlertTriangle, CheckCircle2, Info, Lightbulb } from "lucide-react";
import type { ReactNode } from "react";

const toneConfig = {
  info: { icon: Info, label: "Info" },
  tip: { icon: Lightbulb, label: "Tip" },
  warning: { icon: AlertTriangle, label: "Warning" },
  check: { icon: CheckCircle2, label: "Check" }
} as const;

export interface CalloutProps {
  children: ReactNode;
  title?: string;
  type?: keyof typeof toneConfig;
}

export function Callout({ children, title, type = "info" }: CalloutProps) {
  const config = toneConfig[type];
  const Icon = config.icon;

  return (
    <div className={`callout callout-${type}`}>
      <Icon aria-hidden="true" className="callout-icon" />
      <div>
        <p className="callout-title">{title ?? config.label}</p>
        <div className="callout-body">{children}</div>
      </div>
    </div>
  );
}
