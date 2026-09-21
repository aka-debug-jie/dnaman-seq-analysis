# Examples

Minimal, runnable scripts for the `dnaman` package. Each one restarts DNAMAN,
loads a sequence, runs one analysis and writes text/figure files under
`%DNAMAN_RESULTS%`.

## Prerequisites

```powershell
pip install -e .                      # from the repository root
$env:DNAMAN_DIR  = "C:\Program Files (x86)\DNAMAN"
$env:DNAMAN_BASE = "C:\work\dnaman"   # optional workspace root

python -m dnaman doctor               # expect: result: ALL GOOD
```

Put your own sequences in `%DNAMAN_SEQ%` (default `%DNAMAN_BASE%\work\seq`), or
pass an absolute path as the first argument of every helper.

## The scripts

| Script | What it does | DNAMAN command |
|---|---|---|
| `01_restriction_analysis.py` | double-strand digest: text summary + map + pattern figures | 325 |
| `02_primer_design.py` | PCR primer pairs for an ORF with relaxed acceptance limits | 430 |
| `03_batch_and_report.py` | several analyses in one go, then a summary workbook | 251 / 300 / `report` |

They are Windows-only: the package drives the DNAMAN GUI through Win32 APIs and
raises a descriptive `ImportError` anywhere else.

## Notes

- Every analysis runs in its own DNAMAN process. Loading a second sequence while
  a channel is occupied fails silently, so `ops.Session` restarts the app for
  each call - the scripts look slow for that reason, not because they hang.
- `examples` deliberately keep the code short. The hard-won details (exact
  control ids, wizard pages, which fields ignore `SetWindowText`) are in
  [`skills/dnaman-seq-analysis/SKILL.md`](../skills/dnaman-seq-analysis/SKILL.md).
