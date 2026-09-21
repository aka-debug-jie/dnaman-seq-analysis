---
name: dnaman-seq-analysis
description: Drive DNAMAN 4.0 (legacy Windows GUI) for sequence analysis - restriction/enzyme mapping, primer design, translation, ORF, assembly, alignment, protein analysis - via pywinauto/Win32 automation; falls back to Biopython, primer3-py, pydna, MAFFT or BLAST+ when DNAMAN cannot do the job. Use when the user mentions DNAMAN, 酶切分析, 引物设计, 序列拼接, ORF, 序列比对, 质粒图谱, or asks to analyse .seq/GenBank files with a locally installed DNAMAN.
---

# DNAMAN sequence analysis (DNAMAN-first, Python fallback)

Goal: complete bioinformatics tasks by driving a locally installed DNAMAN 4.0.1.1
(32-bit MFC application, © 1994-98 Lynnon BioSoft) through Win32 automation, and
only fall back to modern tooling when DNAMAN cannot produce the result.
Windows only (DNAMAN is a Windows application).

## Setup

```powershell
pip install -e .                      # or: pip install dnaman-seq-analysis
$env:DNAMAN_DIR  = "C:\Program Files (x86)\DNAMAN"   # folder with DNAMAN.EXE
$env:DNAMAN_BASE = "C:\work\dnaman"                  # workspace root (optional)
python -m dnaman doctor               # expect: result: ALL GOOD
```

All paths are environment driven (see README): `DNAMAN_DIR`, `DNAMAN_BASE`,
`DNAMAN_WORK`, `DNAMAN_SEQ`, `DNAMAN_RESULTS`, `DNAMAN_TOOLS`, `DNAMAN_LOGS`.
In this skill `%DNAMAN_BASE%` refers to the workspace root and
`%DNAMAN_RESULTS%` to the results directory. The package creates missing
directories automatically (`config.ensure_dirs()` runs on every `Session`).

## Decision tree

1. Is the task in the **DNAMAN verified list** below? -> run it through the
   `dnaman` package, export txt/png.
2. Did DNAMAN fail (no window, error box, needs interactive map/editor)? ->
   fall back to the **Python / CLI tool map**.
3. For anything numerically important -> cross-validate with Biopython and say
   so in the answer.

Never claim a DNAMAN result you did not read back from the screen/clipboard.

## Reusable code (already written, reuse before rewriting)

**The `dnaman` package** is a consolidated, hardened toolkit (safe async clicks,
handle-based status bar, retrying dialog waits, guaranteed cleanup, run log).
Prefer it over ad-hoc scripts.

```python
import os
from dnaman import ops, app, dialogs, results, config
from dnaman.commands import CMD, DLG

files = ops.run_one("insert.seq", "restriction",
                    outdir=os.path.join(config.RESULTS, "insert_restriction"),
                    options={"dialog": "Restriction Analysis",
                             "check": [1098, 1100, 1101, 1102]})   # circular+map+pattern
ops.run_one("insert.gb", "pcr_primers", genbank=True)
ops.run_one("protein.seq", "aa_composition", protein=True)
ops.batch([("insert.seq", "orf"), ("insert.seq", "direct_repeats")])
```

CLI:

```powershell
python -m dnaman doctor                  # environment self-check
python -m dnaman list                    # all command names + ids
python -m dnaman op --seq insert.seq --op restriction
python -m dnaman op --seq insert.gb --op pcr_primers --genbank
python -m dnaman batch --seq insert.seq vector.seq --op composition orf
python -m dnaman pairwise --seq a.seq b.seq                             # 315
python -m dnaman silent-mutation --seq gene.seq --start 698 --end 900   # 347 (region <= ~300 bp)
python -m dnaman directed-mismatch --seq gene.seq --position 781 --base G   # 348
python -m dnaman map-reconstruction --seq vector.seq --enz-a EcoRI --enz-b HindIII   # 340
python -m dnaman report                  # results/summary.xlsx
```

