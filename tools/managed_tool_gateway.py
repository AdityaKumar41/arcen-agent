"""Generic managed-tool gateway helpers for vendor passthroughs."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Callable, Optional

logger = logging.getLogger(__name__)

from arcen_constants import get_arcen_home
from tools.tool_backend_helpers import managed_tool_gateway_enabled

_DEFAULT_TOOL_GATEWAY_DOMAIN = "arcenpay.com"
_DEFAULT_TOOL_GATEWAY_SCHEME = "https"


@dataclass(frozen=True)
class ManagedToolGatewayConfig:
    vendor: str
    gateway_origin: str
    user_token: str
    managed_mode: bool


def auth_json_path():
    """Return the Arcen auth store path, respecting ARCEN_HOME overrides."""
    return get_arcen_home() / "auth.json"


def _parse_timestamp(value: object) -> Optional[datetime]:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _access_token_is_expiring(expires_at: object, skew_seconds: int) -> bool:
    expires = _parse_timestamp(expires_at)
    if expires is None:
        return True
    remaining = (expires - datetime.now(timezone.utc)).total_seconds()
    return remaining <= max(0, int(skew_seconds))


def peek_managed_gateway_token() -> Optional[str]:
    """Cheap probe for an optional managed gateway token."""
    explicit = os.getenv("TOOL_GATEWAY_USER_TOKEN")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    return None


def read_managed_gateway_token() -> Optional[str]:
    """Read an optional managed gateway token from the environment."""
    return peek_managed_gateway_token()


def get_tool_gateway_scheme() -> str:
    """Return configured shared gateway URL scheme."""
    scheme = os.getenv("TOOL_GATEWAY_SCHEME", "").strip().lower()
    if not scheme:
        return _DEFAULT_TOOL_GATEWAY_SCHEME

    if scheme in {"http", "https"}:
        return scheme

    raise ValueError("TOOL_GATEWAY_SCHEME must be 'http' or 'https'")


def build_vendor_gateway_url(vendor: str) -> str:
    """Return the gateway origin for a specific vendor."""
    vendor_key = f"{vendor.upper().replace('-', '_')}_GATEWAY_URL"
    explicit_vendor_url = os.getenv(vendor_key, "").strip().rstrip("/")
    if explicit_vendor_url:
        return explicit_vendor_url

    shared_scheme = get_tool_gateway_scheme()
    shared_domain = os.getenv("TOOL_GATEWAY_DOMAIN", "").strip().strip("/")
    if shared_domain:
        return f"{shared_scheme}://{vendor}-gateway.{shared_domain}"

    return f"{shared_scheme}://{vendor}-gateway.{_DEFAULT_TOOL_GATEWAY_DOMAIN}"


def resolve_managed_tool_gateway(
    vendor: str,
    gateway_builder: Optional[Callable[[str], str]] = None,
    token_reader: Optional[Callable[[], Optional[str]]] = None,
) -> Optional[ManagedToolGatewayConfig]:
    """Resolve shared managed-tool gateway config for a vendor."""
    if not managed_tool_gateway_enabled():
        return None

    resolved_gateway_builder = gateway_builder or build_vendor_gateway_url
    resolved_token_reader = token_reader or read_managed_gateway_token

    gateway_origin = resolved_gateway_builder(vendor)
    user_token = resolved_token_reader()
    if not gateway_origin or not user_token:
        return None

    return ManagedToolGatewayConfig(
        vendor=vendor,
        gateway_origin=gateway_origin,
        user_token=user_token,
        managed_mode=True,
    )


def is_managed_tool_gateway_ready(
    vendor: str,
    gateway_builder: Optional[Callable[[str], str]] = None,
    token_reader: Optional[Callable[[], Optional[str]]] = None,
) -> bool:
    """Return True when gateway URL and a likely-usable token are present.

    Defaults to :func:`peek_managed_gateway_token` so read-only availability scans
    avoid synchronous OAuth refresh. Callers that are about to make a real
    gateway request should use :func:`resolve_managed_tool_gateway` (which
    still defaults to the refresh-aware :func:`read_managed_gateway_token`).
    """
    return resolve_managed_tool_gateway(
        vendor,
        gateway_builder=gateway_builder,
        token_reader=token_reader or peek_managed_gateway_token,
    ) is not None
