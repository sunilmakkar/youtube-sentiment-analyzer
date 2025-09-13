from fastapi import APIRouter, Depends

from app.core.deps import get_current_user

router = APIRouter()


@router.get("/authz/health")
async def authz_health(current=Depends(get_current_user)):
    """
    Lightweight endpoint to verify JWT + org_id scoping.
    """
    return {"status": "ok", "org_id": current.org_id}
