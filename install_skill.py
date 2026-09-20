"""Install the bundled skill into an AI-agent skills directory.

Usage:
    python install_skill.py                     # opencode (default)
    python install_skill.py --target claude     # Claude Code
    python install_skill.py --dest <directory>  # custom skills directory
"""

import argparse
import os
import shutil
import sys

SKILL_NAME = "dnaman-seq-analysis"
TARGETS = {
    "opencode": os.path.join(os.path.expanduser("~"), ".config", "opencode", "skills"),
    "claude": os.path.join(os.path.expanduser("~"), ".claude", "skills"),
}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--target", choices=sorted(TARGETS), default="opencode",
                    help="which agent to install for (default: opencode)")
    ap.add_argument("--dest", default=None, help="explicit skills directory")
    ap.add_argument("--force", action="store_true", help="overwrite an existing installation")
    args = ap.parse_args(argv)

    root = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(root, "skills", SKILL_NAME)
    if not os.path.isdir(src):
        sys.exit("skill folder not found: %s" % src)

    dest_root = args.dest or TARGETS[args.target]
    dest = os.path.join(dest_root, SKILL_NAME)
    if os.path.exists(dest):
        if not args.force:
            sys.exit("already installed: %s (use --force to overwrite)" % dest)
        shutil.rmtree(dest)
    os.makedirs(dest_root, exist_ok=True)
    shutil.copytree(src, dest)
    print("installed %s -> %s" % (SKILL_NAME, dest))
    print("restart the agent session to pick up the skill")
    return 0


if __name__ == "__main__":
    sys.exit(main())
