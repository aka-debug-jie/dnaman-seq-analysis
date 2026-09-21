"""Single source of truth for the package version.

Kept import-free so ``setuptools`` can read it statically (AST) when building,
without importing the package (which requires Windows).
"""

__version__ = "0.1.0"
