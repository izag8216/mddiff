"""CLI interface for mddiff."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from rich.console import Console

from . import __description__, __version__
from .differ import compute_diff
from .renderer import THEME, render_diff


def _read_file(path: str) -> str:
    """Read a file, exit with error if not found."""
    p = Path(path)
    if not p.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    return p.read_text(encoding="utf-8")


def _git_show(ref: str, path: str) -> str:
    """Get file content at a git ref."""
    try:
        result = subprocess.run(
            ["git", "show", f"{ref}:{path}"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
    except subprocess.CalledProcessError:
        print(f"Error: cannot read {path} at {ref}", file=sys.stderr)
        sys.exit(1)


def _git_changed_files(ref: str, glob_pattern: Optional[str] = None) -> List[str]:
    """Get list of changed markdown files between ref and HEAD."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", ref, "--"],
            capture_output=True,
            text=True,
            check=True,
        )
        files = result.stdout.strip().splitlines()
        md_files = [f for f in files if f.endswith(".md")]
        if glob_pattern:
            import fnmatch

            md_files = [f for f in md_files if fnmatch.fnmatch(f, glob_pattern)]
        return md_files
    except subprocess.CalledProcessError:
        print(f"Error: git diff failed for {ref}", file=sys.stderr)
        sys.exit(1)


def cmd_diff(args: argparse.Namespace) -> None:
    """Handle direct file diff."""
    console = Console(theme=THEME)
    old_text = _read_file(args.old)
    new_text = _read_file(args.new)
    result = compute_diff(old_text, new_text)
    render_diff(
        result,
        console=console,
        show_inline=args.inline,
        show_unchanged=args.unchanged,
        summary_only=args.summary,
        section_filter=args.section,
    )


def cmd_commit(args: argparse.Namespace) -> None:
    """Handle git commit diff."""
    console = Console(theme=THEME)
    ref = args.ref
    glob_pattern = args.glob

    files = _git_changed_files(ref, glob_pattern)
    if not files:
        console.print("[dim]No markdown files changed.[/dim]")
        return

    for filepath in files:
        old_text = _git_show(ref, filepath)
        new_path = Path(filepath)
        if not new_path.exists():
            console.print(f"[red]File deleted: {filepath}[/red]")
            continue
        new_text = new_path.read_text(encoding="utf-8")
        result = compute_diff(old_text, new_text)

        if all(d.change_type.value == "unchanged" for d in result.section_diffs):
            continue

        console.print(f"\n[bold]--- {filepath} ---[/bold]")
        render_diff(
            result,
            console=console,
            show_inline=args.inline,
            show_unchanged=args.unchanged,
            summary_only=args.summary,
            section_filter=args.section,
        )


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="mddiff",
        description=__description__,
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    parser.add_argument(
        "old_file",
        nargs="?",
        help="Old markdown file (for diff command)",
    )
    parser.add_argument(
        "new_file",
        nargs="?",
        help="New markdown file (for diff command)",
    )

    parser.add_argument(
        "--diff",
        dest="use_diff",
        action="store_true",
        help="Run diff command",
    )
    parser.add_argument(
        "--commit",
        dest="ref",
        metavar="REF",
        help="Diff markdown files changed since git REF",
    )
    parser.add_argument(
        "--glob",
        type=str,
        default=None,
        help="Glob pattern to filter files (with --commit)",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show only summary statistics",
    )
    parser.add_argument(
        "--section",
        type=str,
        default=None,
        help="Filter to sections matching this string",
    )
    parser.add_argument(
        "--inline",
        action="store_true",
        default=True,
        help="Show inline diff for modified sections (default)",
    )
    parser.add_argument(
        "--no-inline",
        dest="inline",
        action="store_false",
        help="Hide inline diff",
    )
    parser.add_argument(
        "--unchanged",
        action="store_true",
        help="Show unchanged sections too",
    )

    return parser


def main(argv: Optional[List[str]] = None) -> None:
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.ref:
        args.ref = args.ref
        cmd_commit(args)
    elif args.old_file and args.new_file:
        args.old = args.old_file
        args.new = args.new_file
        cmd_diff(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
