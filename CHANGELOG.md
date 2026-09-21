# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-09-21

First public release: drive a locally installed DNAMAN 4.0.1.1 (32-bit MFC GUI)
from Python and AI agents, with modern tooling as fallback.

### Added

- `dnaman` package: `Session` (restart -> load -> run -> export), `run_one`,
  `run_pairwise` (315), `run_silent_mutation` (347), `run_directed_mismatch`
  (348), `run_map_reconstruction` (340) and `batch`, with a JSONL run log at
  `%DNAMAN_LOGS%\runs.jsonl`.
- `dnaman` CLI: `doctor`, `list`, `op`, `batch`, `pairwise`, `silent-mutation`,
  `directed-mismatch`, `map-reconstruction`, `report`.
- Safe Win32 automation layer: async `PostMessage` clicks, handle-based status
  bar reads, retrying dialog waits, `RICHEDIT` text extraction, `PrintWindow`
  figure capture with trim, and clipboard extraction for the assembly editor.
- `commands.py` with the DNAMAN menu command id table and the dialog control ids
  that matter, mapped against every supported operation.
- Agent skill (`skills/dnaman-seq-analysis/SKILL.md`) teaching command ids,
  dialog control ids, verified operations and the hard-won automation rules to
  opencode / Claude Code and other Agent Skills hosts.
- Environment-driven configuration (`DNAMAN_DIR`, `DNAMAN_BASE`, `DNAMAN_WORK`,
  `DNAMAN_SEQ`, `DNAMAN_RESULTS`, `DNAMAN_TOOLS`, `DNAMAN_LOGS`) with automatic
  detection of common install paths.
- `report.build_excel`: walks `%DNAMAN_RESULTS%` and writes `summary.xlsx`
  (`files`, `metrics`, `summary` sheets).
- Python fallbacks for the operations DNAMAN cannot do: Biopython, primer3-py,
  pydna, MAFFT, BLAST+, pycirclize.
- Windows CI on Python 3.9 / 3.11 / 3.12 and a platform-free test suite that
  runs on Linux too.

### Changed

- Distribution name is `dnaman-seq-analysis`, matching the repository and the
  bundled skill.
- The version lives only in `dnaman/_version.py`; `pyproject.toml` reads it
  through a setuptools dynamic attribute.
- Installing the skill is available as `python -m dnaman install-skill`;
  `install_skill.py` remains as a compatibility shim.

### Fixed

- Non-Windows platforms now raise a descriptive `ImportError` instead of an
  opaque `ctypes.WinDLL` attribute error.
- `options={"set": {...}}` writes spin-style dialog fields with
  `EM_SETSEL` + `WM_CHAR`, matching what DNAMAN's internal model actually
  accepts (the 430 numeric fields); `SetWindowText` alone was silently ignored.
- `report.build_excel` accepts an `--out` value that has no directory
  component.
- Removed unused imports; `ruff check dnaman tests` is clean.

[Unreleased]: https://github.com/aka-debug-jie/dnaman-seq-analysis/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/aka-debug-jie/dnaman-seq-analysis/releases/tag/v0.1.0
