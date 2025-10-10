"""
File: analytics.py
Layer: Schemas
---------------
Defines Pydantic models for analytics endpoints:
- sentiment trend
- sentiment distribution
- keyword frequencies
"""

from datetime import datetime
from typing import List
from pydantic import BaseModel, Field


class TrendPoint(BaseModel):
    window_start: datetime = Field(..., example="2025-10-01T00:00:00Z")
    window_end: datetime = Field(..., example="2025-10-02T00:00:00Z")
    pos_pct: float = Field(..., example=0.67)
    neg_pct: float = Field(..., example=0.12)
    neu_pct: float = Field(..., example=0.21)
    count: int = Field(..., example=523)


class SentimentTrendResponse(BaseModel):
    trend: List[TrendPoint]


class SentimentDistributionResponse(BaseModel):
    pos_pct: float = Field(..., example=0.65)
    neg_pct: float = Field(..., example=0.15)
    neu_pct: float = Field(..., example=0.20)
    count: int = Field(..., example=430)


class KeywordEntry(BaseModel):
    term: str = Field(..., example="python")
    count: int = Field(..., example=42)


class KeywordsResponse(BaseModel):
    keywords: List[KeywordEntry]
