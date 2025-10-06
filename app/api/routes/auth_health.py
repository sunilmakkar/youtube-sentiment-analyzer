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

router = APIRouter()


@router.get("/authz/health")
async def authz_health(current=Depends(get_current_user)):
    """
    Authorization health check.

    Validates:
        - JWT is valid.
        - User is associated with an organization (org_id).

    Args:
        current: User object resolved by get_current_user dependency.

    Returns:
        dict: JSON with "status" = "ok" and the user's org_id.
    """
    return {"status": "ok", "org_id": current.org_id}
