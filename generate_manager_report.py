#!/usr/bin/env python3
"""
SYP Team Effectiveness Lab — Manager Diagnostic Report Generator
================================================================
Generates a branded, multi-page PDF diagnostic report for team managers,
summarising the team's performance across the three core dimensions:
Communication, Decision Making, and Collaboration.

Usage (standalone):
    python3 generate_manager_report.py              # uses built-in sample data
    python3 generate_manager_report.py input.json   # reads JSON from file

As a module:
    from generate_manager_report import generate_manager_report_pdf
    pdf_bytes = generate_manager_report_pdf(data_dict)

Expected JSON structure:
    {
        "team_name":     "AED Global",
        "workshop_date": "6 May 2026",
        "manager_name":  "Sarah Mitchell",
        "manager_email": "sarah@aedglobal.com",
        "participants": [
            {
                "name":      "Alice Nguyen",
                "role":      "Guide",          # Guide / Builder / Observer
                "c_score":   78.0,             # Communication 0-100
                "d_score":   42.0,             # Decision Making 0-100
                "co_score":  85.0,             # Collaboration 0-100
                "c_level":   "High",           # High / Low
                "d_level":   "Low",
                "co_level":  "High",
                "archetype": "Signal"
            },
            ...
        ]
    }

Flask route (add to your Railway app.py):
    See generate_flask_route() at the bottom of this file.

Dependencies:
    pip install reportlab --break-system-packages
"""

import json
import sys
import io
from collections import Counter
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
    Table, TableStyle, HRFlowable, PageBreak, KeepTogether,
    NextPageTemplate,
)
from reportlab.platypus.flowables import Flowable


# ─── Brand palette ──────────────────────────────────────────────────────────

DARK_BLUE   = colors.HexColor("#0D2A66")
SKY_BLUE    = colors.HexColor("#1E88E5")
NEAR_BLACK  = colors.HexColor("#1A1A2E")
LIGHT_BLUE  = colors.HexColor("#E3F2FD")
MID_GREY    = colors.HexColor("#6B7280")
LIGHT_GREY  = colors.HexColor("#F3F4F6")
SUCCESS     = colors.HexColor("#059669")
WARNING     = colors.HexColor("#D97706")
WHITE       = colors.white

ARCHETYPE_COLOURS = {
    # Current archetype names (the only six in use)
    "Anchor":        colors.HexColor("#B71C1C"),
    "Compass":       colors.HexColor("#6A1B9A"),
    "Navigator":     colors.HexColor("#00838F"),
    "Relay":         colors.HexColor("#2E75B6"),
    "Signal":        colors.HexColor("#E65100"),
    "Summit":        colors.HexColor("#1B5E20"),
}

ARCHETYPE_SUMMARY = {
    # Current archetype names (the only six in use)
    "Anchor":        "Steady and clear. Holds the team together when pressure rises.",
    "Compass":       "Analytical and methodical. Works through options before committing.",
    "Navigator":     "Decisive under pressure. Keeps direction clear when the path is not.",
    "Relay":         "Versatile and connective. Adapts across roles and keeps work moving.",
    "Signal":        "Communicative and inclusive. Surfaces ideas and keeps people informed.",
    "Summit":        "Strong across all three dimensions. Performs consistently under load.",
}

DIMENSION_DESCRIPTIONS = {
    "Communication":    "How clearly individuals express ideas, listen actively, and adapt their message to different audiences.",
    "Decision Making":  "How effectively individuals analyse options, reason under pressure, and commit to clear choices.",
    "Collaboration":    "How well individuals coordinate with others, share credit, and adapt their style to team needs.",
}

PAGE_W, PAGE_H = A4            # 595 × 842 pt
L_MARGIN = R_MARGIN = 18 * mm
T_MARGIN_COVER   = 10 * mm
T_MARGIN_CONTENT = 28 * mm
B_MARGIN         = 20 * mm
BODY_W = PAGE_W - L_MARGIN - R_MARGIN


# ─── Page templates (canvas callbacks) ──────────────────────────────────────

def _draw_cover(canvas, doc):
    """Full-bleed dark blue cover page."""
    canvas.saveState()
    # Dark blue fill
    canvas.setFillColor(DARK_BLUE)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    # Sky blue accent bar at very top
    canvas.setFillColor(SKY_BLUE)
    canvas.rect(0, PAGE_H - 6 * mm, PAGE_W, 6 * mm, fill=1, stroke=0)
    # Subtle darker strip at bottom
    canvas.setFillColor(colors.HexColor("#061844"))
    canvas.rect(0, 0, PAGE_W, 32 * mm, fill=1, stroke=0)
    canvas.restoreState()


