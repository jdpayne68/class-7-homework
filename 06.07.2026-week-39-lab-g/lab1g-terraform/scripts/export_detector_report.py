#!/usr/bin/env python3
"""
Export a Lab G Bedrock detector response JSON as a printable PDF.

Example:
    python scripts/export_detector_report.py \
      --response /tmp/lab-g-detector-response.json \
      --output evidence/06-bedrock-enriched-detector-response.pdf
"""

from __future__ import annotations

import argparse
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)


def normalize_text(value: str) -> str:
    """Replace glyphs that may render poorly in built-in PDF fonts."""
    replacements = {
        "\u2014": "-",   # em dash
        "\u2013": "-",   # en dash
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u00b1": "+/-",
        "\u26a0\ufe0f": "WARNING",
        "\u26a0": "WARNING",
        "\u2022": "*",
        "\u00a0": " ",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value


def inline_markup(value: str) -> str:
    """Convert a small, safe subset of Markdown to ReportLab paragraph markup."""
    value = normalize_text(value)
    value = html.escape(value, quote=False)

    # Inline code first so later substitutions do not alter it.
    code_fragments: list[str] = []

    def save_code(match: re.Match[str]) -> str:
        code_fragments.append(match.group(1))
        return f"@@CODE{len(code_fragments) - 1}@@"

    value = re.sub(r"`([^`]+)`", save_code, value)
    value = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", value)

    for index, fragment in enumerate(code_fragments):
        escaped = html.escape(normalize_text(fragment), quote=False)
        value = value.replace(
            f"@@CODE{index}@@",
            f'<font name="Courier">{escaped}</font>',
        )

    return value


def get_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()

    return {
        "title": ParagraphStyle(
            "ReportTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            alignment=TA_CENTER,
            spaceAfter=14,
            textColor=colors.HexColor("#1F2937"),
        ),
        "subtitle": ParagraphStyle(
            "ReportSubtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            alignment=TA_CENTER,
            spaceAfter=18,
            textColor=colors.HexColor("#4B5563"),
        ),
        "h1": ParagraphStyle(
            "H1",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=19,
            spaceBefore=14,
            spaceAfter=7,
            keepWithNext=True,
            textColor=colors.HexColor("#111827"),
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            spaceBefore=12,
            spaceAfter=6,
            keepWithNext=True,
            textColor=colors.HexColor("#1F2937"),
        ),
        "h3": ParagraphStyle(
            "H3",
            parent=base["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=14,
            spaceBefore=9,
            spaceAfter=5,
            keepWithNext=True,
            textColor=colors.HexColor("#374151"),
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.5,
            alignment=TA_LEFT,
            spaceAfter=6,
            textColor=colors.HexColor("#111827"),
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.5,
            leftIndent=18,
            firstLineIndent=-9,
            spaceAfter=4,
            bulletIndent=7,
            textColor=colors.HexColor("#111827"),
        ),
        "quote": ParagraphStyle(
            "Quote",
            parent=base["BodyText"],
            fontName="Helvetica-Oblique",
            fontSize=9,
            leading=13,
            leftIndent=18,
            rightIndent=12,
            borderWidth=0.5,
            borderColor=colors.HexColor("#9CA3AF"),
            borderPadding=7,
            backColor=colors.HexColor("#F3F4F6"),
            spaceBefore=5,
            spaceAfter=8,
            textColor=colors.HexColor("#374151"),
        ),
        "summary_label": ParagraphStyle(
            "SummaryLabel",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#374151"),
        ),
        "summary_value": ParagraphStyle(
            "SummaryValue",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            leftIndent=12,
            spaceAfter=3,
            textColor=colors.HexColor("#111827"),
        ),
        "small": ParagraphStyle(
            "Small",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#6B7280"),
        ),
    }


def markdown_flowables(text: str, styles: dict[str, ParagraphStyle]) -> Iterable[object]:
    """Convert common Markdown constructs into ReportLab flowables."""
    paragraph_lines: list[str] = []

    def flush_paragraph() -> list[object]:
        nonlocal paragraph_lines
        if not paragraph_lines:
            return []
        joined = " ".join(line.strip() for line in paragraph_lines).strip()
        paragraph_lines = []
        if not joined:
            return []
        return [Paragraph(inline_markup(joined), styles["body"])]

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        if not stripped:
            yield from flush_paragraph()
            continue

        if re.fullmatch(r"[-*_]{3,}", stripped):
            yield from flush_paragraph()
            yield Spacer(1, 3)
            yield HRFlowable(
                width="100%",
                thickness=0.6,
                color=colors.HexColor("#9CA3AF"),
                spaceBefore=2,
                spaceAfter=7,
            )
            continue

        heading = re.match(r"^(#{1,3})\s+(.+)$", stripped)
        if heading:
            yield from flush_paragraph()
            level = len(heading.group(1))
            yield Paragraph(
                inline_markup(heading.group(2)),
                styles[f"h{level}"],
            )
            continue

        quote = re.match(r"^>\s?(.*)$", stripped)
        if quote:
            yield from flush_paragraph()
            yield Paragraph(
                inline_markup(quote.group(1)),
                styles["quote"],
            )
            continue

        checkbox = re.match(r"^[-*]\s+\[([ xX])\]\s+(.+)$", stripped)
        if checkbox:
            yield from flush_paragraph()
            marker = "[x]" if checkbox.group(1).lower() == "x" else "[ ]"
            yield Paragraph(
                f"{marker} {inline_markup(checkbox.group(2))}",
                styles["bullet"],
                bulletText="",
            )
            continue

        bullet = re.match(r"^[-*+]\s+(.+)$", stripped)
        if bullet:
            yield from flush_paragraph()
            yield Paragraph(
                inline_markup(bullet.group(1)),
                styles["bullet"],
                bulletText="•",
            )
            continue

        numbered = re.match(r"^(\d+)[.)]\s+(.+)$", stripped)
        if numbered:
            yield from flush_paragraph()
            yield Paragraph(
                inline_markup(numbered.group(2)),
                styles["bullet"],
                bulletText=f"{numbered.group(1)}.",
            )
            continue

        # Markdown table rows are flattened into readable lines rather than
        # forcing a wide table that may clip in a portrait PDF.
        if stripped.startswith("|") and stripped.endswith("|"):
            if re.fullmatch(r"\|[\s:|-]+\|", stripped):
                continue
            yield from flush_paragraph()
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            visible = " | ".join(cell for cell in cells if cell)
            if visible:
                yield Paragraph(inline_markup(visible), styles["small"])
            continue

        paragraph_lines.append(stripped)

    yield from flush_paragraph()


def page_footer(canvas, document) -> None:
    canvas.saveState()
    width, _ = LETTER
    canvas.setStrokeColor(colors.HexColor("#D1D5DB"))
    canvas.setLineWidth(0.5)
    canvas.line(0.65 * inch, 0.55 * inch, width - 0.65 * inch, 0.55 * inch)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor("#6B7280"))
    canvas.drawString(0.65 * inch, 0.35 * inch, "Lab G - Bedrock-Enriched SOAR Report")
    canvas.drawRightString(
        width - 0.65 * inch,
        0.35 * inch,
        f"Page {document.page}",
    )
    canvas.restoreState()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export the Lab G detector response as a printable PDF."
    )
    parser.add_argument(
        "--response",
        default="/tmp/lab-g-detector-response.json",
        help="Path to the detector response JSON.",
    )
    parser.add_argument(
        "--output",
        default="evidence/06-bedrock-enriched-detector-response.pdf",
        help="Destination PDF path.",
    )
    parser.add_argument(
        "--redact-username",
        action="store_true",
        help="Replace the username in the report with <redacted-username>.",
    )
    args = parser.parse_args()

    response_path = Path(args.response).expanduser()
    output_path = Path(args.output).expanduser()

    if not response_path.is_file():
        raise SystemExit(f"Response file not found: {response_path}")

    try:
        data = json.loads(response_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {response_path}: {exc}") from exc

    findings = data.get("findings") or []
    finding = findings[0] if findings else {}
    enrichment = finding.get("ai_enrichment") or {}
    analysis = str(enrichment.get("analysis") or "NO ANALYSIS RETURNED")

    token_id = finding.get("token_id")
    if token_id:
        analysis = analysis.replace(str(token_id), "<redacted-token-id>")

    username = finding.get("username")
    display_username = username
    if args.redact_username and username:
        analysis = analysis.replace(str(username), "<redacted-username>")
        display_username = "<redacted-username>"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    styles = get_styles()
    story: list[object] = []

    story.append(Paragraph("Bedrock-Enriched SOAR Report", styles["title"]))
    story.append(
        Paragraph(
            "Lab G - Unused Authentication Token Detector",
            styles["subtitle"],
        )
    )

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    summary_items = [
        ("Generated", generated_at),
        ("Finding count", data.get("finding_count")),
        ("AI enrichments succeeded", data.get("ai_enrichments_succeeded")),
        ("AI enrichments failed", data.get("ai_enrichments_failed")),
        ("AI status", enrichment.get("status")),
        ("Model", enrichment.get("model_id")),
        ("Stop reason", enrichment.get("stop_reason")),
        ("Alert type", finding.get("alert_type")),
        ("Username", display_username),
        ("Token age", f"{finding.get('age_minutes')} minutes" if finding else None),
        ("Threshold", f"{finding.get('threshold_minutes')} minutes" if finding else None),
    ]

    story.append(Paragraph("Detector Summary", styles["h1"]))
    for label, value in summary_items:
        if value is None:
            continue
        story.append(
            Paragraph(
                f"<b>{html.escape(str(label))}:</b> {inline_markup(str(value))}",
                styles["summary_value"],
            )
        )

    story.append(Spacer(1, 6))
    story.append(
        HRFlowable(
            width="100%",
            thickness=0.8,
            color=colors.HexColor("#9CA3AF"),
            spaceAfter=8,
        )
    )
    story.append(Paragraph("AI Incident Analysis", styles["h1"]))
    story.extend(markdown_flowables(analysis, styles))

    story.append(Spacer(1, 10))
    story.append(
        Paragraph(
            "Analyst-assistance notice: This report supports human investigation. "
            "It does not independently confirm compromise or authorize automated "
            "account-disabling actions.",
            styles["quote"],
        )
    )

    document = SimpleDocTemplate(
        str(output_path),
        pagesize=LETTER,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.75 * inch,
        title="Bedrock-Enriched SOAR Report",
        author="Lab G Unused Token Detector",
        subject="AI-assisted security incident analysis",
    )
    document.build(
        story,
        onFirstPage=page_footer,
        onLaterPages=page_footer,
    )

    print(f"PASS: PDF report created: {output_path}")


if __name__ == "__main__":
    main()
