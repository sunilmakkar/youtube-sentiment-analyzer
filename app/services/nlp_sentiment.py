"""
Service: NLP Sentiment Analysis
--------------------------------
This service provides a thin wrapper around a HuggingFace
sentiment-analysis pipeline. It is designed to:

1. Lazy-load the model only once per Celery worker process.
   - On the first call, the pipeline is created and cached.
   - Subsequent calls reuse the same pipeline instance.

2. Support batch inference using the BATCH_SIZE env var.

3. Return normalized results with label, score, and model_name.
"""

import os
from typing import List, Dict

from transformers import pipeline

from app.core.config import settings


# Global variable to hold the loaded model instance
_model = None

# Health flag for worker warmup
model_loaded = False

# Load batch size from env (default to 16 if not set)
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 16))


def _load_model():
    """
    Internal helper to initialize the HuggingFace pipeline.
    Called only once per worker process. 
    """
    global _model, model_loaded

    if _model is None:
        # Use the model name from env (HF_MODEL_NAME in .env)
        _model = pipeline("sentiment-analysis", model=settings.HF_MODEL_NAME)

        # Mark model as ready
        model_loaded = True

    return _model


def analyze_batch(texts: List[str]) -> List[Dict[str, str]]:
    """
    Run sentiment analysis on a batch of text strings.

    Args:
        texts (List[str]): List of comment texts.

    Returns:
        List[Dict[str, str]]:
            Each dict contains:
            - label: "POSITIVE" | "NEGATIVE" | "NEUTRAL"
            - score: float confidence score
            - model_name: model indentifier
    """
    model = _load_model()

    # HuggingFace pipeline automatically handles batching if we pass a list
    results = model(texts, batch_size=BATCH_SIZE, truncation=True)

    normalized = []
    for r in results:
        # Normalize labels to lower-case short form
        label = r["label"].lower()
        if label.startswith("pos"):
            label = "pos"
        elif label.startswith("neg"):
            label = "neg"
        else:
            label = "neu"

        normalized.append(
            {
                "label": label,
                "score": float(r["score"]),
                "model_name": settings.HF_MODEL_NAME
            }
        )
    return normalized


def is_model_loaded() -> bool:
    """
    Expose model warmup status for health checks.
    Returns True once the model is loaded in the worker.
    """
    return model_loaded