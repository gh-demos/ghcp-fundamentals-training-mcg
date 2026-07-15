#!/usr/bin/env python3
"""
Quick log triage utility.

Features:
- Accepts .log or .log.gz files
- Filters events from the last N minutes
- Tallies (status-code, endpoint) pairs
- Optional status-code filtering (for example: --status 499,321)
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, NamedTuple
import argparse
import gzip
import re
import sys


class ParsedLine(NamedTuple):
    timestamp_utc: datetime
    status: int
    path: str


# Common/combined log pattern:
# 127.0.0.1 - - [15/Jul/2025:14:23:41 +0000] "GET /health HTTP/1.1" 200 123
LOG_PATTERN = re.compile(
    r"^(?P<ip>\S+) \S+ \S+ "
    r"\[(?P<timestamp>[^\]]+)\] "
    r'"(?P<method>\S+) (?P<path>\S+) \S+" '
    r"(?P<status>\d{3}) \S+"
)


def read_lines(file_path: Path) -> Iterable[str]:
    """Yield stripped lines from a .log or .log.gz file."""
    opener = gzip.open if file_path.suffix == ".gz" else open
    with opener(file_path, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            yield line.rstrip("\n")


def parse_line(line: str) -> ParsedLine | None:
    """Return parsed line fields or None for malformed lines."""
    match = LOG_PATTERN.match(line)
    if not match:
        return None

    ts_raw = match.group("timestamp")
    try:
        timestamp = datetime.strptime(ts_raw, "%d/%b/%Y:%H:%M:%S %z")
    except ValueError:
        return None

    return ParsedLine(
        timestamp_utc=timestamp.astimezone(timezone.utc),
        status=int(match.group("status")),
        path=match.group("path"),
    )


def triage(
    lines: Iterable[str],
    minutes: int,
    wanted_status: set[int] | None,
) -> Counter[tuple[int, str]]:
    """Aggregate counts for lines within the time window and status filter."""
    counter: Counter[tuple[int, str]] = Counter()
    now_utc = datetime.now(timezone.utc)
    lower_bound = now_utc - timedelta(minutes=minutes)

    for line in lines:
        parsed = parse_line(line)
        if parsed is None:
            continue

        if parsed.timestamp_utc < lower_bound:
            continue

        if wanted_status is not None and parsed.status not in wanted_status:
            continue

        counter[(parsed.status, parsed.path)] += 1

    return counter


def render(counter: Counter[tuple[int, str]], top: int) -> None:
    """Print top offenders as a markdown table."""
    print("| Rank | Status | Path | Hits |")
    print("|------|--------|------|------|")

    for rank, ((status, path), hits) in enumerate(counter.most_common(top), start=1):
        print(f"| {rank} | {status} | {path} | {hits} |")


def parse_status_filter(status_arg: str | None) -> set[int] | None:
    """Parse comma-separated status filter into a set of integer codes."""
    if not status_arg:
        return None

    values = set()
    for raw in status_arg.split(","):
        token = raw.strip()
        if not token:
            continue

        if not token.isdigit() or len(token) != 3:
            raise ValueError(f"Invalid status code: {token}")

        values.add(int(token))

    return values or None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Quick log triage utility")
    parser.add_argument(
        "file",
        nargs="?",
        type=Path,
        help="Path to .log or .log.gz file (positional)",
    )
    parser.add_argument(
        "--file",
        dest="file_opt",
        type=Path,
        default=None,
        help="Path to .log or .log.gz file",
    )
    parser.add_argument(
        "--minutes",
        type=int,
        default=15,
        help="Time window in minutes (default: 15)",
    )
    parser.add_argument(
        "--status",
        type=str,
        default=None,
        help="Comma-separated status codes to include, for example: 499,321",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of rows to print (default: 10)",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    file_path: Path | None = args.file_opt or args.file
    if file_path is None:
        parser.error("a log file is required (positional file or --file)")

    if args.minutes <= 0:
        parser.error("--minutes must be greater than 0")

    if args.top <= 0:
        parser.error("--top must be greater than 0")

    if not file_path.exists():
        parser.error(f"File not found: {file_path}")

    valid_suffixes = (".log", ".log.gz")
    file_name = file_path.name
    if not any(file_name.endswith(s) for s in valid_suffixes):
        parser.error("Input must be a .log or .log.gz file")

    try:
        wanted_status = parse_status_filter(args.status)
    except ValueError as exc:
        parser.error(str(exc))

    counts = triage(read_lines(file_path), args.minutes, wanted_status)

    if not counts:
        print("No matching log entries found.", file=sys.stderr)
        return 1

    render(counts, args.top)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
