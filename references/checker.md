# Protected-data comparison

Run with Python 3 (standard library only), using an absolute script path and absolute input paths when outside the skill folder:

`python scripts/compare_protected.py --before before.md --after after.md --protect terms.json`

`terms.json` is an optional JSON array of case-sensitive strings, for example `["Example Brand", "Example Product", "Approved CTA"]`. Include exact approved CTA/quotes when their wording must stay fixed. Keep this list task-specific; do not overwrite project brand context.

Exit 0: no tracked differences. Exit 1: differences need review. Exit 2: input/usage error. The tool reads files and returns compact JSON; it never edits them. Review counts and quantity/unit bindings, not just whether a number occurs somewhere. A legitimate addition/removal may trigger review. Headline/list formatting and number normalization may affect matches; see script help/tests for supported formats.

A clean result does not certify factual truth, full semantic equivalence, quote attribution, sentence-level negation, or every date/Thai number-word expression. Read the source and rewrite to check these. Never report “fact checked” based only on this tool.
