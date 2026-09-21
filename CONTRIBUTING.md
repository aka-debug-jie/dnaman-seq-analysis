# Contributing

Thanks for helping make DNAMAN drivable. This project automates a 1990s 32-bit
Windows GUI, so a few rules are less obvious than usual.

## Development setup

Windows is required to run anything that touches the GUI. Everything else
(lint, the platform-free tests, packaging) works anywhere.

```powershell
git clone https://github.com/aka-debug-jie/dnaman-seq-analysis.git
cd dnaman-seq-analysis
pip install -e ".[all]"
pip install ruff
```

You also need a legally installed copy of DNAMAN 4.0 to exercise real
operations, plus your own `.seq` / GenBank files in `%DNAMAN_SEQ%`.

## Tests

```powershell
python -m unittest discover -s tests -v    # all 26
python -m unittest discover -s tests -p "test_platform_free.py" -v   # 18, any OS
ruff check dnaman tests examples install_skill.py
```

- `tests/test_platform_free.py` - `commands`, `config`, `report`, `seqmath`.
  No Win32, no DNAMAN, runs on Linux and on CI.
- `tests/test_windows.py` - anything importing `ops` / `results` / `win32`.
  Nothing there launches the GUI; keep it that way so CI stays fast and safe.

Keep the two files split. If a new test needs the Win32 layer, it belongs in
`test_windows.py`.

## Layout

```
dnaman/
  win32.py       ctypes primitives (user32 / gdi32); the only place that is
                 hard Windows-only
  app.py         launch / kill / status bar / message boxes
  dialogs.py     common file dialog, GenBank dialog, Sequence Type prompt, wizard driver
  results.py     RICHEDIT text, PrintWindow screenshots, clipboard
  seqmath.py     platform-free sequence reading + fragment arithmetic
  commands.py    menu command ids and dialog control ids  <- extend here first
  config.py      environment-driven paths
  ops.py         Session, run_one, batch and the multi-step flows (315/340/347/348)
  skill.py       installs the bundled agent skill
  cli.py         argparse front end
  report.py      results/ -> summary.xlsx
  _version.py    the single source of the version
```

Modules that need Win32 are imported lazily (`dnaman/__init__.py`), so
`import dnaman` must keep working on non-Windows platforms. Do not add eager
imports of `win32` / `app` / `dialogs` / `ops` / `results` to `__init__.py`.

## Adding a DNAMAN operation

1. Add the menu command id to `CMD` in `dnaman/commands.py` (verify it by hand
   first - the ids are not documented anywhere by Lynnon BioSoft).
2. Add the dialog control ids to `DLG` if the operation opens a dialog.
3. Try it through the generic helpers before writing a new function:

   ```python
   ops.run_one("insert.seq", "composition")
   ops.run_one("insert.seq", "pcr_primers",
               options={"dialog": "Primer filtration", "set": {1000: 300}})
   ```

   `options` supports `dialog` (substring of the window title), `check`
   (checkbox ids to tick), `set` ({control id: value}, written with
   `set_edit_value`) and `handler` (a callable for anything custom).
4. Only add a dedicated `run_*` helper when the operation needs a multi-step
   interaction that the generic path cannot express.
5. Document what actually happened in `skills/dnaman-seq-analysis/SKILL.md`
   - including the failure modes. That file is the authoritative reference;
   the README deliberately does not duplicate it.

## Automation rules you must not break

- Never `SendMessage(BM_CLICK)` a button that opens a modal dialog - use
  `win32.click()` (async `PostMessage`), otherwise the call blocks forever.
- Take the `results.docs()` baseline **before** sending the menu command, and
  keep polling for a few seconds after the first result window appears.
- `SetWindowText` does not update DNAMAN's internal model for a range of custom
  edit fields; use `win32.set_edit_value` (`EM_SETSEL` + `WM_CHAR`).
- Restart DNAMAN between sequence loads. Loading into an occupied channel fails
  silently.
- Never claim a result you did not read back from the screen or clipboard.

## Commits and pull requests

- One focused change per commit; imperative subject line, body explaining why.
- Run `ruff check` and the platform-free suite before pushing. CI runs the full
  suite on Windows 3.9 / 3.11 / 3.12.
- Update `CHANGELOG.md` under `[Unreleased]` for anything user-visible.

## Legal

Do not commit DNAMAN binaries, licence files, screenshots of the DNAMAN UI, or
sequence data you are not allowed to publish. The repository must stay
redistributable under MIT.
