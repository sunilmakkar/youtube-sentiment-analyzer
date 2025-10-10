"""
File: auth_health.py
Purpose:
    Provide a lightweight health check endpoint that validates
    authentication and multi-tenant scoping (via JWT).

Key responsibilities:
    - Ensures a valid JWT is provided.
    - Confirms the request is scoped to an organization (org_id).
    - Returns a simple JSON response with status and org_id.

Related modules:
    - app/core/deps.py → provides get_current_user dependency.
    - app/api/routes/health.py → system-level health checks.
"""

from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.schemas.auth import CurrentUser

router = APIRouter(prefix="/authz", tags=["authz"])


@router.get(
    "/health",
    summary="JWT authorization health check",
    response_description="Validates authentication and org scoping via JWT.",
)
async def authz_health(current: CurrentUser = Depends(get_current_user)):
    """
    Authorization health check.

    Validates:
        - JWT is valid.
        - User is associated with an organization (org_id).

    Args:
        current (CurrentUser): User context resolved by get_current_user dependency.

    Returns:
        dict: JSON with "status" = "ok" and the user's org_id.

    Example response:
        {
            "status": "ok",
            "org_id": "4fa7b2ac-91e0-4e22-b087-f1f3b1b91b10"
        }
    """
    return {"status": "ok", "org_id": current.org_id}