def _draw_content(canvas, doc):
    """Header + footer on every interior page."""
    canvas.saveState()

    # ── Header bar
    canvas.setFillColor(DARK_BLUE)
    canvas.rect(0, PAGE_H - 22 * mm, PAGE_W, 22 * mm, fill=1, stroke=0)

    canvas.setFont("Helvetica-Bold", 8.5)
    canvas.setFillColor(WHITE)
    canvas.drawString(L_MARGIN, PAGE_H - 12 * mm, "TEAM EFFECTIVENESS WORKSHOP")

    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor("#90CAF9"))
    canvas.drawString(L_MARGIN, PAGE_H - 18.5 * mm, "Manager Diagnostic Report  ·  Confidential")
    canvas.drawRightString(PAGE_W - R_MARGIN, PAGE_H - 12 * mm, f"Page {doc.page}")

    # Sky blue accent underline
    canvas.setFillColor(SKY_BLUE)
    canvas.rect(0, PAGE_H - 23 * mm, PAGE_W, 1 * mm, fill=1, stroke=0)

    # ── Footer
    canvas.setFillColor(LIGHT_GREY)
    canvas.rect(0, 0, PAGE_W, 12 * mm, fill=1, stroke=0)
    canvas.setFont("Helvetica", 6.5)
    canvas.setFillColor(MID_GREY)
    canvas.drawString(L_MARGIN, 4 * mm,
                      "© The Performance Lens by Saigon Young Professionals")
    canvas.drawRightString(PAGE_W - R_MARGIN, 4 * mm,
                           f"Generated {datetime.now().strftime('%d %B %Y')}")

    canvas.restoreState()


# ─── Custom flowables ────────────────────────────────────────────────────────

class DimensionBar(Flowable):
    """Labelled horizontal score bar with 60-point threshold marker."""

    def __init__(self, label, avg_score, high_n, low_n):
        super().__init__()
        self.label     = label
        self.avg_score = avg_score
        self.high_n    = high_n
        self.low_n     = low_n
        self._height   = 18 * mm

    def wrap(self, *args):
        return (BODY_W, self._height)

    def draw(self):
        c       = self.canv
        label_w = 48 * mm
        bar_x   = label_w
        bar_y   = 5 * mm
        bar_h   = 9 * mm
        bar_w   = BODY_W - label_w

        # Label
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(NEAR_BLACK)
        c.drawString(0, bar_y + 2.5 * mm, self.label)

        # Hi/Lo sub-label
        c.setFont("Helvetica", 7)
        c.setFillColor(MID_GREY)
        c.drawString(0, bar_y - 2 * mm, f"↑ High: {self.high_n}   ↓ Low: {self.low_n}")

        # Track
        c.setFillColor(LIGHT_GREY)
        c.roundRect(bar_x, bar_y, bar_w, bar_h, 3 * mm, fill=1, stroke=0)

        # Fill
        fill_w   = bar_w * min(self.avg_score, 100) / 100
        fill_col = SUCCESS if self.avg_score >= 60 else WARNING
        c.setFillColor(fill_col)
        if fill_w > 0:
            c.roundRect(bar_x, bar_y, fill_w, bar_h, 3 * mm, fill=1, stroke=0)

        # Threshold marker at 60
        tx = bar_x + bar_w * 0.60
        c.setStrokeColor(MID_GREY)
        c.setLineWidth(0.8)
        c.setDash([3, 2])
        c.line(tx, bar_y - 1, tx, bar_y + bar_h + 1)
        c.setDash([])
        c.setFont("Helvetica", 6)
        c.setFillColor(MID_GREY)
        c.drawCentredString(tx, bar_y + bar_h + 2.5, "60")

        # Score text
        score_txt = f"{self.avg_score:.0f}"
        if fill_w > 14 * mm:
            c.setFont("Helvetica-Bold", 9)
            c.setFillColor(WHITE)
            c.drawRightString(bar_x + fill_w - 3 * mm, bar_y + 3 * mm, score_txt)
        else:
            c.setFont("Helvetica-Bold", 9)
            c.setFillColor(NEAR_BLACK)
            c.drawString(bar_x + fill_w + 3 * mm, bar_y + 3 * mm, score_txt)


