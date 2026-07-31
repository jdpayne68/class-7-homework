#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import textwrap
from pathlib import Path


def wrap_markdown(text: str, width: int) -> str:
    """Wrap prose while preserving Markdown structure."""
    output: list[str] = []
    in_code_block = False

    list_pattern = re.compile(
        r"^(\s*(?:[-*+]|\d+[.)]|>\s*|-\s+\[[ xX]\])\s+)(.*)$"
    )

    for line in text.splitlines():
        stripped = line.strip()

        if stripped.startswith("```"):
            in_code_block = not in_code_block
            output.append(line)
            continue

        # Preserve code, blank lines, headings, rules, and Markdown tables.
        if (
            in_code_block
            or not stripped
            or stripped.startswith("#")
            or stripped.startswith("|")
            or stripped in {"---", "***", "___"}
        ):
            output.append(stripped if stripped else "")
            continue

        list_match = list_pattern.match(line)

        if list_match:
            prefix, content = list_match.groups()

            output.append(
                textwrap.fill(
                    content,
                    width=width,
                    initial_indent=prefix,
                    subsequent_indent=" " * len(prefix),
                    break_long_words=False,
                    break_on_hyphens=False,
                )
            )
        else:
            output.append(
                textwrap.fill(
                    stripped,
                    width=width,
                    break_long_words=False,
                    break_on_hyphens=False,
                )
            )

    return "\n".join(output)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Display the Lab G detector response with wrapped AI analysis."
    )
    parser.add_argument(
        "--response",
        default="/tmp/lab-g-detector-response.json",
        help="Path to the Lambda response JSON.",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=88,
        help="Maximum display width for prose.",
    )
    args = parser.parse_args()

    response_path = Path(args.response)

    if not response_path.is_file():
        raise SystemExit(f"Response file not found: {response_path}")

    data = json.loads(response_path.read_text(encoding="utf-8"))
    findings = data.get("findings") or []
    enrichment = findings[0].get("ai_enrichment", {}) if findings else {}

    analysis = enrichment.get("analysis", "NO ANALYSIS RETURNED")

    # Redact the token identifier from portfolio evidence.
    if findings:
        token_id = findings[0].get("token_id")
        if token_id:
            analysis = analysis.replace(str(token_id), "<redacted-token-id>")

    print("DETECTOR SUMMARY")
    print("================")
    print(
        json.dumps(
            {
                "finding_count": data.get("finding_count"),
                "ai_enrichments_succeeded": data.get(
                    "ai_enrichments_succeeded"
                ),
                "ai_enrichments_failed": data.get(
                    "ai_enrichments_failed"
                ),
                "ai_status": enrichment.get("status"),
                "model_id": enrichment.get("model_id"),
                "stop_reason": enrichment.get("stop_reason"),
            },
            indent=2,
        )
    )

    print("\nAI ANALYSIS")
    print("===========")
    print(wrap_markdown(analysis, args.width))


if __name__ == "__main__":
    main()
