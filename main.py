"""Convenience launcher so ``python main.py`` works from the repository root.

The real entry point lives in ``src/hammurabi/main.py``; this file only
delegates to it. For normal use prefer the ``hammurabi`` console script or
``python -m hammurabi``.
"""

from hammurabi.main import main

if __name__ == "__main__":
    raise SystemExit(main())
