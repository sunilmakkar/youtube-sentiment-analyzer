import logging
import sys


def init_logging() -> None:
    """Configure structured logging for the app."""
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
