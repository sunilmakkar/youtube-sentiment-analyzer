"""
File: rate_limiter.py
Service: Per-Org Rate Limiting
------------------------------
This service enforces request rate limits for multi-tenant APIs.

Key responsibilities:
    - Limit how many times an org can hit sensitive endpoints (e.g. /ingest)
      within a rolling time window.
    - Use Redis to implement a token bucket algorithm:
        * Each org_id has a "bucket" with a max capacity.
        * Tokens are added at a fixed rate (refill).
        * Each request consumes a token.
        * If no tokens remain, the request is blocked.
    - Protect system resources from abuse, ensure fairness across tenants.

Related modules:
    - app/core/config.py → provides Redis connection string.
    - app/api/routes/ingest.py → consumes this service to enforce per-org limits.
"""

import time
import redis.asyncio as aioredis
from app.core.config import settings

# Rate limit configuration (per org)
RATE_LIMIT_MAX_TOKENS = 5           # bucket capacity (burst allowed)
RATE_LIMIT_REFILL_RATE = 5 / 60     # tokens per second (~5 tokens per minute)

# Global Redis connection pool
redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)


async def check_rate_limit(org_id: str) -> bool:
    """
    Check and update the rate limit bucket for a given org.

    Args:
        org_id (str): Tenant organization identifier.
    
    Returns:
        bool:
        - True -> request allowed (token consumed).
        - False -> request denied (rate limit exceeded).
    """
    key = f"rate:{org_id}"
    now = time.time()

    # Fetch state
    bucket = await redis.hgetall(key)
    if bucket:
        tokens = float(bucket.get("tokens", RATE_LIMIT_MAX_TOKENS))
        last_refill = float(bucket.get("last_refill", now))
    else:
        tokens = RATE_LIMIT_MAX_TOKENS
        last_refill = now

    # Refill tokens based on elapsed time
    elapsed = now - last_refill
    tokens = min(RATE_LIMIT_MAX_TOKENS, tokens + elapsed * RATE_LIMIT_REFILL_RATE)
    allowed = tokens >= 1.0

    if allowed:
        tokens -= 1.0   # consume one token
        await redis.hset(
            key,
            mapping={"tokens": tokens, "last_refill": now},  # ✅ fixed
        )
        await redis.expire(key, 60)     # expire after inactivity
        return True
    else:
        # No tokens -> reject request
        await redis.hset(
            key,
            mapping={"tokens": tokens, "last_refill": now},
        )
        await redis.expire(key, 60)
        return False
