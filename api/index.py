"""Vercel serverless entrypoint.

Vercel's Python runtime looks for a module under api/ exporting an ASGI app
named `app`. The real application lives in app/main.py; this file only makes
it importable from the repo root.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from app.main import app  # noqa: E402

__all__ = ["app"]
