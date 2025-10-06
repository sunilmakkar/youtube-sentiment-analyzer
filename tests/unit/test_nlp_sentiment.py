"""
Unit Test: NLP Sentiment Service
--------------------------------
These tests verify the behavior of the sentiment analysis wrapper in
`app/services/nlp_sentiment.py`.

Scope:
    - `_load_model()` initializes HuggingFace pipeline only once.
    - `analyze_batch()` normalizes results with label, score, model_name.
    - `is_model_loaded()` reflects model warmup status.

Notes:
    - HuggingFace pipeline is patched with a fake implementation.
    - No external models are downloaded; results are deterministic.
"""

import pytest
from unittest.mock import patch

import app.services.nlp_sentiment as nlp


async def test_load_model_initializes_once(monkeypatch):
    """
    Verify `_load_model()` initializes the pipeline only once
    and reuses the same instance on subsequent calls.
    """
    fake_pipeline = object()

    with patch("app.services.nlp_sentiment.pipeline", return_value=fake_pipeline) as mock_pipeline:
        # Reset globals before test
        nlp._model = None
        nlp.model_loaded = False

        model1 = nlp._load_model()
        model2 = nlp._load_model()

        # Should return the fake pipeline both times
        assert model1 is fake_pipeline
        assert model2 is fake_pipeline

        # Underlying HuggingFace pipeline called only once
        mock_pipeline.assert_called_once()


def test_analyze_batch_normalizes_labels(monkeypatch):
    """
    Verify `analyze_batch()` returns normalized labels and correct keys.
    """
    fake_results = [
        {"label": "POSITIVE", "score": 0.95},
        {"label": "NEGATIVE", "score": 0.85},
        {"label": "something_else", "score": 0.50},
    ]

    def fake_pipeline(texts, batch_size=None, truncation=True):
        return fake_results
    
    monkeypatch.setattr(nlp, "_load_model", lambda: fake_pipeline)

    outputs = nlp.analyze_batch(["a", "b", "c"])

    # Should return three results
    assert len(outputs) == 3

    # Check normalization
    labels = [o["label"] for o in outputs]
    assert labels == ["pos", "neg", "neu"]

    # All outputs include the right keys
    for out in outputs:
        assert "label" in out
        assert "score" in out
        assert "model_name" in out
        assert isinstance(out["score"], float)


def test_is_model_loaded_flag(monkeypatch):
    """
    Verify `is_model_loaded()` correctly reflects warmup status.
    """
    # Reset state
    nlp._model = None
    nlp.model_loaded = False

    assert nlp.is_model_loaded() is False

    # Patch pipeline so _load_model succeeds
    monkeypatch.setattr(nlp, "pipeline", lambda *a, **k: object())

    # Call _load_model to set flag
    nlp._load_model()
    assert nlp.is_model_loaded() is True