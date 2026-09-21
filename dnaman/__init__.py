"""DNAMAN 4.0 automation toolkit (DNAMAN-first, Python fallback).

Quick start:

    from dnaman import ops, app, results, dialogs

    files = ops.run_one("insert.seq", "restriction",
                        outdir="results/insert_restriction")

Configure the DNAMAN installation and workspace with the ``DNAMAN_DIR`` and
``DNAMAN_BASE`` environment variables (see README), then run
``python -m dnaman doctor`` to verify the setup.

Only Windows is supported: the modules that talk to the Win32 API
(``win32``, ``app``, ``dialogs``, ``ops``, ``results``) are imported lazily, so
this package and its platform-independent parts (``commands``, ``config``,
``report``, ``seqmath``) can be inspected on any operating system. Importing a
Win32-backed module on a non-Windows platform raises a descriptive
``ImportError``.
"""

import importlib

from ._version import __version__  # noqa: F401
from . import commands, config, report, seqmath  # noqa: F401

__all__ = ["commands", "config", "report", "seqmath", "__version__"]

# Win32-backed submodules, imported on first attribute access (PEP 562).
_LAZY = ("app", "dialogs", "ops", "results", "win32")


def __getattr__(name):
    if name in _LAZY:
        module = importlib.import_module("." + name, __name__)
        globals()[name] = module
        return module
    raise AttributeError("module %r has no attribute %r" % (__name__, name))


def __dir__():
    return sorted(set(globals()) | set(_LAZY))