class StatBox(Flowable):
    """Coloured box showing a key metric."""

    def __init__(self, value, label, colour, width=44 * mm, height=22 * mm):
        super().__init__()
        self.value  = str(value)
        self.label  = label
        self.colour = colour
        self.bw     = width
        self.bh     = height

    def wrap(self, *args):
        return (self.bw, self.bh)

    def draw(self):
        c = self.canv
        c.setFillColor(self.colour)
        c.roundRect(0, 0, self.bw, self.bh, 3.5 * mm, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 18)
        c.setFillColor(WHITE)
        c.drawCentredString(self.bw / 2, self.bh * 0.46, self.value)
        c.setFont("Helvetica", 7)
        c.setFillColor(WHITE)
        c.drawCentredString(self.bw / 2, self.bh * 0.16, self.label.upper())


# ─── Text styles ─────────────────────────────────────────────────────────────

def _styles():
    return {
        "section_title": ParagraphStyle("section_title",
            fontName="Helvetica-Bold", fontSize=14, textColor=DARK_BLUE,
            spaceBefore=2 * mm, spaceAfter=3 * mm),

        "sub_heading": ParagraphStyle("sub_heading",
            fontName="Helvetica-Bold", fontSize=10, textColor=NEAR_BLACK,
            spaceBefore=2 * mm, spaceAfter=2 * mm),

        "body": ParagraphStyle("body",
            fontName="Helvetica", fontSize=9, textColor=NEAR_BLACK,
            leading=14, spaceAfter=3 * mm),

        "caption": ParagraphStyle("caption",
            fontName="Helvetica", fontSize=8, textColor=MID_GREY,
            leading=12, spaceAfter=3 * mm),

        "bullet": ParagraphStyle("bullet",
            fontName="Helvetica", fontSize=9, textColor=NEAR_BLACK,
            leading=14, leftIndent=8, firstLineIndent=-8, spaceAfter=2 * mm),

        # Cover page
        "cover_title": ParagraphStyle("cover_title",
            fontName="Helvetica-Bold", fontSize=30, textColor=WHITE,
            leading=36, spaceAfter=4 * mm),

        "cover_sub": ParagraphStyle("cover_sub",
            fontName="Helvetica", fontSize=13,
            textColor=colors.HexColor("#90CAF9"), spaceAfter=2 * mm),

        "cover_meta": ParagraphStyle("cover_meta",
            fontName="Helvetica", fontSize=10,
            textColor=colors.HexColor("#BBDEFB"), spaceAfter=2 * mm),

        # Table cells
        "t_head": ParagraphStyle("t_head",
            fontName="Helvetica-Bold", fontSize=8, textColor=WHITE,
            alignment=TA_CENTER),

        "t_cell": ParagraphStyle("t_cell",
            fontName="Helvetica", fontSize=8.5, textColor=NEAR_BLACK,
            alignment=TA_CENTER, leading=11),

        "t_cell_l": ParagraphStyle("t_cell_l",
            fontName="Helvetica", fontSize=8.5, textColor=NEAR_BLACK,
            leading=11),
    }


# ─── Data analysis ────────────────────────────────────────────────────────────

def _calc_stats(participants):
    n = len(participants)
    if n == 0:
        return {}

    c_scores  = [p["c_score"]  for p in participants]
    d_scores  = [p["d_score"]  for p in participants]
    co_scores = [p["co_score"] for p in participants]

    c_avg  = round(sum(c_scores)  / n, 1)
    d_avg  = round(sum(d_scores)  / n, 1)
    co_avg = round(sum(co_scores) / n, 1)

    c_high  = sum(1 for p in participants if p.get("c_level")  == "High")
    d_high  = sum(1 for p in participants if p.get("d_level")  == "High")
    co_high = sum(1 for p in participants if p.get("co_level") == "High")

    overall_avg = round((c_avg + d_avg + co_avg) / 3, 1)

    strengths = []
    dev_areas = []
    for dim, avg in [("Communication", c_avg),
                     ("Decision Making", d_avg),
                     ("Collaboration", co_avg)]:
        (strengths if avg >= 60 else dev_areas).append(dim)

    archetype_counts = Counter(p["archetype"] for p in participants)
    role_counts      = Counter(p.get("role", "Unknown") for p in participants)

    return {
        "n": n,
        "c_avg": c_avg,   "d_avg": d_avg,   "co_avg": co_avg,
        "c_high": c_high, "d_high": d_high, "co_high": co_high,
        "c_low": n - c_high, "d_low": n - d_high, "co_low": n - co_high,
        "overall_avg": overall_avg,
        "archetype_counts": archetype_counts,
        "role_counts": role_counts,
        "strengths": strengths,
        "dev_areas": dev_areas,
    }


