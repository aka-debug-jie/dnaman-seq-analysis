import argparse
import os
import sys

from . import commands as C, config, ops, report, skill


def cmd_doctor(args):
    print("DNAMAN toolkit doctor")
    print("=" * 52)
    ok = True
    config.ensure_dirs()

    def check(label, cond, detail=""):
        nonlocal ok
        ok = ok and bool(cond)
        print("  %-26s %s %s" % (label, "OK" if cond else "FAIL", detail))

    def optional(label, cond, detail=""):
        print("  %-26s %s %s" % (label, "OK" if cond else "optional, not found", detail))

    check("DNAMAN.EXE", os.path.exists(config.EXE), config.EXE)
    check("sequence dir", os.path.isdir(config.SEQ_DIR), config.SEQ_DIR)
    check("results dir", os.path.isdir(config.RESULTS), config.RESULTS)
    try:
        import pywinauto

        check("pywinauto", True, pywinauto.__version__)
    except Exception as exc:
        check("pywinauto", False, str(exc))
    for mod in ("Bio", "openpyxl"):
        try:
            m = __import__(mod)
            check(mod, True, getattr(m, "__version__", ""))
        except Exception as exc:
            check(mod, False, str(exc))
    for mod in ("primer3", "pydna", "pycirclize", "dna_features_viewer", "docx",
                "matplotlib"):
        try:
            m = __import__(mod)
            optional(mod, True, getattr(m, "__version__", ""))
        except Exception as exc:
            optional(mod, False, str(exc))
    optional("BLAST+", os.path.exists(os.path.join(config.BLAST_BIN, "blastn.exe")),
             config.BLAST_BIN)
    optional("MAFFT", os.path.exists(config.MAFFT_BAT), config.MAFFT_BAT)
    try:
        n = len([f for f in os.listdir(config.SEQ_DIR) if f.endswith((".seq", ".gb"))])
        check("sequences available", n > 0, "%d files" % n)
    except Exception as exc:
        check("sequences available", False, str(exc))
    print()
    print("result:", "ALL GOOD" if ok else "PROBLEMS FOUND")
    return 0 if ok else 1


def cmd_list(args):
    for name, cid in sorted(C.CMD.items(), key=lambda kv: kv[1]):
        print("  %-24s %s" % (name, cid))
    return 0


def cmd_op(args):
    files = ops.run_one(args.seq, args.op, outdir=args.out, tag=args.tag,
                        genbank=args.genbank, protein=args.protein)
    print("files:", files)
    return 0 if files else 1


def cmd_batch(args):
    pairs = [(s, op) for s in args.seq for op in args.op]
    out = ops.batch(pairs, outroot=args.out)
    for k, v in out.items():
        print("  %-40s %d file(s)" % (k, len(v)))
    return 0


def cmd_pairwise(args):
    files = ops.run_pairwise(args.seq, outdir=args.out)
    print("files:", files)
    return 0 if files else 1


def cmd_silent(args):
    files = ops.run_silent_mutation(args.seq, start=args.start, end=args.end,
                                    outdir=args.out)
    print("files:", files)
    return 0 if files else 1


def cmd_mismatch(args):
    files = ops.run_directed_mismatch(args.seq, args.position, args.base,
                                      outdir=args.out)
    print("files:", files)
    return 0 if files else 1


def cmd_maprecon(args):
    files = ops.run_map_reconstruction(args.seq, args.enz_a, args.enz_b,
                                       circular=not args.linear, outdir=args.out)
    print("files:", files)
    return 0 if files else 1


def cmd_report(args):
    path, files, topics = report.build_excel(args.out, args.results)
    print("workbook: %s" % path)
    print("rows    : %d file(s) across %d topic(s)" % (files, topics))
    return 0


def cmd_install_skill(args):
    return skill.run(args)


def main(argv=None):
    p = argparse.ArgumentParser(prog="dnaman", description="DNAMAN 4.0 automation toolkit")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("doctor", help="check environment and dependencies")
    d.set_defaults(func=cmd_doctor)

    ls = sub.add_parser("list", help="list command names and ids")
    ls.set_defaults(func=cmd_list)

    o = sub.add_parser("op", help="run one command on one sequence")
    o.add_argument("--seq", required=True, help="sequence file name in SEQ_DIR or absolute path")
    o.add_argument("--op", required=True, help="command name or numeric id")
    o.add_argument("--out", default=None)
    o.add_argument("--tag", default=None)
    o.add_argument("--genbank", action="store_true")
    o.add_argument("--protein", action="store_true")
    o.set_defaults(func=cmd_op)

    b = sub.add_parser("batch", help="run several commands over several sequences")
    b.add_argument("--seq", nargs="+", required=True)
    b.add_argument("--op", nargs="+", required=True)
    b.add_argument("--out", default=None)
    b.set_defaults(func=cmd_batch)

    pw = sub.add_parser("pairwise", help="align two sequences via two channels (315)")
    pw.add_argument("--seq", nargs=2, required=True)
    pw.add_argument("--out", default=None)
    pw.set_defaults(func=cmd_pairwise)

    sm = sub.add_parser("silent-mutation", help="restriction silent mutation (347)")
    sm.add_argument("--seq", required=True)
    sm.add_argument("--start", default=None, help="analysis region start (keep <= ~300 bp)")
    sm.add_argument("--end", default=None, help="analysis region end")
    sm.add_argument("--out", default=None)
    sm.set_defaults(func=cmd_silent)

    dm = sub.add_parser("directed-mismatch", help="site-directed point mutation (348)")
    dm.add_argument("--seq", required=True)
    dm.add_argument("--position", required=True, help="mutation position (1-based)")
    dm.add_argument("--base", required=True, help="mutant base, e.g. G")
    dm.add_argument("--out", default=None)
    dm.set_defaults(func=cmd_mismatch)

    mr = sub.add_parser("map-reconstruction", help="reconstruct a map from a double digest (340)")
    mr.add_argument("--seq", required=True)
    mr.add_argument("--enz-a", required=True)
    mr.add_argument("--enz-b", required=True)
    mr.add_argument("--linear", action="store_true")
    mr.add_argument("--out", default=None)
    mr.set_defaults(func=cmd_maprecon)

    r = sub.add_parser("report", help="summarise results/ into an Excel workbook")
    r.add_argument("--out", default=None)
    r.add_argument("--results", default=None)
    r.set_defaults(func=cmd_report)

    s = sub.add_parser("install-skill", parents=[skill.build_parser(add_help=False)],
                       help="install the bundled AI-agent skill")
    s.set_defaults(func=cmd_install_skill)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
