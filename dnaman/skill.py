"""Install the bundled agent skill into an AI-agent skills directory.

Exposed both as ``python install_skill.py`` (repo root shim) and as the
``dnaman install-skill`` CLI subcommand.
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

# <repo root>/skills/<skill name>; only present in a source checkout.
_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_PACKAGE_DIR)
DEFAULT_SOURCE = os.path.join(_REPO_ROOT, "skills", SKILL_NAME)


def add_arguments(ap):
    """Add the install-skill options to an existing parser (or subparser)."""
    ap.add_argument("--target", choices=sorted(TARGETS), default="opencode",
                    help="which agent to install for (default: opencode)")
    ap.add_argument("--dest", default=None, help="explicit skills directory")
    ap.add_argument("--source", default=None,
                    help="override the skill folder to copy (default: <repo>/skills/%s)" % SKILL_NAME)
    ap.add_argument("--force", action="store_true",
                    help="overwrite an existing installation")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the destination without copying anything")
    return ap


def build_parser(prog="dnaman install-skill", add_help=True):
    ap = argparse.ArgumentParser(
        prog=prog,
        description="Install the bundled %s skill for an AI agent." % SKILL_NAME,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=add_help,
        epilog=(
            "targets:\n"
            "  opencode  ~/.config/opencode/skills (default)\n"
            "  claude    ~/.claude/skills\n"
        ),
    )
    return add_arguments(ap)


def install(target="opencode", dest=None, source=None, force=False, dry_run=False):
    """Copy the skill folder. Returns the destination path."""
    src = source or DEFAULT_SOURCE
    if not os.path.isdir(src):
        raise FileNotFoundError(
            "skill folder not found: %s\n"
            "Run this from a source checkout (git clone ...), or pass --source "
            "<path to skills/%s>." % (src, SKILL_NAME)
        )

    dest_root = dest or TARGETS[target]
    dest_path = os.path.join(dest_root, SKILL_NAME)
    if dry_run:
        return dest_path
    if os.path.exists(dest_path):
        if not force:
            raise FileExistsError(
                "already installed: %s (use --force to overwrite)" % dest_path
            )
        shutil.rmtree(dest_path)
    os.makedirs(dest_root, exist_ok=True)
    shutil.copytree(src, dest_path)
    return dest_path


def run(args):
    """Execute an already-parsed install-skill namespace. Returns an exit code."""
    try:
        dest = install(target=args.target, dest=args.dest, source=args.source,
                       force=args.force, dry_run=args.dry_run)
    except (FileNotFoundError, FileExistsError) as exc:
        print(exc, file=sys.stderr)
        return 1
    if args.dry_run:
        print("would install %s -> %s" % (SKILL_NAME, dest))
        return 0
    print("installed %s -> %s" % (SKILL_NAME, dest))
    print("restart the agent session to pick up the skill")
    return 0


def main(argv=None):
    return run(build_parser().parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