def _overview_text(stats):
    oa = stats["overall_avg"]
    n  = stats["n"]
    if oa >= 75:
        tone = "scored strongly overall"
    elif oa >= 60:
        tone = "scored above the threshold overall, with specific areas to develop"
    else:
        tone = "scored below the threshold overall, which points to team-level work to do"

    parts = [
        f"Your team of {n} completed the Team Effectiveness Workshop and {tone} "
        f"(team average: {oa}/100)."
    ]
    if stats["strengths"]:
        parts.append(f"The team scored above the threshold in: {', '.join(stats['strengths'])}.")
    if stats["dev_areas"]:
        parts.append(f"The team scored below the threshold in: {', '.join(stats['dev_areas'])}.")

    n_archetypes = len(stats["archetype_counts"])
    if n_archetypes >= 4:
        parts.append(
            "The team covers four or more archetypes. That range gives you different working "
            "styles to draw on, provided you coordinate them deliberately."
        )
    elif n_archetypes <= 2:
        top = stats["archetype_counts"].most_common(1)[0][0]
        parts.append(
            f"Most of the team sits in the {top} archetype. The working style is consistent, "
            f"so it is worth seeking out perspectives the group does not naturally produce."
        )
    return " ".join(parts)


def _dim_insight(dim_name, avg, high_n, low_n, n):
    pct = high_n / n * 100 if n else 0
    if avg >= 75:
        verdict = (f"a team strength. {high_n} of {n} scored High "
                   f"({pct:.0f}%)")
    elif avg >= 60:
        verdict = (f"above the threshold. {high_n} scored High and {low_n} scored Low, "
                   f"so there is room to bring the lower scores up")
    elif avg >= 45:
        verdict = (f"a development priority. Only {high_n} of {n} reached the High "
                   f"threshold. Targeted coaching here would show results quickly")
    else:
        verdict = (f"a capability gap. {low_n} of {n} scored below the threshold. "
                   f"A structured intervention is recommended")
    return f"<b>{dim_name}</b> (avg {avg}/100) is {verdict}."


def _recommendations(stats):
    recs = []

    # Dimension-driven
    if "Communication" in stats["dev_areas"]:
        recs.append(
            "Set up regular communication routines: daily stand-ups, written async updates, "
            "or a weekly team note. The aim is to make active listening and clear messaging a habit "
            "rather than something that happens only when there is time for it."
        )
    if "Decision Making" in stats["dev_areas"]:
        recs.append(
            "Run the exercises again as monthly scenario reviews, where the team works through a "
            "structured problem under time pressure. Debrief each session together and name what "
            "made the decision easier or harder."
        )
    if "Collaboration" in stats["dev_areas"]:
        recs.append(
            "Assign cross-functional projects or rotate pair-work deliberately. This builds shared "
            "working norms and widens each person's range of working styles."
        )

    # Archetype-driven
    anchor_n = stats["archetype_counts"].get("Anchor", 0)
    if anchor_n > 0:
        recs.append(
            f"You have {anchor_n} Anchor profile(s). These people steady the team and keep it "
            "together under pressure. Give them defined responsibility for group cohesion, and make "
            "sure that work is recognised, because it is easy to overlook."
        )

    structured_n = (stats["archetype_counts"].get("Navigator", 0) +
                    stats["archetype_counts"].get("Compass", 0))
    if structured_n >= stats["n"] * 0.6:
        recs.append(
            "The team leans toward structured, methodical profiles. Schedule some open-ended or "
            "unstructured work so the group practises adapting when the path is not laid out for it."
        )

    communicative_n = (stats["archetype_counts"].get("Signal", 0) +
                       stats["archetype_counts"].get("Relay", 0))
    if communicative_n >= stats["n"] * 0.6:
        recs.append(
            "The team is weighted toward communicators and adaptors. Direct that into knowledge-sharing, "
            "mentoring of junior staff, or cross-team liaison roles, where the strength is most useful."
        )

    # Universal closer
    recs.append(
        "Hold a 30-minute team debrief using the individual profile PDFs as the starting point. "
        "Structured conversation about working styles is a low-cost, high-value use of a manager's "
        "time, and it supports both psychological safety and team cohesion."
    )

    return recs[:5]


# ─── Report section builders ──────────────────────────────────────────────────

