"""
File: logging.py
Purpose:
    Centralized logging configuration for the application.

Key responsibilities:
    - Initialize structured JSON-style logs for stdout (container-friendly).
    - Apply consistent formatting for all log messages across the app.
    - Prevent duplicate handlers when reloading (important for dev mode).

Related modules:
    - Python built-in `logging` → provides the logging framework.
    - sys.stdout → logs are written to standard output for container aggregation.
"""

import logging
import sys


def init_logging() -> None:
    """
    Initialize global logging configuration.

    Workflow:
        1. Create a StreamHandler to write logs to stdout.
        2. Apply a JSON-like log formatter for structured logs.
        3. Set log level to INFO globally.
        4. Ensure handlers are not duplicated (important in autoreload).

    This function should be called once during app startup (e.g., in `main.py`).
    """
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '{"time":"%(asctime)s","level":"%(levelname)s","name":"%(name)s","message":"%(message)s"}'
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # avoid duplicate handlers on reload
    if not root.handlers:
        root.addHandler(handler)
