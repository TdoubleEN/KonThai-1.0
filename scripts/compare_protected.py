#!/usr/bin/env python3
"""Read-only surface comparison, not semantic, factual, or date verification.

Thai digits, comma thousands, decimal zeroes and known unit aliases normalize.
Bare line-start ordered-list markers (``1. `` / ``1) ``) are ignored: use
--protect to retain an exact marker when it is data. URLs and hashtags are
checked separately, excluding their embedded digits from the number counts.
Explicit strings are case-sensitive, non-overlapping occurrences (str.count).
Only adjacent, known units are bound to numbers; labels and sentence meanings
are not understood. A same-number swap between unrecognized labels may pass.
"""

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys
import unicodedata


DIGITS = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")
NUMBER = re.compile(r"(?<![0-9.])[-+−]?(?:[0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?|\.[0-9]+)")
URL = re.compile(r"(?:https?://|www\.)[^\s<>\"“”]+", re.IGNORECASE)
LIST_MARKER = re.compile(r"(?m)^\s*[0-9]+[.)](?=[ \t]+)")
UNIT_GROUPS = {
    "ml": ("ml", "mL", "ML", "มล.", "มล", "มิลลิลิตร"),
    "l": ("l", "L", "ลิตร"),
    "g": ("g", "กรัม"),
    "kg": ("kg", "กก.", "กก", "กิโลกรัม"),
    "bar": ("bar", "bars", "บาร์"),
    "THB": ("บาท", "THB", "฿"),
    "%": ("%", "เปอร์เซ็นต์"),
    "°C": ("°C", "° C", "องศาเซลเซียส"),
    "W": ("W", "วัตต์"),
    "kW": ("kW", "กิโลวัตต์"),
    "mm": ("mm", "มม.", "มิลลิเมตร"),
    "cm": ("cm", "ซม.", "เซนติเมตร"),
    "m": ("m", "เมตร"),
    "s": ("s", "sec", "วินาที"),
    "min": ("min", "นาที"),
    "h": ("h", "hr", "ชั่วโมง"),
}
UNIT_ALIASES = {alias: unit for unit, aliases in UNIT_GROUPS.items() for alias in aliases}
UNIT = re.compile(r"[ \t]*(" + "|".join(re.escape(s) for s in sorted(UNIT_ALIASES, key=len, reverse=True)) + r")(?![A-Za-z])")


def canonical_number(raw):
    raw = raw.replace(",", "").replace("−", "-")
    sign = "-" if raw.startswith("-") else ""
    whole, dot, fraction = raw.lstrip("-+").partition(".")
    whole = whole.lstrip("0") or "0"
    fraction = fraction.rstrip("0")
    value = whole + ("." + fraction if fraction else "")
    return (sign if value != "0" else "") + value


def trim_url(value):
    # Common prose punctuation; matched parentheses inside URLs remain intact.
    value = value.rstrip(".,;:!?'")
    for left, right in (("(", ")"), ("[", "]"), ("{", "}")):
        while value.endswith(right) and value.count(right) > value.count(left):
            value = value[:-1]
    return value


def mask(text, spans):
    chars = list(text)
    for start, end in spans:
        chars[start:end] = " " * (end - start)
    return "".join(chars)


def extract(text, protected=()):
    result = {key: Counter() for key in ("numbers", "quantities", "urls", "hashtags", "explicit")}
    spans = []
    for match in URL.finditer(text):
        result["urls"][trim_url(match.group())] += 1
        spans.append(match.span())
    working = mask(text, spans)
    spans = []
    for match in re.finditer("#", working):
        end = match.end()
        while end < len(working):
            category = unicodedata.category(working[end])
            if category[0] not in "LMN" and category != "Pc":
                break
            end += 1
        if end > match.end():
            result["hashtags"][working[match.start():end]] += 1
            spans.append((match.start(), end))
    working = LIST_MARKER.sub(lambda m: " " * len(m.group()), mask(working, spans).translate(DIGITS))
    for match in NUMBER.finditer(working):
        value = canonical_number(match.group())
        result["numbers"][value] += 1
        unit_match = UNIT.match(working, match.end())
        if unit_match:
            result["quantities"][value + " " + UNIT_ALIASES[unit_match.group(1)]] += 1
        elif re.search(r"฿[ \t]*$", working[:match.start()]):
            result["quantities"][value + " THB"] += 1
    result["explicit"] = Counter({token: text.count(token) for token in protected if text.count(token)})
    return result


def compare(before, after, protected=()):
    old, new = extract(before, protected), extract(after, protected)
    removed, added, changed = {}, {}, {}
    for category in old:
        lost, gained = old[category] - new[category], new[category] - old[category]
        if lost or gained:
            if lost:
                removed[category] = dict(sorted(lost.items()))
            if gained:
                added[category] = dict(sorted(gained.items()))
            # Totals are occurrence counts, not inferred one-to-one replacements.
            changed[category] = {"before_count": sum(old[category].values()), "after_count": sum(new[category].values())}
    return {"review_needed": bool(changed), "removed": removed, "added": added, "changed": changed}


def read_utf8(path):
    return Path(path).read_text(encoding="utf-8-sig")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", required=True)
    parser.add_argument("--after", required=True)
    parser.add_argument("--protect", help="UTF-8 JSON array of exact, case-sensitive strings")
    args = parser.parse_args(argv)
    try:
        protected = json.loads(read_utf8(args.protect)) if args.protect else []
        if not isinstance(protected, list) or any(not isinstance(s, str) or not s.strip() for s in protected):
            raise ValueError("--protect must contain a JSON array of nonempty, nonblank strings")
        protected = list(dict.fromkeys(protected))
        report = compare(read_utf8(args.before), read_utf8(args.after), protected)
    except (OSError, UnicodeError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=True))
        return 2
    print(json.dumps(report, ensure_ascii=True, separators=(",", ":")))
    return 1 if report["review_needed"] else 0


if __name__ == "__main__":
    sys.exit(main())
