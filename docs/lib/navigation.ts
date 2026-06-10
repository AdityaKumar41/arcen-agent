import {
  BookOpen,
  Bot,
  Boxes,
  Cable,
  Code2,
  Cog,
  Compass,
  Cpu,
  Database,
  GitBranch,
  KeyRound,
  LucideIcon,
  MessageSquare,
  Network,
  Rocket,
  ScrollText,
  ShieldCheck,
  TerminalSquare,
  Wrench
} from "lucide-react";

export interface NavItem {
  title: string;
  href: string;
  description: string;
  icon: LucideIcon;
}

export interface NavGroup {
  title: string;
  items: NavItem[];
}

export const navGroups: NavGroup[] = [
  {
    title: "Start",
    items: [
      {
        title: "Overview",
        href: "/docs",
        description: "What Arcen is and where it fits.",
        icon: Compass
      },
      {
        title: "Quickstart",
        href: "/docs/getting-started/quickstart",
        description: "Install, configure, and start a first session.",
        icon: Rocket
      },
      {
        title: "Configuration",
        href: "/docs/getting-started/configuration",
        description: "Profiles, providers, config files, and secrets.",
        icon: Cog
      }
    ]
  },
  {
    title: "Use Arcen",
    items: [
      {
        title: "CLI and TUI",
        href: "/docs/user-guide/cli",
        description: "Terminal workflows, commands, and sessions.",
        icon: TerminalSquare
      },
      {
        title: "Messaging gateway",
        href: "/docs/user-guide/messaging-gateway",
        description: "Telegram, Slack, Discord, WhatsApp, Signal, and more.",
        icon: MessageSquare
      },
      {
        title: "Tools",
        href: "/docs/features/tools",
        description: "Toolsets, terminal backends, and approvals.",
        icon: Wrench
      },
      {
        title: "Skills",
        href: "/docs/features/skills",
        description: "Procedural memory, built-in skills, and optional skills.",
        icon: BookOpen
      },
      {
        title: "Memory",
        href: "/docs/features/memory",
        description: "Persistent recall, search, profiles, and providers.",
        icon: Database
      }
    ]
  },
  {
    title: "Ship",
    items: [
      {
        title: "Deploy the docs",
        href: "/docs/deployment/vercel",
        description: "Deploy this MDX site from your Vercel account.",
        icon: Rocket
      },
      {
        title: "Run Arcen in production",
        href: "/docs/deployment/production",
        description: "Gateway, profiles, isolation, logs, and updates.",
        icon: Network
      },
      {
        title: "Security model",
        href: "/docs/deployment/security",
        description: "Approvals, secrets, container isolation, and egress.",
        icon: ShieldCheck
      }
    ]
  },
  {
    title: "Build",
    items: [
      {
        title: "Architecture",
        href: "/docs/developer-guide/architecture",
        description: "Agent loop, tool registry, CLI, gateway, and TUI.",
        icon: Boxes
      },
      {
        title: "Plugins",
        href: "/docs/developer-guide/plugins",
        description: "General, memory, model-provider, and context plugins.",
        icon: Cable
      },
      {
        title: "Contributing",
        href: "/docs/developer-guide/contributing",
        description: "Local setup, test flow, and review expectations.",
        icon: GitBranch
      }
    ]
  },
  {
    title: "Reference",
    items: [
      {
        title: "Commands",
        href: "/docs/reference/commands",
        description: "Common CLI and slash-command reference.",
        icon: ScrollText
      },
      {
        title: "Environment",
        href: "/docs/reference/environment",
        description: "Secrets, config files, logs, and runtime paths.",
        icon: KeyRound
      },
      {
        title: "Core files",
        href: "/docs/reference/core-files",
        description: "Load-bearing files and where to make changes.",
        icon: Code2
      },
      {
        title: "Model providers",
        href: "/docs/reference/model-providers",
        description: "Provider plugin discovery and selection.",
        icon: Cpu
      },
      {
        title: "Tools API",
        href: "/docs/reference/tools-api",
        description: "Core tool registration and schema rules.",
        icon: Bot
      }
    ]
  }
];

export const flatNavItems = navGroups.flatMap(group => group.items);
