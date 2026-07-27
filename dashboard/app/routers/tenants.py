"""
Avamed super-admin tenant picker — step 5 of MULTI_TENANCY_PROPOSAL.md §8.

Renders LINKS to each tenant's own hostname/login. This route (and this whole
module) must NEVER connect to a tenant database or render any tenant's case
data — the picker's entire job is to be a link list. See §6/§6b of the
proposal and governance/STEP5_DESIGN.md §5 for why that boundary is load-bearing.

Gated to the avamed-super-admin role only (require_avamed_super_admin).
"""
from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Request

from ..db import connect
from ..helpers import current_staff_from_request, ensure_ready, require_avamed_super_admin
from ..paths import ROOT_DIR
from ..templates_config import templates

router = APIRouter()

# Lives at config/registry.json — NOT config/tenants/registry.json. That
# subfolder is deliberately ACL-locked (Saeed's step-4 fix removed ordinary-
# user write access so only admin-elevated processes can touch it), which
# blocked git itself from creating this file there at merge time. config/
# itself carries no such restriction. See governance/STEP5_DESIGN.md §6.
REGISTRY_PATH = ROOT_DIR / "config" / "registry.json"


def load_tenant_registry(path=None) -> list[dict[str, Any]]:
    """Read the machine-readable tenant list. Config pointers only — see
    config/registry.json's own header comment. Returns [] if the file
    is missing rather than raising, so a misconfigured/not-yet-onboarded
    environment shows an empty picker instead of a 500."""
    registry_path = path or REGISTRY_PATH
    if not registry_path.exists():
        return []
    try:
        data = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    tenants = data.get("tenants", [])
    return tenants if isinstance(tenants, list) else []


def tenant_login_url(tenant: dict[str, Any]) -> str:
    """Hostname if set (public, HTTPS), else localhost:port for pre-hostname tenants."""
    hostname = tenant.get("hostname")
    if hostname:
        return f"https://{hostname}/login"
    port = tenant.get("port")
    return f"http://localhost:{port}/login" if port else "#"


@router.get("/tenants")
def tenants_page(request: Request) -> Any:
    ensure_ready()
    with connect() as conn:
        current_staff = current_staff_from_request(request, conn)
    require_avamed_super_admin(current_staff)

    tenants = load_tenant_registry()
    for tenant in tenants:
        tenant["login_url"] = tenant_login_url(tenant)

    return templates.TemplateResponse(
        request,
        "tenants.html",
        {
            "current_staff": current_staff,
            "tenants": tenants,
            "active_nav": "tenants",
        },
    )
