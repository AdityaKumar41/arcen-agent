export interface NavItem {
  title: string;
  href: string;
  description: string;
  icon: string;
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
        title: "Introduction",
        href: "/docs",
        description: "What Arcen is and how the docs are organized.",
        icon: "compass"
      },
      {
        title: "Quickstart",
        href: "/docs/getting-started/quickstart",
        description: "Install, configure, and start a first session.",
        icon: "rocket"
      },
      {
        title: "Configuration",
        href: "/docs/getting-started/configuration",
        description: "Profiles, providers, config files, and secrets.",
        icon: "cog"
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
        icon: "terminal"
      },
      {
        title: "Messaging gateway",
        href: "/docs/user-guide/messaging-gateway",
        description: "Telegram, Slack, Discord, WhatsApp, Signal, and more.",
        icon: "message"
      },
      {
        title: "Gateway platforms",
        href: "/docs/user-guide/gateway-platforms",
        description: "Adapter model and platform-specific setup notes.",
        icon: "network"
      },
      {
        title: "Tools",
        href: "/docs/features/tools",
        description: "Toolsets, terminal backends, and approvals.",
        icon: "tool"
      },
      {
        title: "Terminal backends",
        href: "/docs/features/terminal-backends",
        description: "Local, Docker, SSH, Modal, Daytona, and Singularity.",
        icon: "terminal"
      },
      {
        title: "Skills",
        href: "/docs/features/skills",
        description: "Procedural memory, built-in skills, and optional skills.",
        icon: "book"
      },
      {
        title: "Memory",
        href: "/docs/features/memory",
        description: "Persistent recall, search, profiles, and providers.",
        icon: "database"
      },
      {
        title: "MCP",
        href: "/docs/features/mcp",
        description: "Connect external MCP servers to extend capabilities.",
        icon: "plug"
      },
      {
        title: "Cron",
        href: "/docs/features/cron",
        description: "Scheduled tasks and recurring automations.",
        icon: "cog"
      },
      {
        title: "Context files",
        href: "/docs/features/context-files",
        description: "Project instructions and workspace context.",
        icon: "scroll"
      }
    ]
  },
  {
    title: "Operations",
    items: [
      {
        title: "Production",
        href: "/docs/deployment/production",
        description: "Gateway, profiles, isolation, logs, and updates.",
        icon: "network"
      },
      {
        title: "Security model",
        href: "/docs/deployment/security",
        description: "Approvals, secrets, container isolation, and egress.",
        icon: "shield"
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
        icon: "boxes"
      },
      {
        title: "TUI internals",
        href: "/docs/developer-guide/tui",
        description: "Ink frontend, JSON-RPC transport, and Python gateway.",
        icon: "terminal"
      },
      {
        title: "Plugins",
        href: "/docs/developer-guide/plugins",
        description: "General, memory, model-provider, and context plugins.",
        icon: "plug"
      },
      {
        title: "Observability",
        href: "/docs/developer-guide/observability",
        description: "Observer hooks, telemetry events, and integration points.",
        icon: "network"
      },
      {
        title: "Contributing",
        href: "/docs/developer-guide/contributing",
        description: "Local setup, test flow, and review expectations.",
        icon: "branch"
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
        icon: "scroll"
      },
      {
        title: "Environment",
        href: "/docs/reference/environment",
        description: "Secrets, config files, logs, and runtime paths.",
        icon: "key"
      },
      {
        title: "Core files",
        href: "/docs/reference/core-files",
        description: "Load-bearing files and where to make changes.",
        icon: "code"
      },
      {
        title: "Model providers",
        href: "/docs/reference/model-providers",
        description: "Provider plugin discovery and selection.",
        icon: "cpu"
      },
      {
        title: "Tools API",
        href: "/docs/reference/tools-api",
        description: "Core tool registration and schema rules.",
        icon: "bot"
      }
    ]
  }
];

export const flatNavItems = navGroups.flatMap(group => group.items);

export function normalizePath(pathname: string) {
  if (pathname.length > 1 && pathname.endsWith("/")) {
    return pathname.slice(0, -1);
  }
  return pathname;
}
