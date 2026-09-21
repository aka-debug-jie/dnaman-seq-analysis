"""PCR primer design (command 430) with relaxed acceptance limits.

    python examples/02_primer_design.py [sequence-file]

DNAMAN's defaults (product 400-600 bp, length 18-21, Tm 62-65, GC 40-60) are too
narrow for full-ORF cloning primers, so the limits are widened here.

Two caveats from `skills/dnaman-seq-analysis/SKILL.md`:

* the **product-size range** is the reliable way to pin the antisense primer
  end - the antisense "from/to" window semantics are not;
* the `3' Unique (base) < 6` filter silently drops primers whose 3'-terminal 6
  bases are not unique, which is often why an ATG-start primer is missing.
"""

import os
import sys

from dnaman import config, ops

SEQ = sys.argv[1] if len(sys.argv) > 1 else "gene.seq"
OUT = os.path.join(config.RESULTS, "pcr_primers")

# Page 1 ("Primer filtration") control ids: 1000/1001 product size,
# 1007/1008 primer length, 1009/1010 Tm, 1011/1012 GC%.
LIMITS = {
    1000: 300, 1001: 1200,     # product size range (bp)
    1007: 18, 1008: 25,        # primer length (nt)
    1009: 50, 1010: 85,        # Tm (C)
    1011: 35, 1012: 85,        # GC content (%)
}

files = ops.run_one(
    SEQ,
    "pcr_primers",
    outdir=OUT,
    tag="pcr_primers",
    options={"dialog": "Primer filtration", "set": LIMITS},
)

print("sequence : %s" % SEQ)
print("output   : %s" % OUT)
for path in files:
    print("  wrote %s" % os.path.basename(path))
print()
print("Remember to append the restriction tails yourself, e.g. CGGGAATTC... / CCCAAGCTT...")
