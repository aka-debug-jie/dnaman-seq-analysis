"""Platform-independent sequence helpers.

Everything in this module is pure Python / Biopython and has no Win32
dependency, so it can be imported and unit-tested on any operating system
(unlike the rest of the package, which drives the DNAMAN Windows GUI).
"""


def read_dnaman_seq(path):
    """Read the raw sequence out of a DNAMAN ``.seq`` / GenBank text file."""
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


def sizes_from_cuts(length, cuts, circular=True):
    """Fragment sizes produced by digesting a sequence of `length` bp.

    `cuts` are 1-based cut positions as reported by Biopython's
    ``Restriction.Analysis``.
    """
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


def restriction_fragments(seq, enzymes, circular=True):
    """{enzyme: [cut positions]} for `enzymes` on `seq` (needs Biopython)."""
    from Bio.Restriction import Analysis, RestrictionBatch
    from Bio.Seq import Seq as BioSeq

    batch = RestrictionBatch(enzymes)
    res = Analysis(batch, BioSeq(seq), linear=not circular).full()
    return {str(e): sorted(res[e]) for e in batch}
