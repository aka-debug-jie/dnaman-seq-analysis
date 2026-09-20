import os

_CANDIDATE_DIRS = [
    os.environ.get("DNAMAN_DIR"),
    r"C:\Program Files (x86)\DNAMAN",
    r"C:\Program Files\DNAMAN",
    r"C:\DNAMAN",
    r"D:\DNAMAN",
    r"D:\Program Files\DNAMAN",
    r"D:\Program Files (x86)\DNAMAN",
]


def _find_dnaman_dir():
    for d in _CANDIDATE_DIRS:
        if d and os.path.exists(os.path.join(d, "DNAMAN.EXE")):
            return d
    return r"C:\Program Files (x86)\DNAMAN"


DN_DIR = os.environ.get("DNAMAN_DIR") or _find_dnaman_dir()
EXE = os.path.join(DN_DIR, "DNAMAN.EXE")

BASE = os.environ.get("DNAMAN_BASE", os.path.join(os.path.expanduser("~"), "DNAMAN"))
WORK = os.environ.get("DNAMAN_WORK", os.path.join(BASE, "work"))
SEQ_DIR = os.environ.get("DNAMAN_SEQ", os.path.join(WORK, "seq"))
RESULTS = os.environ.get("DNAMAN_RESULTS", os.path.join(BASE, "results"))
TOOLS = os.environ.get("DNAMAN_TOOLS", os.path.join(BASE, "tools"))
LOG_DIR = os.environ.get("DNAMAN_LOGS", os.path.join(WORK, "logs"))

BLAST_BIN = os.path.join(TOOLS, "ncbi-blast-2.17.0+", "bin")
MAFFT_BAT = os.path.join(TOOLS, "mafft", "mafft-win", "mafft.bat")


def seq_path(name):
    return name if os.path.isabs(name) else os.path.join(SEQ_DIR, name)


def ensure_dirs():
    for d in (WORK, SEQ_DIR, RESULTS, LOG_DIR):
        os.makedirs(d, exist_ok=True)