Package layout: `config.py` (paths, env-overridable), `win32.py` (ctypes
primitives), `commands.py` (CMD/DLG id tables), `app.py` (launch/kill/status/
messages), `dialogs.py` (file dialog, GenBank dialog, Sequence Type prompt,
wizard driver), `results.py` (RICHEDIT read, PrintWindow capture + trim,
clipboard), `ops.py` (`Session`, `run_one`, `batch`, JSONL run log at
`%DNAMAN_LOGS%\runs.jsonl`), `cli.py`, `report.py`.

## Hard-won automation rules

- **Never `SendMessage(BM_CLICK)`** on a button that opens a modal dialog - it
  blocks forever. Use `PostMessage(hwnd, 0x00F5, 0, 0)` (`PostMessage` is safe;
  the package's `click()` already does this).
- **Restart DNAMAN for every sequence.** Loading a second sequence while a
  channel is occupied silently does nothing. `ops.Session` does this for you.
- **File dialog recipe**: send the menu command, wait for a `#32770` window that
  has a child with control id `1152`, then `WM_SETTEXT ""` + one
  `PostMessage(WM_CHAR, ord(ch))` per character (30 ms apart), then
  `PostMessage(BM_CLICK)` on control id `1`. `SetWindowText` alone does not
  update the shell dialog model and the Open button will be ignored.
- **Custom numeric/region edits (spin-box style)**: `SetWindowText` updates the
  display but NOT DNAMAN's internal model - the value is silently ignored.
  Write with `SendMessage(edit, EM_SETSEL=0xB1, 0, -1)` then one
  `PostMessage(WM_CHAR, ord(ch))` per digit (`win32.set_edit_value`). Required
  for the 347 region (1255/1256), 348 position/base (1265/1258) and every 430
  numeric field (1000-1020).
- **GenBank import**: cmd 222 additionally pops a `GenBank Sequence` dialog with
  a ListBox id `1063`; select index 0 (`LB_SETCURSEL`) and click `Load` (id `1`).
- **Protein**: DNAMAN asks `Is <name> a DNA sequence?` (`Sequence Type` dialog).
  Click **No** (id `7`) to load as protein. Status bar then reads
  `Channel 1:Protein | <name> | NNNaa`.
- **Wizards**: click `Select All` once per dialog then `Next` (`12324`) /
  `Finish` (`12325`) / `OK` (`1`). Reset the "select all done" state before each
  run (`dialogs.reset_wizard_state()`).
- **Restriction analysis options** (wizard page 1): `1098` circular, `1099`
  summary text, `1100` restriction map, `1101` show enzyme position, `1102`
  pattern figure.
- **Reading results**:
  - **Take the `docs()` baseline BEFORE sending the menu command.** The summary
    text and map windows can open while the wizard is still being clicked; if
    the baseline is taken after the wizard finishes they land in `before` and
    are never exported (only the later Pattern figure shows up).
  - after the first new result window appears, keep polling ~3 s before
    exporting - figures (map/pattern) can appear a moment later and are missed
    if you break out of the wait loop too early
  - text: `results.rich_of(hwnd)` (FindWindowEx `RICHEDIT`) + `results.read_text()`
  - figures: `results.capture_png(hwnd)` (PrintWindow, works even when the
    window is covered) + PIL white/black trim
  - MASED / assembly editor (no RICHEDIT): activate the document, then post
    `WM_COMMAND 57642` (Select All) and `57634` (Copy) and read the clipboard
    (tkinter `clipboard_get`). Clicking an in-window button (e.g. `Export`)
    first is what makes the view active.
- **Screenshots of dialogs**: PrintWindow also works on modal `#32770` dialogs
  (do NOT trim them - the gray background defeats the white/black trim). Drive
  wizards manually (snap each page, then click Next/Finish/OK) instead of
  `handle_wizard`, and snapshot message boxes before dismissing them.
- **Verify every load** via the status bar (`app.status_text(main_h)`): it must
  show the expected sequence name and bp/aa count before running analyses.
- DNAMAN is 32-bit; pywinauto prints a warning under 64-bit Python. Window,
  menu, RICHEDIT and clipboard access all work; a few custom controls do not.

## Command IDs (menu -> id)

Sequence: load from file `221`, GenBank `222`, GCG `223`, database `224`,
multiple `228`; display composition `251`, reverse `252`, complement `253`,
rev-comp `254`, double strand `255`, RNA `256`, protein `257`; BLAST docs
`275-279`; assembly `290`; search sequences `295`, direct repeats `296`, mirror
repeats `297`, hairpin `298`, amino-acid `299`, ORF `300`; dot matrix `310`;
two-sequence alignment `315`; multiple alignment `320`; random new `248`,
randomize current `249`.

Restriction: analysis `325`, cloning `335`, map reconstruction `340`, draw map
`345`, silent mutation `347`, directed mismatch `348`.

Primer: oligo DB manager `400`, import `402`, export `403`; load primer from
input `410`, from DB `411`; Tm `420`, self-complementarity `425`,
complementarity with DNA `426`, second primer `427/428`, design PCR primers
`430`, mispriming `414`.

Protein: genetic code `350`, translation overview `352`, translation `355`,
reverse translation `380/381`, codon usage `360/361/362`, amino-acid
composition `365`, charge/pH `368`, hydrophobicity `366/383`, hydrophilicity
`367/384`, secondary structure `385`.

Database: manager `440`, scan similarity `460`, search nt `461`, search aa `462`.
Info: restriction enzymes `470`, methylase `480`, genetic code `482`, amino acids
`484`, nucleotides `486`.

Editor: undo/redo `57643/57644`, select all `57642`, copy `57634`, paste `57637`,
find `57636`, sequence format `210`, enter sequence `215`, save as `57604`.

Dialog control ids you actually need:

- **325 Restriction Analysis**: page 1 options `1098` circular, `1099` summary
  text, `1100` map, `1101` enzyme position, `1102` pattern; page 2
  "Enzyme Selection" (file combo defaults to `常用酶.enz` with 11 enzymes incl.
  EcoRI/HindIII; `Select All >>` must be clicked or the run fails with
  `Select enzymes!`).
- **347 Silent Mutation**: `1000` enzyme-file combo (`0`=DNAMANRE.ENZ ~1364,
  `1`=RESTRICT.ENZ 117 default, `2`=常用酶.enz 11), `1251/1252` cutter >=5/>=6,
  `1253` enzyme count, `1254` `&Seq`, `1255/1256` analysis region start/end.
- **348 Directed Mismatch**: `1265` mutation position, `1258` mutant base
  ("for"), `1255` WT context (display), `1256` mutant context (static),
  `1254` `&Site`, `1266/1267/1268` max-mismatch radios (Non / <=1 / <=2).
- **430 PCR primer design** (three dialogs: "Primer filtration" -> "Refinement
  and pair selection" -> "Final"): page 1 `1000/1001` product size,
  `1002/1003` sense from/to, `1004/1005` antisense from/to, `1006` "Shortest
  primers only", `1007/1008` length, `1009/1010` Tm, `1011/1012` GC,
  `1013` primer nM, `1014/1015` dimer/hairpin, `1016/1017` polyN/3'-unique,
  `1020` salt; page 2 `1018` primer-primer, `1019` Tm difference,
  `1113` mispriming cutoff (list counts are statics `1110/1111`); page 3 is a
  ListBox of pairs (read with `LB_GETCOUNT`/`LB_GETTEXT`).

## Verified DNAMAN operations

Working end-to-end (text and/or figure exported):

composition 251 · reverse/complement/rev-comp/RNA 252-256 · ORF 300 · direct
repeats 296 · mirror repeats 297 · hairpin 298 · aa search 299 · enter sequence
215 · random sequence 248 · randomize 249 · dot matrix 310 · restriction
analysis 325 (+ map/pattern figures, circular, or "all DNA in sequence
channels" 1103 for multi-channel) · translation 355 · translation overview 352 ·
codon usage 360 · aa composition 365 · hydrophobicity 366 · hydrophilicity 367 ·
secondary structure 385 · reverse translation 380 · PCR primer design 430 ·
primer Tm 420 (via `Show Tm` + `Report`) · self-complementarity 425 ·
complementarity with DNA 426 · sequence assembly 290 (consensus via clipboard) ·
multiple alignment 320 · **pairwise alignment 315** · **silent mutation 347** ·
**directed mismatch 348** · **map reconstruction 340** · GenBank import 222.

### Multi-channel loading (unlocks 315 and any "all channels" option)

`Load Sequence | Multiple` (228) uses the same common file dialog but accepts the
Windows multi-select syntax - type `"path1" "path2"` into edit 1152 and press
Open. DNAMAN answers with an `N Sequences` info box (dismiss it); channel 1 then
holds the first file. Wait ~5 s before reading the status bar. Use
`ops.Session.load_multiple([...])` / `ops.run_pairwise([a, b])`.

- **315 Two Sequence Alignment**: after a two-file multi-load, cmd 315 opens a
  `Pairwise Alignment` dialog (Fast / Optimal, gap params, identity symbol) -
  it can take up to ~20 s to appear. Press OK -> the result is a normal
  RICHEDIT text document ("Fast alignment of DNA sequences X and Y ... identity=
  99%"). `python -m dnaman pairwise --seq A B`.
- **347 Silent Mutation**: works at the **degenerate-codon level** - it prints
  W.T./RT1/RT2 degenerate sequences plus a per-enzyme site table, and a site is
  only "removed" if no codon combination can form it (it removed one EcoRI site
  but could NOT remove another because GAR|TTY|CAR still allows GAA|TTC).
  `&Seq` sets the region to 1-300 only, not the whole sequence; set the region
  explicitly (1255/1256). **Regions larger than ~200-300 bp crash DNAMAN** -
  restrict the window to the target site.
  `python -m dnaman silent-mutation --seq X --start 698 --end 900`.
- **348 Directed Mismatch**: the reliable way to introduce a specific point
  mutation. Set position (1265) and the new base (1258, e.g. `781` + `G`); OK
  yields a report with the mutant context and the affected enzymes (`*` marks
  the mutation, `^` a mismatch). It does NOT emit a mutated sequence document -
  apply the change with a script and re-verify with 325.
- **430 PCR primer design**: defaults (product 400-600 bp, length 18-21,
  Tm 62-65, GC 40-60) are too narrow for full-ORF cloning primers. Relax to the
  target product size, length 18-25, Tm 50-85, GC 35-85 and raise the page-2
  Tm-difference limit; the **product-size range is the reliable way to pin the
  antisense primer end** (the antisense "from/to" window semantics are
  unreliable). The `3' Unique (base) < 6` filter rejects primers whose
  3'-terminal 6 bases are not unique (e.g. `CAATGG` occurring 3x) - that is why
  an ATG-start primer can be missing from the list. Add the restriction tails
  yourself (`CGGGAATTC...`, `CCCAAGCTT...`).
- **340 Map Reconstruction**: fill the fragment grid **largest first** - column A
  ids 1001-1010, column B 1011-1020, column A+B 1021-1030, values in Kb with 3
  decimals; DNA type Circular (1052) by default. Wrong order or wrong sizes
  gives `Fragment sizes not correct` / `No solution!`. Compute the digest with
  Biopython first (see `ops.run_map_reconstruction`).
  `python -m dnaman map-reconstruction --seq X --enz-a EcoRI --enz-b HindIII`.

### Cloning workflow (gene -> plasmid)

End-to-end recipe for cloning an ORF into a vector (validated with an
EcoRI/HindIII double-digest strategy):

1. Prep (Python/Biopython): parse the `.seq`, locate the ORF, list enzyme sites
   for the chosen pair, decide whether an internal site must be removed
   (silent mutation) and design primers with restriction tails.
2. DNAMAN steps, restarting the app and snapping screenshots at each key node:
   221 load -> 325 digest (linear) -> 347/348 to kill internal sites -> 325
   verify the mutated sequence -> 430 primers -> 325 on the in-silico PCR
   product -> 325 on the vector (circular) -> 325 on the recombinant
   (circular). Check the status bar after every load before continuing.
3. Ligation (pydna): `Dseqrecord(seq, circular=True).cut(EcoRI, HindIII)` ->
   pick backbone/insert -> `backbone + insert` -> `.looped()` -> verify with
   `rec.cut(...)`. pydna 5.5.16 has **no** `.ligate()`; `+` joins fragments and
   `.looped()` circularises. Fragment sizes count sticky overhangs (a 2635 bp
   backbone reports as 2639), so quote the DNAMAN numbering and the pydna
   numbering separately. Rotate the recombinant to a fixed origin (anchor on the
   vector start) so no restriction site is split across position 1.
4. Report: build a Word/Excel report with python-docx / openpyxl, including the
   screenshots, result tables and explicit notes about blocked/fallback steps
   (335, 347 limits).

Partial / blocked:

- `335 Cloning` needs an interactive DNA-map document; it opens nothing from a
  plain sequence -> use pydna/Biopython.
- `368 Charge/pH` dialog opens and computes, but the result fields are custom
  controls that `GetWindowText` cannot read -> recompute with Biopython
  (`ProtParam`); note 365 amino-acid composition already reports `Predicted pI`.
- MASED editor text cannot be copied through `Edit|Copy` from the frame; only
  the assembly editor and the pairwise result respond to the clipboard trick.
- Online BLAST (`275-279`) targets a dead NCBI interface -> use local BLAST+.

## Reporting and tests

- `python -m dnaman report` walks `%DNAMAN_RESULTS%` (including nested topic
  dirs), extracts key metrics (length, A/C/G/T, sites, longest ORF, primer-pair
  count, identity, pI, consensus length) and writes `results/summary.xlsx` with
  three sheets: `files`, `metrics`, `summary`.
- Unit tests: `python -m unittest discover -s tests -v` (21 tests covering
  config, command tables, metric extraction, fragment math, sequence reading,
  image trimming, report building). Keep them green after changes.

## Fallback tool map (optional installs)

Python: `biopython`, `primer3-py`, `pydna`, `dna-features-viewer`,
`pycirclize`, `matplotlib`, `openpyxl`, `python-docx`.

Binaries (optional, in `%DNAMAN_TOOLS%`):

| Tool | Path | Use for |
|---|---|---|
| BLAST+ 2.17.0 | `%DNAMAN_TOOLS%\ncbi-blast-2.17.0+\bin\blastn.exe`, `makeblastdb.exe` | local/offline BLAST, database search |
| MAFFT 7.526 | `%DNAMAN_TOOLS%\mafft\mafft-win\mafft.bat` | multiple sequence alignment |

| DNAMAN feature | Replacement |
|---|---|
| composition / translation / ORF | `Bio.Seq` (`translate`, custom stop-to-stop ORF scan) |
| restriction sites & maps | `Bio.Restriction` (`Analysis(batch, seq, linear=False)`), `dna_features_viewer` / `pycirclize` for figures |
| primer design, Tm, hairpins | `primer3-py` (`design_primers`, `calc_tm`, `calc_hairpin`) |
| cloning / ligation | `pydna` - `cut()` -> `backbone + insert` -> `.looped()` (no `.ligate()` in 5.5.16) |
| multiple alignment / trees | MAFFT + `Bio.Phylo` (NJ) |
| BLAST | BLAST+ `makeblastdb` / `blastn` locally |
| protein properties | `Bio.SeqUtils.ProtParam` (pI, GRAVY, composition) |
| reports | `openpyxl` for xlsx summaries; `python-docx` for Word reports with screenshots; plain txt otherwise |

## Output conventions

- Results go to `%DNAMAN_RESULTS%\<NN_topic>\` (`text.txt` for the main text
  result, `figure_*.png` for graphics, `report.txt` for derived analyses).
- Keep DNAMAN's original English wording; do not translate the result body.
- `\u7648` (U+7648) is DNAMAN's mangled `℃`; replace with `\u2103` before saving.
- Work files (extracted sequences, probes, manifests) live in `%DNAMAN_WORK%`.
- Word reports (python-docx): keep screenshots in `<topic>\screenshots\`, move
  probe shots into `screenshots\probes\`, caption every figure, and state
  DNAMAN limitations/fallbacks explicitly instead of hiding them. Set the East
  Asian font (`w:eastAsia` = 微软雅黑) on the Normal style and on each run.

## Verification checklist

1. Status bar shows the expected sequence name + length before each analysis.
2. Every exported txt is non-empty and mentions the right sequence name.
3. Figures are non-blank after trimming.
4. For numeric results (sites, ORF length, composition) run the Biopython
   cross-check and report agreement (off-by-one positions are expected: DNAMAN
   reports the base before the cut, Biopython the 1-based recognition start).
