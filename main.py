"""Weirdest job title entry for make.fun.

Writes the single job title to entry.txt in the output directory
($MAKEFUN_OUTPUT_DIR, default /output). Stdlib only, deterministic, no
network and no side effects beyond the one output file.

Gate (from the competition rules): /output/entry.txt must be UTF-8 text
of 1 to 60 characters, a single line, not only white space. The entry is
written with no trailing newline so the file holds exactly the judged
line.

Modes:
  (default)   validate ENTRY, write it, read it back, confirm byte-identical
  --check     validate ENTRY only and exit; writes nothing
  --self-test validate ENTRY and check a byte-identical write/read
              round-trip in a temporary directory, then exit
"""

import argparse
import os
import sys

ENTRY = "Senior Manager of Apologizing to Angry Geese"

MAX_CHARS = 60


def _check_spacing(text: str) -> list[str]:
    """Reject sloppy spacing: double spaces or leading/trailing blanks.

    A job title is printed verbatim, so an accidental double space or a
    stray leading/trailing blank would show up in the judged text. Keep
    the check strict even though the entry itself is fixed.
    """
    problems = []
    if text != text.strip():
        problems.append("entry has leading or trailing whitespace")
    if "  " in text:
        problems.append("entry contains a double space")
    return problems


def _check_punctuation(text: str) -> list[str]:
    """Reject a title that ends mid-thought or with stray punctuation."""
    problems = []
    if text.rstrip().endswith((",", ";", ":")):
        problems.append("entry ends with trailing clause punctuation")
    return problems


def validate(text: str) -> list[str]:
    """Return a list of gate failures for `text` (empty means valid)."""
    problems = []
    if not 1 <= len(text) <= MAX_CHARS:
        problems.append(f"length {len(text)} chars, must be 1-{MAX_CHARS}")
    if not text.strip():
        problems.append("entry is only white space")
    if "\n" in text:
        problems.append("entry must be a single line")
    problems.extend(_check_spacing(text))
    problems.extend(_check_punctuation(text))
    try:
        text.encode("utf-8")
    except UnicodeEncodeError as exc:  # pragma: no cover - defensive
        problems.append(f"not encodable as UTF-8: {exc}")
    return problems


def write_entry(out_dir: str) -> str:
    """Write ENTRY to entry.txt under `out_dir`; return the file path."""
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.txt")
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(ENTRY)
    return path


def self_test() -> int:
    """Validate ENTRY, write it to a temp dir, read it back, compare bytes."""
    import tempfile

    problems = validate(ENTRY)
    if problems:
        print("self-test FAIL: " + "; ".join(problems), file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory() as tmp:
        path = write_entry(tmp)
        with open(path, "rb") as f:
            raw = f.read()
        if raw != ENTRY.encode("utf-8"):
            print("self-test FAIL: read-back bytes differ from ENTRY",
                  file=sys.stderr)
            return 1
        if raw.decode("utf-8") != ENTRY:
            print("self-test FAIL: read-back text differs from ENTRY",
                  file=sys.stderr)
            return 1
    print(f"self-test OK: {len(ENTRY)} chars, single line, "
          f"byte-identical round-trip")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=None,
                        help="output directory (default: "
                             "$MAKEFUN_OUTPUT_DIR or /output)")
    parser.add_argument("--self-test", action="store_true",
                        help="validate ENTRY and check a byte-identical "
                             "write/read round-trip, then exit")
    parser.add_argument("--check", action="store_true",
                        help="validate ENTRY only (no file written) and exit")
    args = parser.parse_args(argv)

    if args.check:
        problems = validate(ENTRY)
        if problems:
            print("check FAIL: " + "; ".join(problems), file=sys.stderr)
            return 1
        print(f"check OK: ENTRY valid ({len(ENTRY)} chars)")
        return 0

    if args.self_test:
        return self_test()

    problems = validate(ENTRY)
    if problems:
        print("invalid ENTRY: " + "; ".join(problems), file=sys.stderr)
        return 1

    out_dir = args.out or os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    path = write_entry(out_dir)
    # Read back and confirm the file holds exactly the entry.
    with open(path, encoding="utf-8") as f:
        if f.read() != ENTRY:
            print(f"read-back mismatch in {path}", file=sys.stderr)
            return 1
    print(f"wrote {path} ({len(ENTRY)} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
