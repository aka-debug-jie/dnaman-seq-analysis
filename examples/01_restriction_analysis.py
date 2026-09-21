"""Restriction analysis (command 325): text summary + map + pattern figures.

    python examples/01_restriction_analysis.py [sequence-file]

`sequence-file` defaults to ``insert.seq`` inside %DNAMAN_SEQ%; absolute paths
are accepted as well.
"""

import os
import sys

from dnaman import config, ops

SEQ = sys.argv[1] if len(sys.argv) > 1 else "insert.seq"
OUT = os.path.join(config.RESULTS, "insert_restriction")

# Wizard page 1 checkboxes:
#   1098 circular DNA        1099 summary text      1100 restriction map
#   1101 show enzyme position 1102 pattern figure
files = ops.run_one(
    SEQ,
    "restriction",
    outdir=OUT,
    tag="restriction",
    options={
        "dialog": "Restriction Analysis",
        "check": [1098, 1099, 1100, 1101, 1102],
    },
)

print("sequence : %s" % SEQ)
print("output   : %s" % OUT)
for path in files:
    print("  wrote %s" % os.path.basename(path))