def _section_cover(team_name, workshop_date, manager_name, st):
    story = []
    story.append(Spacer(1, 14 * mm))

    # Brand wordmark
    story.append(Paragraph(
        "The Performance Lens",
        ParagraphStyle("logo_txt", fontName="Helvetica-Bold",
                       fontSize=20, textColor=SKY_BLUE)))
    story.append(Paragraph(
        "by Saigon Young Professionals",
        ParagraphStyle("logo_sub", fontName="Helvetica",
                       fontSize=10, textColor=colors.HexColor("#90CAF9"))))
    story.append(Spacer(1, 18 * mm))

    # Main title
    story.append(Paragraph("TEAM<br/>DIAGNOSTIC<br/>REPORT", st["cover_title"]))

    # Sky accent rule
    story.append(HRFlowable(width=BODY_W, thickness=2,
                             color=SKY_BLUE, spaceAfter=5 * mm))

    # Team + date
    story.append(Paragraph(team_name.upper(), st["cover_sub"]))
    story.append(Paragraph(f"Workshop date: {workshop_date}", st["cover_meta"]))

    story.append(Spacer(1, 50 * mm))

    # Manager line
    story.append(Paragraph(
        f"Prepared for {manager_name}",
        ParagraphStyle("mgr", fontName="Helvetica-Bold",
                       fontSize=11, textColor=WHITE)))
    story.append(Paragraph(
        "Team Effectiveness Workshop  ·  Confidential",
        ParagraphStyle("conf", fontName="Helvetica",
                       fontSize=9, textColor=colors.HexColor("#90CAF9"))))

    # Switch template BEFORE the page break so page 2 gets the Content template
    story.append(NextPageTemplate("Content"))
    story.append(PageBreak())
    return story


def _section_snapshot(stats, st):
    story = []
    story.append(Paragraph("Team at a Glance", st["section_title"]))
    story.append(HRFlowable(width=BODY_W, thickness=1,
                             color=LIGHT_BLUE, spaceAfter=3 * mm))

    # Overview paragraph
    story.append(Paragraph(_overview_text(stats), st["body"]))
    story.append(Spacer(1, 3 * mm))

    # Stat boxes
    n_boxes = 4
    gap     = 4 * mm
    box_w   = (BODY_W - gap * (n_boxes - 1)) / n_boxes

    dominant = (stats["archetype_counts"].most_common(1)[0][0]
                if stats["archetype_counts"] else "—")
    boxes = [
        StatBox(stats["n"],               "Participants",  DARK_BLUE,  box_w),
        StatBox(f"{stats['overall_avg']}", "Avg Score",     SKY_BLUE,   box_w),
        StatBox(len(stats["strengths"]),   "Strengths",     SUCCESS,    box_w),
        StatBox(len(stats["dev_areas"]),   "Dev Areas",     WARNING,    box_w),
    ]
    row = Table([[b for b in boxes]], colWidths=[box_w] * n_boxes,
                hAlign="LEFT")
    row.setStyle(TableStyle([
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("COLPADDING",    (0, 0), (-1, -1), gap / 2),
    ]))
    story.append(row)
    story.append(Spacer(1, 5 * mm))

    # Archetype distribution table
    story.append(Paragraph("Archetype Distribution", st["sub_heading"]))

    rows = [["Archetype", "Count", "% Team", "Profile"]]
    for arch, cnt in sorted(stats["archetype_counts"].items(), key=lambda x: -x[1]):
        pct = f"{cnt / stats['n'] * 100:.0f}%"
        rows.append([arch, str(cnt), pct, ARCHETYPE_SUMMARY.get(arch, "")])

    arch_table = Table(rows,
                       colWidths=[34 * mm, 16 * mm, 18 * mm, BODY_W - 68 * mm])
    ts = [
        ("BACKGROUND",    (0, 0), (-1, 0),  DARK_BLUE),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  WHITE),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0),  8),
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 1), (-1, -1), 8.5),
        ("ALIGN",         (0, 0), (-1, -1), "LEFT"),
        ("ALIGN",         (1, 0), (2, -1),  "CENTER"),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, LIGHT_BLUE]),
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#DEE2E6")),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
    ]
    for i, (arch, _) in enumerate(
            sorted(stats["archetype_counts"].items(), key=lambda x: -x[1]), 1):
        col = ARCHETYPE_COLOURS.get(arch, MID_GREY)
        ts += [("TEXTCOLOR", (0, i), (0, i), col),
               ("FONTNAME",  (0, i), (0, i), "Helvetica-Bold")]

    arch_table.setStyle(TableStyle(ts))
    story.append(arch_table)
    return story


