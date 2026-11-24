"""Weirdest job title entry for make.fun.

Writes the single job title to entry.txt in the output directory
($MAKEFUN_OUTPUT_DIR, default /output). Stdlib only, deterministic, no
network and no side effects beyond the one output file.

The title is assembled from its three beats (frame + duty + target) so
the corporate-job-title shape is visible in the source instead of being
one opaque string, and it is written out as UTF-8 bytes so the file
holds exactly the judged line.

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

# The title in its three beats: the corporate frame, the duty, and the
# target of the duty. Joined with single spaces; the result is the
# judged line, byte for byte.
_TITLE_BEATS = ("Senior Manager of", "Apologizing to", "Angry Geese")
ENTRY = " ".join(_TITLE_BEATS)

MAX_CHARS = 60
FRAME_PREFIX = "Senior Manager of "


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


def _check_length(text: str) -> list[str]:
    """Reject a title outside the competition's 1-60 character gate."""
    if not 1 <= len(text) <= MAX_CHARS:
        return [f"length {len(text)} chars, must be 1-{MAX_CHARS}"]
    return []


def _check_single_line(text: str) -> list[str]:
    """Reject anything that is not exactly one line of text."""
    problems = []
    if not text.strip():
        problems.append("entry is only white space")
    if "\n" in text or "\r" in text:
        problems.append("entry must be a single line")
    return problems


def _check_frame(text: str) -> list[str]:
    """Reject a title that lost its corporate-frame shape.

    The joke only works as a job title if it still reads like one, so
    the frame prefix and a non-empty duty after it are part of the gate.
    """
    problems = []
    if not text.startswith(FRAME_PREFIX):
        problems.append("entry must start with the 'Senior Manager of ' frame")
    elif not text[len(FRAME_PREFIX):].strip():
        problems.append("entry has an empty duty after the frame")
    return problems


# Every check runs on the same text; validate() just collects them.
_CHECKS = (_check_length, _check_single_line, _check_spacing,
           _check_punctuation, _check_frame)


def validate(text: str) -> list[str]:
    """Return a list of gate failures for `text` (empty means valid)."""
    problems = []
    for check in _CHECKS:
        problems.extend(check(text))
    try:
        text.encode("utf-8")
    except UnicodeEncodeError as exc:  # pragma: no cover - defensive
        problems.append(f"not encodable as UTF-8: {exc}")
    return problems


def write_entry(out_dir: str) -> str:
    """Write ENTRY to entry.txt under `out_dir`; return the file path.

    Written as UTF-8 bytes (not text mode) so no platform newline
    translation can sneak a trailing newline into the judged line.
    """
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.txt")
    with open(path, "wb") as f:
        f.write(ENTRY.encode("utf-8"))
    return path


def self_test() -> int:
    """Validate ENTRY, write it twice, read both back, compare bytes."""
    problems = validate(ENTRY)
    if problems:
        print("self-test FAIL: " + "; ".join(problems), file=sys.stderr)
        return 1
    expected = ENTRY.encode("utf-8")
    if expected.endswith(b"\n"):
        print("self-test FAIL: ENTRY ends with a newline", file=sys.stderr)
        return 1
    import tempfile

    written = []
    for _ in range(2):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_entry(tmp)
            with open(path, "rb") as f:
                raw = f.read()
            if raw != expected:
                print("self-test FAIL: read-back bytes differ from ENTRY",
                      file=sys.stderr)
                return 1
            if len(raw) != len(expected):
                print("self-test FAIL: read-back size differs from ENTRY",
                      file=sys.stderr)
                return 1
            written.append(raw)
    if written[0] != written[1]:
        print("self-test FAIL: two writes differ (not deterministic)",
              file=sys.stderr)
        return 1
    print(f"self-test OK: {len(ENTRY)} chars, single line, "
          f"byte-identical round-trip (x2, deterministic)")
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
    # Read back as raw bytes and confirm the file holds exactly the entry.
    with open(path, "rb") as f:
        if f.read() != ENTRY.encode("utf-8"):
            print(f"read-back mismatch in {path}", file=sys.stderr)
            return 1
    print(f"wrote {path} ({len(ENTRY)} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
