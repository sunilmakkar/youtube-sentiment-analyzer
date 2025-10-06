"""
File: keywords.py
Service: Keyword Extraction
---------------------------
This service extracts and persists keyword frequencies
from comments associated with a video.

Key responsibilities:
    - Tokenize all comments for a given org/video.
    - Count term frequencies and select top_k terms.
    - Upsert keyword stats into the `keywords` table.
    - Enforce uniqueness per (org_id, video_id, term).

Related modules:
    - app/models/comment.py → source comment text.
    - app/models/keyword.py → target table for keyword stats.
    - app/tasks/aggregate.py → Celery entrypoints.
"""

import uuid
from collections import Counter
from datetime import datetime

import nltk
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import Comment
from app.models.keyword import Keyword

# Ensure tokenizers is available
nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)


async def compute_and_store_keywords(
    session: AsyncSession, video_id: str, org_id: str, top_k: int = 25
) -> list[dict]:
    """
    Compute and persist top keywords for a video.

    Args:
        session (AsyncSession): Active database session.
        video_id (str): Target video ID (UUID).
        org_id (str): Tenant org identifier.
        top_k (int): Number of keywords to store.

    Returns:
        list[dict]: [{"term": str, "count": int}, ...]
    """
    stmt = (
        select(Comment.text)
        .where(Comment.org_id == org_id)
        .where(Comment.video_id == video_id)
    )
    result = await session.execute(stmt)
    texts = [r[0] for r in result.fetchall()]

    # Tokenize + normalize
    tokens = [w.lower() for text in texts for w in nltk.word_tokenize(text)]
    if not tokens:
        return []
    freq = Counter(tokens).most_common(top_k)

    # Upsert into DB
    upserted = []
    for term, count in freq:
        values = dict(
            id=str(uuid.uuid4()),
            org_id=org_id,
            video_id=video_id,
            term=term,
            count=count,
            last_updated_at=datetime.utcnow(),
        )
        insert_stmt = (
            insert(Keyword)
            .values(**values)
            .on_conflict_do_update(
                index_elements=["org_id", "video_id", "term"],
                set_={
                    "count": count,
                    "last_updated_at": datetime.utcnow(),
                },
            )
        )

        await session.execute(insert_stmt)
        upserted.append({"term": term, "count": count})

    await session.commit()
    return upserted