def _section_dimensions(stats, st):
    story = []
    story.append(Spacer(1, 5 * mm))
    story.append(Paragraph("Dimension Analysis", st["section_title"]))
    story.append(HRFlowable(width=BODY_W, thickness=1,
                             color=LIGHT_BLUE, spaceAfter=3 * mm))
    story.append(Paragraph(
        "Scores are normalised 0–100 per participant based on their role-specific question set. "
        "The dashed line marks the 60-point High/Low threshold.",
        st["caption"]))
    story.append(Spacer(1, 2 * mm))

    dims = [
        ("Communication",  stats["c_avg"],  stats["c_high"],  stats["c_low"]),
        ("Decision Making", stats["d_avg"], stats["d_high"],  stats["d_low"]),
        ("Collaboration",   stats["co_avg"], stats["co_high"], stats["co_low"]),
    ]
    for label, avg, high_n, low_n in dims:
        story.append(DimensionBar(label, avg, high_n, low_n))
        story.append(Spacer(1, 1 * mm))
        story.append(Paragraph(
            _dim_insight(label, avg, high_n, low_n, stats["n"]), st["body"]))
        desc = DIMENSION_DESCRIPTIONS.get(label, "")
        if desc:
            story.append(Paragraph(desc, st["caption"]))
        story.append(Spacer(1, 2 * mm))

    # Strengths / dev areas callout
    story.append(Spacer(1, 2 * mm))
    col_w = (BODY_W - 5 * mm) / 2

    s_lines = ("<b>✓ Team Strengths</b><br/>" +
               ("<br/>".join(f"• {x}" for x in stats["strengths"])
                if stats["strengths"] else "No dimensions currently above threshold."))
    d_lines = ("<b>△ Development Areas</b><br/>" +
               ("<br/>".join(f"• {x}" for x in stats["dev_areas"])
                if stats["dev_areas"] else "All three dimensions are above the threshold."))

    callout = Table(
        [[Paragraph(s_lines, ParagraphStyle("s", fontName="Helvetica", fontSize=9,
                                             textColor=colors.HexColor("#065F46"),
                                             leading=14)),
          Paragraph(d_lines, ParagraphStyle("d", fontName="Helvetica", fontSize=9,
                                             textColor=colors.HexColor("#92400E"),
                                             leading=14))]],
        colWidths=[col_w, col_w]
    )
    callout.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#D1FAE5")),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#FEF3C7")),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 9),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 9),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("COLPADDING",    (0, 0), (-1, -1), 2.5),
    ]))
    story.append(callout)
    return story


def _section_individuals(participants, st):
    story = []
    story.append(PageBreak())
    story.append(Paragraph("Individual Profiles", st["section_title"]))
    story.append(HRFlowable(width=BODY_W, thickness=1,
                             color=LIGHT_BLUE, spaceAfter=3 * mm))
    story.append(Paragraph(
        "Normalised scores (0–100) for each team member alongside their archetype classification. "
        "↑ = High (≥60)  ↓ = Low (<60).",
        st["caption"]))
    story.append(Spacer(1, 2 * mm))

    headers = ["Name", "Role", "Archetype", "Comm", "Decision", "Collab"]
    cws     = [44 * mm, 22 * mm, 28 * mm, 22 * mm, 24 * mm, 22 * mm]

    def fmt(val, level):
        marker = "↑" if level == "High" else "↓"
        return f"{round(val):.0f} {marker}"

    rows = [headers]
    for p in sorted(participants, key=lambda x: x.get("name", "")):
        rows.append([
            p.get("name", "—"),
            p.get("role", "—"),
            p.get("archetype", "—"),
            fmt(p["c_score"],  p.get("c_level", "")),
            fmt(p["d_score"],  p.get("d_level", "")),
            fmt(p["co_score"], p.get("co_level", "")),
        ])

    table = Table(rows, colWidths=cws)
    ts = [
        ("BACKGROUND",    (0, 0),  (-1, 0),  DARK_BLUE),
        ("TEXTCOLOR",     (0, 0),  (-1, 0),  WHITE),
        ("FONTNAME",      (0, 0),  (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0),  (-1, 0),  8),
        ("FONTNAME",      (0, 1),  (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 1),  (-1, -1), 8.5),
        ("ALIGN",         (0, 0),  (-1, -1), "CENTER"),
        ("ALIGN",         (0, 0),  (0,  -1), "LEFT"),
        ("ROWBACKGROUNDS",(0, 1),  (-1, -1), [WHITE, LIGHT_BLUE]),
        ("GRID",          (0, 0),  (-1, -1), 0.5, colors.HexColor("#DEE2E6")),
        ("TOPPADDING",    (0, 0),  (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0),  (-1, -1), 5),
        ("LEFTPADDING",   (0, 0),  (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0),  (-1, -1), 5),
    ]
    for i, p in enumerate(
            sorted(participants, key=lambda x: x.get("name", "")), 1):
        col = ARCHETYPE_COLOURS.get(p.get("archetype", ""), NEAR_BLACK)
        ts += [("TEXTCOLOR", (2, i), (2, i), col),
               ("FONTNAME",  (2, i), (2, i), "Helvetica-Bold")]

    table.setStyle(TableStyle(ts))
    story.append(table)
    return story


