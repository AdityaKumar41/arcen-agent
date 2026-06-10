#!/usr/bin/env bash
set -euo pipefail

# Stable public installer entrypoint for:
#   curl -fsSL https://arcen-cli.arcenpay.com/install.sh | bash
#
# Keep the canonical installer in scripts/install.sh so release logic and local
# development use one implementation.

INSTALLER_URL="${ARCEN_INSTALLER_SOURCE_URL:-https://raw.githubusercontent.com/AdityaKumar41/arcen-agent/main/scripts/install.sh}"
tmp="$(mktemp -t arcen-install.XXXXXX.sh)"
cleanup() {
    rm -f "$tmp"
}
trap cleanup EXIT

curl -fsSL "$INSTALLER_URL" -o "$tmp"
bash "$tmp" "$@"
