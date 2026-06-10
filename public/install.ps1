# Stable public installer entrypoint for:
#   iex (irm https://arcen-cli.arcenpay.com/install.ps1)
#
# Keep the canonical installer in scripts/install.ps1 so release logic and local
# development use one implementation.

$ErrorActionPreference = "Stop"
$installerUrl = if ($env:ARCEN_INSTALLER_SOURCE_URL) {
    $env:ARCEN_INSTALLER_SOURCE_URL
} else {
    "https://raw.githubusercontent.com/AdityaKumar41/arcen-agent/main/scripts/install.ps1"
}

$script = Invoke-RestMethod -Uri $installerUrl
Invoke-Expression $script