def _section_recommendations(stats, st):
    story = []
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Manager Recommendations", st["section_title"]))
    story.append(HRFlowable(width=BODY_W, thickness=1,
                             color=LIGHT_BLUE, spaceAfter=3 * mm))
    story.append(Paragraph(
        "These recommendations are based on your team's dimension scores and archetype distribution. "
        "They are ordered by likely impact given the team's results.",
        st["caption"]))
    story.append(Spacer(1, 2 * mm))

    for i, rec in enumerate(_recommendations(stats), 1):
        num_style = ParagraphStyle(
            "rn", fontName="Helvetica-Bold", fontSize=14,
            textColor=SKY_BLUE, alignment=TA_CENTER)
        rec_style = ParagraphStyle(
            "rt", fontName="Helvetica", fontSize=9,
            textColor=NEAR_BLACK, leading=14)
        row = Table(
            [[Paragraph(str(i), num_style),
              Paragraph(rec, rec_style)]],
            colWidths=[12 * mm, BODY_W - 12 * mm]
        )
        row.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 3),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 3),
        ]))
        story.append(row)
        if i < len(_recommendations(stats)):
            story.append(HRFlowable(width=BODY_W, thickness=0.5,
                                     color=LIGHT_BLUE, spaceAfter=1 * mm))

    # Closing note
    story.append(Spacer(1, 7 * mm))
    story.append(HRFlowable(width=BODY_W, thickness=1, color=LIGHT_BLUE))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "Individual profile PDFs have been sent directly to each participant. "
        "You also have the team data sheet, shared separately, which contains all scores "
        "in a searchable format. "
        "For questions about the Team Effectiveness Workshop, contact your SYP facilitator.",
        ParagraphStyle("closing", fontName="Helvetica", fontSize=8,
                       textColor=MID_GREY, leading=12)
    ))
    return story


# ─── Master build function ────────────────────────────────────────────────────

def _enrich_participant(p: dict) -> dict:
    """
    Ensures each participant dict has c_level / d_level / co_level.
    If the caller omitted them, derive from the normalised scores
    using the standard threshold (≥ 60 = High, < 60 = Low).
    Also coerces score values to float so arithmetic never breaks.
    """
    p = dict(p)
    p["c_score"]  = float(p.get("c_score",  0) or 0)
    p["d_score"]  = float(p.get("d_score",  0) or 0)
    p["co_score"] = float(p.get("co_score", 0) or 0)
    # Always derive binary High/Low from scores — the live scenario uses a
    # 4-tier label (Advanced/Proficient/Developing/Foundational) which would
    # break the High/Low counting logic in the report.
    p["c_level"]  = "High" if p["c_score"]  >= 60 else "Low"
    p["d_level"]  = "High" if p["d_score"]  >= 60 else "Low"
    p["co_level"] = "High" if p["co_score"] >= 60 else "Low"
    return p


