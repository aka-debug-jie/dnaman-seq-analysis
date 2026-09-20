import json
import os
import time

from . import app, commands as C, config, dialogs, results
from .win32 import (BM_GETCHECK, WM_COMMAND, child_by_id, child_windows, class_of,
                    click, enabled, set_edit_value, text_of, top_windows, u32,
                    visible, wait_for)

LOG_PATH = os.path.join(config.LOG_DIR, "runs.jsonl")


def _log_run(record):
    try:
        os.makedirs(config.LOG_DIR, exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass


def cmd_id(name):
    if isinstance(name, int):
        return name
    if name not in C.CMD:
        raise KeyError("unknown command %r" % name)
    return C.CMD[name]


class Session:
    """One DNAMAN instance. Always restarts (channel must be empty to load)."""

    def __init__(self, log=print):
        self.log = log
        self.app = None
        self.win = None
        self.main_h = None
        self.pid = None

    def __enter__(self):
        config.ensure_dirs()
        app.kill()
        self.app, self.win, self.main_h, self.pid = app.launch()
        dialogs.close_stray_dialogs(self.pid)
        return self

    def __exit__(self, *exc):
        app.kill()
        return False

    # ---------------- loading ----------------

    def load(self, seqfile, genbank=False, protein=False, timeout=25):
        path = config.seq_path(seqfile)
        cmd = C.CMD["load_genbank"] if genbank else C.CMD["load_from_file"]
        dialogs.open_file_dialog(self.pid, self.main_h, cmd, path, timeout=timeout)
        if genbank:
            names = dialogs.handle_genbank_dialog(self.pid, timeout=timeout)
            self.log("  genbank entries: %s" % names)
        if protein:
            answered = dialogs.handle_sequence_type(self.pid, protein=True, timeout=15)
            self.log("  protein prompt answered: %s" % answered)
        time.sleep(0.8)
        status = app.status_text(self.main_h)
        self.log("  loaded %s -> %s" % (os.path.basename(path), status))
        return status

    def load_multiple(self, seqfiles, timeout=30):
        """Load several sequences into successive channels (menu: Load Sequence | Multiple).

        The common file dialog accepts the Windows multi-select syntax
        '"path1" "path2"'. DNAMAN then reports 'N Sequences'; channel 1 holds the
        first file. Commands with the 'All DNA in sequence channels' option (1103)
        operate on all of them.
        """
        paths = [config.seq_path(f) for f in seqfiles]
        quoted = " ".join('"%s"' % p for p in paths)
        dialogs.open_file_dialog(self.pid, self.main_h, C.CMD["load_multiple"],
                                 quoted, timeout=timeout)
        time.sleep(3.5)
        msg = app.message_text(self.pid)
        if msg:
            self.log("  %s" % msg)
            app.dismiss_message(self.pid)
        time.sleep(2.0)
        status = app.status_text(self.main_h)
        self.log("  loaded %d sequences -> %s" % (len(paths), status))
        return status

    # ---------------- running ----------------

    def run(self, name, outdir, tag="result", options=None, budget=15.0,
            settle=1.2, timeout=40):
        cid = cmd_id(name)
        os.makedirs(outdir, exist_ok=True)
        dialogs.reset_wizard_state()
        before = results.docs(self.win)
        u32.PostMessageW(self.main_h, WM_COMMAND, cid, 0)
        time.sleep(settle)

        if options:
            dlg = wait_for(
                lambda: next((h for h in top_windows(self.pid)
                              if options["dialog"] in text_of(h)), None),
                timeout=15,
            )
            if dlg:
                handler = options.get("handler")
                if handler:
                    handler(self, dlg)
                for cid2 in options.get("check", []):
                    h = child_by_id(dlg, cid2)
                    if h and u32.SendMessageW(h, BM_GETCHECK, 0, 0) == 0:
                        click(h)
                        time.sleep(0.3)
                for cid2, value in (options.get("set", {}) or {}).items():
                    h = child_by_id(dlg, int(cid2))
                    if h:
                        from .win32 import type_text

                        type_text(h, str(value))

        deadline = time.time() + timeout
        new = {}
        first_seen = None
        while time.time() < deadline:
            dialogs.handle_wizard(self.pid, budget=1.5, log=self.log)
            after = results.docs(self.win)
            for h, v in after.items():
                if h not in before:
                    new[h] = v
            if new and first_seen is None:
                first_seen = time.time()
            if first_seen and time.time() - first_seen >= 3.0:
                break
            time.sleep(0.4)
        new = list(new.items())

        msg = app.message_text(self.pid)
        if msg:
            self.log("  message: %s" % msg)
            app.dismiss_message(self.pid)
            time.sleep(1.0)

        written = self._export(new, outdir, tag)
        _log_run({
            "seq": getattr(self, "current_seq", None),
            "cmd": cid, "name": name if isinstance(name, str) else str(name),
            "tag": tag, "files": written, "message": msg,
        })
        return written

    def _export(self, new, outdir, tag):
        written = []
        rich_map = {}
        for h, (cls, title) in new:
            r = results.rich_of(h)
            if r and r not in rich_map:
                rich_map[r] = title
        for r, title in rich_map.items():
            txt = results.read_text(r)
            if txt:
                p = os.path.join(outdir, tag + ".txt")
                results.save_text(txt, p)
                self.log("    %s.txt (%d chars)" % (tag, len(txt)))
                written.append(p)
        for h, (cls, title) in new:
            if not cls.startswith("Afx:400000:b") or not title.strip() or results.rich_of(h):
                continue
            from .win32 import maximize

            maximize(h)
            safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in title)[:24]
            p = os.path.join(outdir, "%s_%s.png" % (tag, safe))
            if results.capture_png(h, p):
                results.trim(p)
                self.log("    %s" % os.path.basename(p))
                written.append(p)
        return written


