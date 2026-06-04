#!/usr/bin/env python3
"""
Fast File Search — Everything-like search utility.
Uses pathlib exclusively for filesystem operations with a progress bar.

Usage:
    python pythontask.py <query> [--root <dir>] [--case-sensitive] [--include-dirs]
    python pythontask.py <query> --regex
"""

import argparse
import fnmatch
import re
import sys
from pathlib import Path

from tqdm import tqdm


def count_items(root: Path) -> int:
    """Quickly estimate the number of filesystem entries under *root*."""
    try:
        return sum(1 for _ in root.rglob("*"))
    except (PermissionError, OSError):
        return 0


def match_name(name: str, query: str, case_sensitive: bool, use_regex: bool) -> bool:
    """Return True when *name* matches the query."""
    if use_regex:
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            return re.search(query, name, flags) is not None
        except re.error:
            tqdm.write(f"[error] Invalid regex: {query}")
            sys.exit(1)
    elif case_sensitive:
        return query in name
    else:
        return query.lower() in name.lower()


def walk_with_progress(
    root: Path,
    query: str,
    case_sensitive: bool = False,
    use_regex: bool = False,
    files_only: bool = True,
) -> list[Path]:
    """Walk *root* recursively, collect matches, and render a progress bar.

    The progress bar shows directories scanned so the user gets immediate
    feedback even when the total entry count isn't known yet.
    """
    results: list[Path] = []

    # ---- pre-count so tqdm can render a percentage bar --------------------
    print("Counting entries (this may take a moment for large trees)...")
    total = count_items(root)
    if total == 0:
        print("No accessible entries found under the root directory.")
        return results

    # ---- search pass ------------------------------------------------------
    with tqdm(total=total, desc="Searching", unit="entry",
              bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]") as pbar:
        try:
            for path in root.rglob("*"):
                pbar.update(1)

                if files_only and not path.is_file():
                    continue

                if match_name(path.name, query, case_sensitive, use_regex):
                    results.append(path)
                    tqdm.write(str(path))
        except (PermissionError, OSError):
            pass

    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fast file search with progress bar (Everything-like).",
    )
    parser.add_argument(
        "query",
        help="Search term (substring match by default; use --regex for regex).",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Root directory to search from (default: current working directory).",
    )
    parser.add_argument(
        "--case-sensitive", "-c",
        action="store_true",
        help="Enable case-sensitive matching.",
    )
    parser.add_argument(
        "--regex", "-r",
        action="store_true",
        help="Treat the query as a regular expression.",
    )
    parser.add_argument(
        "--include-dirs", "-d",
        action="store_true",
        help="Include directories in results (default: files only).",
    )
    parser.add_argument(
        "--glob", "-g",
        action="store_true",
        help="Treat the query as a glob/fnmatch pattern (e.g. '*.py').",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    root = args.root.expanduser().resolve()
    if not root.exists():
        print(f"Error: root directory does not exist — {root}")
        sys.exit(1)
    if not root.is_dir():
        print(f"Error: root path is not a directory — {root}")
        sys.exit(1)

    query = args.query
    files_only = not args.include_dirs

    print(f"Search root : {root}")
    print(f"Query       : {query}")
    print(f"Case sens.  : {args.case_sensitive}")
    print(f"Regex mode  : {args.regex}")
    print(f"Files only  : {files_only}")
    print("-" * 50)

    results = walk_with_progress(
        root=root,
        query=query,
        case_sensitive=args.case_sensitive,
        use_regex=args.regex,
        files_only=files_only,
    )

    print("-" * 50)
    print(f"Found {len(results)} match(es).")


if __name__ == "__main__":
    main()
