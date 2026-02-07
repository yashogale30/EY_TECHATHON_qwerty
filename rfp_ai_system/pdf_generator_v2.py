import os
from datetime import datetime

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4


# ============ FOOTER WITH PAGE NUMBERS ============
def add_footer(canvas_obj, doc):
    canvas_obj.saveState()
    canvas_obj.setFont("Helvetica", 9)
    canvas_obj.setFillColor(colors.HexColor("#7F8FA3"))
    canvas_obj.drawString(
        0.75 * inch,
        0.5 * inch,
        f"RFP Bid Evaluation Report | Generated on {datetime.now().strftime('%d %b %Y')}",
    )
    canvas_obj.drawRightString(7.75 * inch, 0.5 * inch, f"Page {doc.page}")
    canvas_obj.restoreState()


def _to_float(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return float(default)


def _money_inr(x, decimals=0):
    val = _to_float(x, 0.0)
    if decimals == 2:
        return f"INR {val:,.2f}"
    return f"INR {val:,.0f}"


def generate_rfp_pdf(rfp_data, output_path):
    """Generate a professional RFP evaluation report (ReportLab Platypus)."""

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    # Document setup
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.8 * inch,
        title="RFP Bid Evaluation Report",
    )

    # Styles
    styles = getSampleStyleSheet()

    # IMPORTANT: don't name a new style "BodyText" (it already exists in the sample sheet).
    styles.add(
        ParagraphStyle(
            name="TitleCustom",
            parent=styles["Heading1"],
            fontSize=30,
            textColor=colors.HexColor("#2E3A59"),
            spaceAfter=10,
            alignment=1,  # center
            fontName="Helvetica-Bold",
        )
    )
    styles.add(
        ParagraphStyle(
            name="SubtitleCustom",
            parent=styles["Normal"],
            fontSize=13,
            textColor=colors.HexColor("#5A6C7D"),
            alignment=1,
            spaceAfter=24,
            fontName="Helvetica",
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionHeaderCustom",
            parent=styles["Heading2"],
            fontSize=14,
            textColor=colors.HexColor("#2E3A59"),
            spaceAfter=12,
            spaceBefore=10,
            fontName="Helvetica-Bold",
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodyTextCustom",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#3D4A5C"),
            leading=14,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SmallNote",
            parent=styles["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#7F8FA3"),
            leading=12,
        )
    )

    # Data
    rfp = (rfp_data or {}).get("rfp", {}) or {}
    matches = (rfp_data or {}).get("matches", []) or []
    score = _to_float((rfp_data or {}).get("score", 0.0), 0.0)
    price = (rfp_data or {}).get("price", 0.0)

    story = []

    # ================= COVER PAGE =================
    story.append(Spacer(1, 1.2 * inch))
    story.append(Paragraph("RFP Bid Evaluation Report", styles["TitleCustom"]))
    story.append(Paragraph("AI-Powered Tender Intelligence System", styles["SubtitleCustom"]))
    story.append(Spacer(1, 0.6 * inch))

    cover_data = [
        ["PROJECT", rfp.get("projectName", "N/A")],
        ["AUTHORITY", rfp.get("issued_by", "N/A")],
        ["CATEGORY", rfp.get("category", "N/A")],
        ["REPORT DATE", datetime.now().strftime("%d %B %Y")],
    ]

    cover_table = Table(cover_data, colWidths=[2.0 * inch, 4.2 * inch])
    cover_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E8EEF7")),
                ("BACKGROUND", (1, 0), (1, -1), colors.white),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 11),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#2E3A59")),
                ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#3D4A5C")),
                ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                ("ALIGN", (1, 0), (1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.8, colors.HexColor("#D4DFE8")),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )

    story.append(cover_table)
    story.append(PageBreak())

    # ================= EXECUTIVE SUMMARY =================
    story.append(Paragraph("Executive Summary", styles["SectionHeaderCustom"]))
    story.append(Spacer(1, 0.12 * inch))

    if score >= 0.75:
        score_color = colors.HexColor("#27AE60")
        rec_text = "PROCEED"
        rec_color = colors.HexColor("#27AE60")
    elif score >= 0.50:
        score_color = colors.HexColor("#F39C12")
        rec_text = "REVIEW"
        rec_color = colors.HexColor("#F39C12")
    else:
        score_color = colors.HexColor("#E74C3C")
        rec_text = "HOLD"
        rec_color = colors.HexColor("#E74C3C")

    summary_data = [
        ["OVERALL SCORE", "ESTIMATED BID", "RECOMMENDATION"],
        [f"{score:.1%}", _money_inr(price, decimals=0), rec_text],
    ]
    summary_table = Table(summary_data, colWidths=[2.2 * inch, 2.2 * inch, 2.0 * inch])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E3A59")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 11),
                ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#F5F7FA")),
                ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 1), (0, 1), 20),
                ("FONTSIZE", (1, 1), (1, 1), 13),
                ("FONTSIZE", (2, 1), (2, 1), 12),
                ("TEXTCOLOR", (0, 1), (0, 1), score_color),
                ("TEXTCOLOR", (2, 1), (2, 1), rec_color),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 1.2, colors.HexColor("#D4DFE8")),
                ("TOPPADDING", (0, 0), (-1, -1), 14),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
            ]
        )
    )
    story.append(summary_table)
    story.append(Spacer(1, 0.25 * inch))

    details_data = [
        ["Project Name", rfp.get("projectName", "N/A")],
        ["Issued By", rfp.get("issued_by", "N/A")],
        ["Category", rfp.get("category", "N/A")],
        ["Submission Deadline", rfp.get("submissionDeadline", "N/A")],
    ]
    details_table = Table(details_data, colWidths=[1.7 * inch, 4.7 * inch])
    details_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E8EEF7")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#2E3A59")),
                ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#3D4A5C")),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#D4DFE8")),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#F9FAFC")]),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    story.append(details_table)
    story.append(PageBreak())

    # ================= TECHNOLOGY MATCH SUMMARY =================
    story.append(Paragraph("Technology Match Summary", styles["SectionHeaderCustom"]))
    story.append(Spacer(1, 0.12 * inch))

    if matches:
        unit_prices = [_to_float(m.get("unit_price", 0.0), 0.0) for m in matches]
        lead_times = [_to_float(m.get("lead_time_days", 0.0), 0.0) for m in matches]

        avg_price = sum(unit_prices) / len(unit_prices) if unit_prices else 0.0
        min_price = min(unit_prices) if unit_prices else 0.0
        max_price = max(unit_prices) if unit_prices else 0.0
        min_lt = min(lead_times) if lead_times else 0.0
        max_lt = max(lead_times) if lead_times else 0.0

        story.append(
            Paragraph(
                (
                    f"<b>Sourcing Analysis:</b> {len(matches)} supplier options identified with unit pricing from "
                    f"{_money_inr(min_price)} to {_money_inr(max_price)} (average: {_money_inr(avg_price)}). "
                    f"Lead times range from {int(min_lt)} to {int(max_lt)} days."
                ),
                styles["BodyTextCustom"],
            )
        )
        story.append(Spacer(1, 0.18 * inch))
    else:
        story.append(Paragraph("No matching products were provided for this RFP.", styles["BodyTextCustom"]))
        story.append(Spacer(1, 0.18 * inch))

    rows = [["Product", "Match %", "BIS", "Lead Time", "Unit Price"]]
    for m in matches[:12]:
        bis_val = m.get("bis_certified", "No")
        bis_text = "Yes" if bis_val in (True, "Yes", "YES", "yes") else "No"

        rows.append(
            [
                (m.get("product_name", "N/A") or "N/A")[:46],
                f"{_to_float(m.get('spec_match_percent', 0.0), 0.0):.0f}%",
                bis_text,
                f"{int(_to_float(m.get('lead_time_days', 0), 0))} days",
                _money_inr(m.get("unit_price", 0.0), decimals=2),
            ]
        )

    products_table = Table(rows, repeatRows=1, colWidths=[2.9 * inch, 0.9 * inch, 0.7 * inch, 1.1 * inch, 1.2 * inch])
    products_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E3A59")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D4DFE8")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F9FAFC"), colors.white]),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.append(products_table)

    if len(matches) > 12:
        story.append(Spacer(1, 0.12 * inch))
        story.append(Paragraph(f"Showing 12 of {len(matches)} matches.", styles["SmallNote"]))

    story.append(PageBreak())

    # ================= RECOMMENDATION =================
    story.append(Paragraph("Recommendation & Next Steps", styles["SectionHeaderCustom"]))
    story.append(Spacer(1, 0.12 * inch))

    next_steps = (
        "<b>Overall Assessment:</b><br/><br/>"
        f"Composite score: <b>{score:.1%}</b>. Recommendation: <b>{rec_text}</b>.<br/><br/>"
        "<b>Key Strengths:</b><br/>"
        "• Technical specification match captured from shortlisted catalogue items.<br/>"
        "• Multiple supplier options enable negotiation and redundancy.<br/>"
        "• BIS compliance indicated per item where provided.<br/><br/>"
        "<b>Next Steps:</b><br/>"
        "1) Validate final BOQ vs. tender scope and specs.<br/>"
        "2) Confirm BIS/test certificates for the final vendor shortlist.<br/>"
        "3) Lock delivery schedule and penalties/LD clauses.<br/>"
        "4) Freeze commercial terms and submit bid package."
    )
    story.append(Paragraph(next_steps, styles["BodyTextCustom"]))

    # Build PDF
    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
    return output_path
