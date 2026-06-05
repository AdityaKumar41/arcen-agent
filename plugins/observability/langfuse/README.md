# Langfuse Observability Plugin

This plugin ships bundled with Arcen but is **opt-in** — it only loads when
you explicitly enable it.

## Enable

Pick one:

```bash
# Interactive: walks you through credentials + SDK install + enable
arcen tools  # → Langfuse Observability

# Manual
pip install langfuse
arcen plugins enable observability/langfuse
```

## Required credentials

Set these in `~/.arcen/.env` (or via `arcen tools`):

```bash
ARCEN_LANGFUSE_PUBLIC_KEY=pk-lf-...
ARCEN_LANGFUSE_SECRET_KEY=sk-lf-...
ARCEN_LANGFUSE_BASE_URL=https://cloud.langfuse.com   # or your self-hosted URL
```

Without the SDK or credentials the hooks no-op silently — the plugin fails
open.

## Verify

```bash
arcen plugins list                 # observability/langfuse should show "enabled"
arcen chat -q "hello"              # then check Langfuse for a "Arcen turn" trace
```

## Optional tuning

```bash
ARCEN_LANGFUSE_ENV=production       # environment tag
ARCEN_LANGFUSE_RELEASE=v1.0.0       # release tag
ARCEN_LANGFUSE_SAMPLE_RATE=0.5      # sample 50% of traces
ARCEN_LANGFUSE_MAX_CHARS=12000      # max chars per field (default: 12000)
ARCEN_LANGFUSE_DEBUG=true           # verbose plugin logging
```

## Disable

```bash
arcen plugins disable observability/langfuse
```
