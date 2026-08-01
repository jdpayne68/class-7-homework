#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import shutil
import textwrap
from pathlib import Path
from typing import Any

IPV4_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|1?\d?\d)\b"
)
AWS_ACCOUNT_RE = re.compile(r"(?<=:)\d{12}(?=:)")


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise SystemExit(f"Expected a JSON object in {path}")

    return data


def decode_dynamodb_value(value: Any) -> Any:
    if not isinstance(value, dict):
        return value

    if "S" in value:
        return value["S"]
    if "N" in value:
        number = value["N"]
        try:
            return int(number)
        except ValueError:
            try:
                return float(number)
            except ValueError:
                return number
    if "BOOL" in value:
        return value["BOOL"]
    if "NULL" in value:
        return None
    if "L" in value:
        return [
            decode_dynamodb_value(item)
            for item in value["L"]
        ]
    if "M" in value:
        return {
            key: decode_dynamodb_value(item)
            for key, item in value["M"].items()
        }

    return value


def decode_dynamodb_items(data: dict[str, Any]) -> list[dict[str, Any]]:
    decoded: list[dict[str, Any]] = []

    for raw_item in data.get("Items", []):
        if not isinstance(raw_item, dict):
            continue

        decoded.append(
            {
                key: decode_dynamodb_value(value)
                for key, value in raw_item.items()
            }
        )

    return decoded


def stored_item_to_finding(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_id": item.get("event_id"),
        "timestamp": item.get("timestamp"),
        "action": item.get("action"),
        "terminating_rule_id": item.get("terminating_rule_id"),
        "terminating_rule_type": item.get("terminating_rule_type"),
        "client_ip": item.get("client_ip") or item.get("source_ip"),
        "country": item.get("country"),
        "method": item.get("method"),
        "uri": item.get("uri"),
        "args": item.get("args"),
        "ai_enrichment": {
            "status": item.get("ai_status"),
            "model_id": item.get("ai_model_id"),
            "analysis": item.get("ai_analysis", ""),
            "stop_reason": item.get("ai_stop_reason"),
        },
    }


def redact_text(
    text: str,
    sensitive_values: list[Any],
) -> str:
    redacted = text

    for value in sensitive_values:
        if value not in (None, ""):
            redacted = redacted.replace(
                str(value),
                "<redacted>",
            )

    redacted = IPV4_RE.sub(
        "<redacted-source-ip>",
        redacted,
    )
    redacted = AWS_ACCOUNT_RE.sub(
        "<redacted-account>",
        redacted,
    )

    return redacted


def terminal_width(requested_width: int | None) -> int:
    if requested_width:
        return max(60, min(requested_width, 120))

    detected = shutil.get_terminal_size(
        fallback=(88, 24)
    ).columns

    return max(72, min(detected - 2, 100))


def print_wrapped_markdown(text: str, width: int) -> None:
    bullet_re = re.compile(r"^(\s*(?:[-*]|\d+\.)\s+)(.*)$")

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        if not stripped:
            print()
            continue

        if stripped in {"---", "***", "___"}:
            continue

        if stripped.startswith("#"):
            heading = stripped.lstrip("#").strip()
            print()
            print(heading.upper())
            print("=" * min(len(heading), width))
            continue

        bullet_match = bullet_re.match(line)
        if bullet_match:
            prefix = bullet_match.group(1)
            body = bullet_match.group(2)

            print(
                textwrap.fill(
                    body,
                    width=width,
                    initial_indent=prefix,
                    subsequent_indent=" " * len(prefix),
                    break_long_words=False,
                    break_on_hyphens=False,
                )
            )
            continue

        print(
            textwrap.fill(
                stripped,
                width=width,
                break_long_words=False,
                break_on_hyphens=False,
            )
        )


def summary_from_response(
    response: dict[str, Any],
) -> dict[str, Any]:
    keys = (
        "events_examined",
        "blocked_events_found",
        "events_processed",
        "events_skipped_existing",
        "bedrock_successes",
        "bedrock_failures",
    )

    return {
        key: response.get(key)
        for key in keys
        if key in response
    }


