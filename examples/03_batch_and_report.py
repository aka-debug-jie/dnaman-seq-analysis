"""Run several analyses, then summarise `%DNAMAN_RESULTS%` into an Excel book.

    python examples/03_batch_and_report.py [sequence-file]

Each pair is one (sequence, analysis) job; `ops.batch` keeps going when a single
job fails and records the exception in the run log.
"""

import os
import sys

from dnaman import config, ops, report

SEQ = sys.argv[1] if len(sys.argv) > 1 else "insert.seq"

# (sequence file, command name or numeric menu id)
JOBS = [
    (SEQ, "composition"),   # 251
    (SEQ, "orf"),           # 300
    (SEQ, "translation"),   # 355
    (SEQ, "restriction"),   # 325
]

results = ops.batch(JOBS)
print("analyses")
for key, files in results.items():
    print("  %-28s %d file(s)" % (key, len(files)))

# report.build_excel() defaults to %DNAMAN_RESULTS%/summary.xlsx, walking every
# topic folder underneath %DNAMAN_RESULTS%.
path, n_files, n_topics = report.build_excel()
print()
print("workbook : %s" % path)
print("rows     : %d file(s) across %d topic(s)" % (n_files, n_topics))
print("log      : %s" % os.path.join(config.LOG_DIR, "runs.jsonl"))