def generate_manager_report_pdf(data: dict) -> bytes:
    """
    Accepts the data dict (see module docstring for schema).
    Returns the PDF as raw bytes.

    c_level / d_level / co_level are optional — they are derived
    from the normalised scores if not supplied by the caller.
    """
    team_name     = data.get("team_name",     "Your Team")
    workshop_date = data.get("workshop_date",
                             datetime.now().strftime("%d %B %Y"))
    manager_name  = data.get("manager_name",  "Team Manager")
    participants  = [_enrich_participant(p) for p in data.get("participants", [])]

    stats = _calc_stats(participants)
    st    = _styles()

    buf = io.BytesIO()

    doc = BaseDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=L_MARGIN,
        rightMargin=R_MARGIN,
        topMargin=T_MARGIN_CONTENT + 4 * mm,
        bottomMargin=B_MARGIN + 4 * mm,
    )

    # Cover frame (taller — no header bar)
    cover_frame = Frame(
        L_MARGIN,
        B_MARGIN,
        BODY_W,
        PAGE_H - T_MARGIN_COVER - B_MARGIN,
        id="cover",
    )
    # Content frame (shorter — header + footer)
    content_frame = Frame(
        L_MARGIN,
        B_MARGIN + 4 * mm,
        BODY_W,
        PAGE_H - T_MARGIN_CONTENT - B_MARGIN - 4 * mm,
        id="content",
    )

    doc.addPageTemplates([
        PageTemplate(id="Cover",   frames=[cover_frame],   onPage=_draw_cover),
        PageTemplate(id="Content", frames=[content_frame], onPage=_draw_content),
    ])

    story = []
    story += _section_cover(team_name, workshop_date, manager_name, st)
    story += _section_snapshot(stats, st)
    story += _section_dimensions(stats, st)
    story += _section_individuals(participants, st)
    story += _section_recommendations(stats, st)

    doc.build(story)
    buf.seek(0)
    return buf.read()


# ─── Flask route (copy into your Railway app.py) ─────────────────────────────

def print_flask_snippet():
    print("""
# ─────────────────────────────────────────────────────────────────────────────
# ADD TO YOUR RAILWAY app.py
# ─────────────────────────────────────────────────────────────────────────────
import io
from flask import request, send_file, jsonify
from generate_manager_report import generate_manager_report_pdf

@app.route("/generate-manager-report", methods=["POST"])
def manager_report():
    data = request.get_json(force=True)
    if not data or "participants" not in data:
        return jsonify({"error": "participants array is required"}), 400
    if len(data["participants"]) == 0:
        return jsonify({"error": "participants array must not be empty"}), 400
    try:
        pdf_bytes = generate_manager_report_pdf(data)
        safe_name = data.get("team_name", "Team").replace(" ", "_")
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"SYP_Manager_Report_{safe_name}.pdf",
        )
    except Exception as e:
        app.logger.error(f"Manager report generation failed: {e}")
        return jsonify({"error": str(e)}), 500
# ─────────────────────────────────────────────────────────────────────────────
""")


# ─── Sample data + CLI entrypoint ────────────────────────────────────────────

SAMPLE_DATA = {
    "team_name":     "AED Global",
    "workshop_date": "6 May 2026",
    "manager_name":  "Sarah Mitchell",
    "manager_email": "sarah@aedglobal.com",
    "participants": [
        {
            "name": "Alice Nguyen",   "role": "Guide",
            "c_score": 78, "d_score": 42, "co_score": 85,
            "c_level": "High", "d_level": "Low",  "co_level": "High",
            "archetype": "Signal"
        },
        {
            "name": "Ben Tran",       "role": "Builder",
            "c_score": 65, "d_score": 71, "co_score": 68,
            "c_level": "High", "d_level": "High", "co_level": "High",
            "archetype": "Navigator"
        },
        {
            "name": "Chi Pham",       "role": "Observer",
            "c_score": 55, "d_score": 80, "co_score": 45,
            "c_level": "Low",  "d_level": "High", "co_level": "Low",
            "archetype": "Compass"
        },
        {
            "name": "Duc Le",         "role": "Guide",
            "c_score": 45, "d_score": 38, "co_score": 40,
            "c_level": "Low",  "d_level": "Low",  "co_level": "Low",
            "archetype": "Anchor"
        },
        {
            "name": "Emma Hoang",     "role": "Builder",
            "c_score": 72, "d_score": 66, "co_score": 74,
            "c_level": "High", "d_level": "High", "co_level": "High",
            "archetype": "Navigator"
        },
        {
            "name": "Feng Liu",       "role": "Observer",
            "c_score": 48, "d_score": 74, "co_score": 80,
            "c_level": "Low",  "d_level": "High", "co_level": "High",
            "archetype": "Navigator"
        },
    ]
}

if __name__ == "__main__":
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        with open(sys.argv[1]) as f:
            data = json.load(f)
        out = sys.argv[2] if len(sys.argv) > 2 else "SYP_Manager_Report.pdf"
    else:
        data = SAMPLE_DATA
        out  = "SYP_Manager_Report_Sample.pdf"

    pdf = generate_manager_report_pdf(data)

    with open(out, "wb") as f:
        f.write(pdf)

    print(f"✓  PDF generated: {out}  ({len(pdf):,} bytes)")
    print(f"   Team: {data.get('team_name')}  |  {len(data.get('participants', []))} participants")
    print()
    print_flask_snippet()
