"""Compatibility shim for the historical entry point.

Prefer ``python -m dnaman install-skill``; this script simply forwards to
``dnaman.skill`` so existing documentation keeps working.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dnaman.skill import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