def run_pairwise(seqfiles, outdir=None, tag="pairwise_alignment", log=print):
    """Align two sequences that are loaded into two channels (menu 315).

    Returns the exported files (RICHEDIT text alignment)."""
    if len(seqfiles) != 2:
        raise ValueError("run_pairwise expects exactly 2 sequence files")
    outdir = outdir or os.path.join(config.RESULTS, "pairwise")
    with Session(log=log) as s:
        s.current_seq = "+".join(seqfiles)
        s.load_multiple(seqfiles)
        return s.run("align_two", outdir, tag=tag)


def run_silent_mutation(seqfile, start=None, end=None, outdir=None,
                        tag="silent_mutation", log=print):
    """Restriction | Silent Mutation (347).

    `&Seq` only fills the region with 1-300, so pass start/end around the
    target site; regions larger than ~200-300 bp crash DNAMAN.
    """
    outdir = outdir or os.path.join(config.RESULTS, "silent_mutation")

    def handler(session, dlg):
        seqbtn = child_by_id(dlg, 1254)
        if seqbtn:
            click(seqbtn)
            time.sleep(1.0)
        if start is not None and end is not None:
            e1 = child_by_id(dlg, 1255)
            e2 = child_by_id(dlg, 1256)
            if e1 and e2:
                set_edit_value(e1, start)
                set_edit_value(e2, end)
                log("  region %s..%s" % (start, end))

    with Session(log=log) as s:
        s.current_seq = seqfile
        s.load(seqfile)
        return s.run("silent_mutation", outdir, tag=tag,
                     options={"dialog": "Silent Mutation", "handler": handler})


def run_directed_mismatch(seqfile, position, base, outdir=None,
                          tag="directed_mismatch", log=print):
    """Restriction | Directed Mismatch (348): mutate `position` to `base`.

    The result is a report (mutant context + affected enzymes), not a mutated
    sequence document; apply the change with a script and re-verify with 325.
    """
    outdir = outdir or os.path.join(config.RESULTS, "directed_mismatch")

    def handler(session, dlg):
        e_pos = child_by_id(dlg, 1265)
        e_base = child_by_id(dlg, 1258)
        if e_pos:
            set_edit_value(e_pos, position)
        if e_base:
            set_edit_value(e_base, base)
        log("  mutation at %s for %s" % (position, base))

    with Session(log=log) as s:
        s.current_seq = seqfile
        s.load(seqfile)
        return s.run("directed_mismatch", outdir, tag=tag,
                     options={"dialog": "Directed Mismatch", "handler": handler})