def render_report(
    response: dict[str, Any],
    findings: list[dict[str, Any]],
    source_note: str,
    width: int,
) -> str:
    lines: list[str] = []

    def emit(value: str = "") -> None:
        lines.append(value)

    emit("WAF ANALYZER REPORT")
    emit("=" * 19)
    emit(f"Source: {source_note}")

    summary = summary_from_response(response)

    if summary:
        emit()
        emit("INVOCATION SUMMARY")
        emit("=" * 18)

        for key, value in summary.items():
            label = key.replace("_", " ").title()
            emit(f"{label}: {value}")

    if not findings:
        emit()
        emit("No findings were available to display.")
        return "\n".join(lines)

    for index, finding in enumerate(findings, start=1):
        enrichment = finding.get("ai_enrichment") or {}
        analysis = str(
            enrichment.get("analysis")
            or "No AI analysis was returned."
        )

        event_id = finding.get("event_id")
        client_ip = (
            finding.get("client_ip")
            or finding.get("source_ip")
        )

        analysis = redact_text(
            analysis,
            [event_id, client_ip],
        )

        emit()
        emit(f"FINDING {index}")
        emit("=" * len(f"FINDING {index}"))
        emit(f"Timestamp: {finding.get('timestamp') or 'unknown'}")
        emit(f"Action: {finding.get('action') or 'unknown'}")
        emit(f"Method: {finding.get('method') or 'unknown'}")
        emit(f"URI: {finding.get('uri') or 'unknown'}")
        emit(
            "Rule: "
            f"{finding.get('terminating_rule_id') or 'unknown'}"
        )
        emit(f"Country: {finding.get('country') or 'unknown'}")
        emit("Source IP: <redacted-source-ip>")
        emit("Event ID: <redacted-event-id>")
        emit(
            "AI status: "
            f"{enrichment.get('status') or 'unknown'}"
        )
        emit(
            "Model: "
            f"{enrichment.get('model_id') or 'unknown'}"
        )
        emit(
            "Stop reason: "
            f"{enrichment.get('stop_reason') or 'unknown'}"
        )
        emit()
        emit("AI SECURITY ANALYSIS")
        emit("=" * 20)

        rendered: list[str] = []
        bullet_re = re.compile(
            r"^(\s*(?:[-*]|\d+\.)\s+)(.*)$"
        )

        for raw_line in analysis.splitlines():
            stripped = raw_line.strip()

            if not stripped:
                rendered.append("")
                continue

            if stripped in {"---", "***", "___"}:
                continue

            if stripped.startswith("#"):
                heading = stripped.lstrip("#").strip().upper()
                rendered.extend(
                    [
                        "",
                        heading,
                        "=" * min(len(heading), width),
                    ]
                )
                continue

            match = bullet_re.match(raw_line)
            if match:
                prefix = match.group(1)
                body = match.group(2)
                rendered.append(
                    textwrap.fill(
                        body,
                        width=width,
                        initial_indent=prefix,
                        subsequent_indent=" " * len(prefix),
                        break_long_words=False,
                        break_on_hyphens=False,
                    )
                )
                continue

            rendered.append(
                textwrap.fill(
                    stripped,
                    width=width,
                    break_long_words=False,
                    break_on_hyphens=False,
                )
            )

        emit("\n".join(rendered).strip())

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Display a clear, redacted Lab H WAF/Bedrock report."
        )
    )
    parser.add_argument(
        "--response",
        default="/tmp/lab-h-analyzer-response.json",
        help="Lambda invocation response JSON.",
    )
    parser.add_argument(
        "--dynamodb-json",
        default="/tmp/lab-h-dynamodb-items.json",
        help="AWS CLI DynamoDB scan JSON used as fallback.",
    )
    parser.add_argument(
        "--output",
        help="Optional path for a redacted text report.",
    )
    parser.add_argument(
        "--width",
        type=int,
        help="Report width. Defaults to detected terminal width.",
    )
    args = parser.parse_args()

    width = terminal_width(args.width)
    response_path = Path(args.response)
    dynamodb_path = Path(args.dynamodb_json)

    response = load_json(response_path)
    findings = response.get("findings") or []
    source_note = "Lambda invocation response"

    if not findings:
        dynamodb_data = load_json(dynamodb_path)
        items = decode_dynamodb_items(dynamodb_data)

        if items:
            latest = max(
                items,
                key=lambda item: str(
                    item.get("recorded_at", "")
                ),
            )
            findings = [stored_item_to_finding(latest)]
            source_note = (
                "latest stored DynamoDB finding "
                "(current invocation skipped a duplicate)"
            )

    report = render_report(
        response,
        findings,
        source_note,
        width,
    )

    print(report)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        output_path.write_text(
            report + "\n",
            encoding="utf-8",
        )
        print()
        print(f"Saved redacted report: {output_path}")


if __name__ == "__main__":
    main()
