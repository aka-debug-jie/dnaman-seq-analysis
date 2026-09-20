"""DNAMAN 4.0 automation toolkit (DNAMAN-first, Python fallback).

Quick start:

    from dnaman import ops, app, results, dialogs

    files = ops.run_one("insert.seq", "restriction",
                        outdir="results/insert_restriction")

Configure the DNAMAN installation and workspace with the ``DNAMAN_DIR`` and
``DNAMAN_BASE`` environment variables (see README), then run
``python -m dnaman doctor`` to verify the setup.
"""

from . import app, commands, config, dialogs, ops, results, win32  # noqa: F401

__all__ = ["app", "commands", "config", "dialogs", "ops", "results", "win32"]
__version__ = "0.1.0"
