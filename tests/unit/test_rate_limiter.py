"""
File: test_rate_limiter.py
Layer: Unit
------------
Unit tests for the Rate Limiter service.

Targets:
    - check_rate_limit

Key aspects validated:
    - Token consumption per request.
    - Blocking when tokens are exhausted.
    - Automatic token refill after wait time.
"""

import asyncio
import pytest

from app.services import rate_limiter


@pytest.mark.asyncio
async def test_rate_limiter_allows_then_blocks(redis_client, seeded_comments_for_auth):
    """
    It should allow up to RATE_LIMIT_MAX_TOKENS requests
    then block when the bucket is empty.
    """
    org_id = seeded_comments_for_auth.org_id

    # Consume all tokens
    allowed = [await rate_limiter.check_rate_limit(org_id) for _ in range(rate_limiter.RATE_LIMIT_MAX_TOKENS)]
    assert all(allowed) # all initial requests allowed

    # Next request should be blocked
    blocked = await rate_limiter.check_rate_limit(org_id)
    assert blocked is False


@pytest.mark.asyncio
async def test_rate_limiter_refills_token(redis_client, seeded_comments_for_auth):
    """
    It should refill tokens after enough time has passed.
    """
    org_id = seeded_comments_for_auth.org_id

    # Exhaust bucket
    for _ in range(rate_limiter.RATE_LIMIT_MAX_TOKENS):
        await rate_limiter.check_rate_limit(org_id)

    # Blocked at this point
    assert await rate_limiter.check_rate_limit(org_id) is False

    # Wait long enough for at leastg 1 token to refill
    await asyncio.sleep(15) # 0.25 of a minute = 1 token with default config

    allowed = await rate_limiter.check_rate_limit(org_id)
    assert allowed is True