def _restriction_fragments(seq, enzymes, circular=True):
    from Bio.Restriction import Analysis, RestrictionBatch
    from Bio.Seq import Seq as BioSeq

    batch = RestrictionBatch(enzymes)
    res = Analysis(batch, BioSeq(seq), linear=not circular).full()
    sites = {str(e): sorted(res[e]) for e in batch}
    return sites


def _sizes_from_cuts(length, cuts, circular=True):
    cuts = sorted(set(cuts))
    if not cuts:
        return [length]
    if circular:
        out = []
        for i in range(len(cuts)):
            a, b = cuts[i], cuts[(i + 1) % len(cuts)]
            out.append((b - a) % length or length)
        return out
    out = [cuts[0] - 1]
    for i in range(1, len(cuts)):
        out.append(cuts[i] - cuts[i - 1])
    out.append(length - cuts[-1] + 1)
    return out


def run_map_reconstruction(seqfile, enz_a, enz_b, circular=True, outdir=None,
                           tag="map_reconstruction", log=print):
    """Restriction | Map Reconstruction (340): fill the fragment grid from a
    computed double digest and let DNAMAN reconstruct the map."""
    outdir = outdir or os.path.join(config.RESULTS, "map_reconstruction")
    seq = _read_dnaman_seq(config.seq_path(seqfile))
    sites = _restriction_fragments(seq, [enz_a, enz_b], circular=circular)
    frag_a = _sizes_from_cuts(len(seq), sites[enz_a], circular)
    frag_b = _sizes_from_cuts(len(seq), sites[enz_b], circular)
    frag_ab = _sizes_from_cuts(len(seq), sites[enz_a] + sites[enz_b], circular)
    log("  %s=%s  %s=%s  both=%s" % (enz_a, frag_a, enz_b, frag_b, frag_ab))

    def handler(session, dlg):
        from .win32 import type_text

        for col_base, sizes in ((1001, frag_a), (1011, frag_b), (1021, frag_ab)):
            for i, size in enumerate(sorted(sizes, reverse=True)[:10]):
                h = child_by_id(dlg, col_base + i)
                if h:
                    type_text(h, "%.3f" % (size / 1000.0), delay=0.02)

    with Session(log=log) as s:
        s.current_seq = seqfile
        s.load(seqfile)
        return s.run("map_reconstruction", outdir, tag=tag,
                     options={"dialog": "Map Reconstruction", "handler": handler})


def _read_dnaman_seq(path):
    out = []
    started = False
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = fh.read().splitlines()
    for line in lines:
        if line.startswith("ORIGIN"):
            started = True
            continue
        if started and line.strip():
            parts = line.split(None, 1)
            if len(parts) > 1:
                out.append(parts[1].replace(" ", ""))
    return "".join(out)


def run_one(seqfile, op, outdir=None, tag=None, genbank=False, protein=False,
            options=None, log=print):
    """Restart -> load -> run one command -> export. Returns list of files."""
    with Session(log=log) as s:
        s.current_seq = seqfile
        s.load(seqfile, genbank=genbank, protein=protein)
        name = op if isinstance(op, str) else "cmd%s" % op
        out = outdir or os.path.join(config.RESULTS, name)
        return s.run(op, out, tag=tag or name, options=options)


def batch(pairs, outroot=None, log=print):
    """pairs: [(seqfile, op_name_or_id), ...] -> {key: files}"""
    out = {}
    for seqfile, op in pairs:
        seq = os.path.splitext(os.path.basename(seqfile))[0]
        name = op if isinstance(op, str) else "cmd%s" % op
        outdir = os.path.join(outroot or config.RESULTS, name)
        try:
            out["%s:%s" % (seq, name)] = run_one(seqfile, op, outdir=outdir,
                                                 tag=name, log=log)
        except Exception as exc:
            log("  ERROR %s %s: %s" % (seq, name, exc))
            out["%s:%s" % (seq, name)] = []
    return out
