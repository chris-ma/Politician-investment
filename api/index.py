"""
Vercel serverless entry point.

Vercel's @vercel/python runtime discovers the `app` variable in this file
and uses it as the ASGI handler for all incoming requests.
"""
import sys
import os

# Ensure the project root is on the path so `app.*` imports resolve correctly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app  # noqa: F401 — re-exported for Vercel runtime

# `app` is the FastAPI ASGI application picked up by Vercel automatically.
