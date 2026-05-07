#!/usr/bin/env python3
"""
SYP Team Effectiveness Lab — Manager Team Diagnostic Report PDF Generator
4-page team overview PDF: Cover / Team Overview / Dimension Analysis / Individual Profiles + Recommendations
"""

import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

# ─── Brand palette ──────────────────────────────────────────────────────────────
NAVY        = colors.HexColor("#0D1B4B")
TEAL        = colors.HexColor("#009688")
TEAL_LIGHT  = colors.HexColor("#E0F2F1")
WHITE       = colors.white
NEAR_BLACK  = colors.HexColor("#1A1A2E")
MID_GREY    = colors.HexColor("#888888")
LIGHT_GREY  = colors.HexColor("#F5F7FA")
RULE_GREY   = colors.HexColor("#E0E0E0")
GREEN_DARK  = colors.HexColor("#1B5E20")
GREEN_LIGHT = colors.HexColor("#E8F5E9")
GREEN_MID   = colors.HexColor("#2E7D32")
AMBER_DARK  = colors.HexColor("#E65100")
AMBER_LIGHT = colors.HexColor("#FFF3E0")
AMBER_MID   = colors.HexColor("#F57C00")

# Archetype accent colours — pill_bg from individual profiles
ARCHETYPE_COLORS = {
    "Operator":  colors.HexColor("#B45309"),
    "Architect": colors.HexColor("#6D28D9"),
    "Navigator": colors.HexColor("#1D4ED8"),
    "Signal":    colors.HexColor("#B91C1C"),
    "Anchor":    colors.HexColor("#047857"),
    "Ember":     colors.HexColor("#4B5563"),
}

ARCHETYPE_DESCRIPTIONS = {
    "Architect": "Strategic · Analytical · Systematic — builds robust frameworks",
    "Navigator": "Adaptive · Decisive · Collaborative — steers through complexity",
    "Anchor":    "Dependable · Grounded · Steadying — holds the team together",
    "Signal":    "Communicative · Expressive · Inclusive — connects the team",
    "Operator":  "Structured · Decisive · Coordinated — drives consistent execution",
    "Ember":     "Developing · Potential · Emerging — growing toward full contribution",
}

ARCHETYPE_ORDER = ["Architect", "Navigator", "Anchor", "Signal", "Operator", "Ember"]

W, H = A4       # 595.28 x 841.89 pts
ML   = 20 * mm  # left margin
MR   = 20 * mm  # right margin
MT   = 20 * mm  # top margin
MB   = 18 * mm  # bottom margin
CW   = W - ML - MR  # usable content width


# ─── Helpers ────────────────────────────────────────────────────────────────────

def draw_para(c, text, x, y, width, font="Helvetica", size=9.5,
              color=NEAR_BLACK, align=TA_JUSTIFY, leading=14):
    """Draw a flowing Paragraph, return y after drawing."""
    sty = ParagraphStyle("p", fontName=font, fontSize=size, textColor=color,
                          alignment=align, leading=leading)
    p = Paragraph(text, sty)
    _, ph = p.wrap(width, 9999)
    p.drawOn(c, x, y - ph)
    return y - ph


def header_band(c, company, page_num):
    """Navy header + teal underline used on pages 2-4."""
    bh = 14 * mm
    c.setFillColor(NAVY)
    c.rect(0, H - bh, W, bh, fill=1, stroke=0)
    c.setFillColor(TEAL)
    c.rect(0, H - bh - 2, W, 2, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(WHITE)
    c.drawString(ML, H - bh + 4 * mm, "TEAM DIAGNOSTIC REPORT")
    c.setFont("Helvetica", 9)
    c.drawRightString(W - MR, H - bh + 4 * mm, company)
    c.setFont("Helvetica", 7.5)
    c.setFillColor(MID_GREY)
    c.drawCentredString(W / 2, MB - 5 * mm, f"Team Effectiveness Lab  ·  Page {page_num}  ·  Confidential")


def section_title(c, text, y):
    """Teal accent bar + bold section heading. Returns y below heading."""
    c.setFillColor(TEAL)
    c.rect(ML, y - 1, 3 * mm, 5.5 * mm, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(NAVY)
    c.drawString(ML + 5 * mm, y, text)
    return y - 9 * mm


def h_rule(c, y, color=RULE_GREY):
    c.setStrokeColor(color)
    c.setLineWidth(0.5)
    c.line(ML, y, W - MR, y)


def stat_box(c, x, y, w, h, label, value, sub=None):
    """Rounded stat box with large teal value."""
    c.setFillColor(LIGHT_GREY)
    c.roundRect(x, y - h, w, h, 3, fill=1, stroke=0)
    c.setFillColor(TEAL)
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(x + w / 2, y - h / 2 + 2, str(value))
    c.setFont("Helvetica", 7.5)
    c.setFillColor(MID_GREY)
    c.drawCentredString(x + w / 2, y - h / 2 - 10, label.upper())
    if sub:
        c.setFont("Helvetica", 7)
        c.drawCentredString(x + w / 2, y - h + 5, sub)


def dimension_bar(c, x, y, label, avg_score, high, low, n, interpretation, description):
    """Horizontal dimension bar. Returns y after drawing."""
    bar_h = 8 * mm
    bar_w = CW - 28 * mm

    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(NAVY)
    c.drawString(x, y, label)
    y -= 5 * mm

    # Background track
    c.setFillColor(RULE_GREY)
    c.roundRect(x, y - bar_h, bar_w, bar_h, 3, fill=1, stroke=0)

    # Score fill
    fill_w = max((avg_score / 100) * bar_w, 4)
    c.setFillColor(TEAL if avg_score >= 60 else AMBER_MID)
    c.roundRect(x, y - bar_h, fill_w, bar_h, 3, fill=1, stroke=0)

    # Score label
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(WHITE if avg_score > 15 else NEAR_BLACK)
    c.drawString(x + max(fill_w - 20, 2), y - bar_h + 2.5 * mm, f"{avg_score:.1f}")

    # Dashed threshold at 60
    thresh_x = x + 0.6 * bar_w
    c.setStrokeColor(NEAR_BLACK)
    c.setLineWidth(1.2)
    c.setDash(3, 3)
    c.line(thresh_x, y - bar_h - 2, thresh_x, y + 2)
    c.setDash()
    c.setFont("Helvetica", 7)
    c.setFillColor(MID_GREY)
    c.drawCentredString(thresh_x, y - bar_h - 4 * mm, "60")

    # Hi/Lo stats
    sx = x + bar_w + 4 * mm
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(GREEN_MID)
    c.drawString(sx, y - 3 * mm, f"↑ {high}/{n}")
    c.setFillColor(AMBER_DARK)
    c.drawString(sx, y - bar_h + 1.5 * mm, f"↓ {low}/{n}")

    y -= bar_h + 5 * mm

    # Bold interpretation
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(NAVY)
    c.drawString(x, y, interpretation)
    y -= 4 * mm

    # Description
    sty = ParagraphStyle("d", fontName="Helvetica", fontSize=8.5,
                          textColor=colors.HexColor("#444444"), leading=12)
    p = Paragraph(description, sty)
    _, ph = p.wrap(CW, 200)
    p.drawOn(c, x, y - ph)
    y -= ph + 7 * mm
    return y


# ─── Page 1: Cover ──────────────────────────────────────────────────────────────

def draw_cover(c, manager_name, company, workshop_date):
    c.setFillColor(NAVY)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    c.setFillColor(TEAL)
    c.rect(0, H - 6 * mm, W, 6 * mm, fill=1, stroke=0)
    c.rect(0, 0, W, 4 * mm, fill=1, stroke=0)
    c.rect(ML - 2, 0.14 * H, 3, 0.72 * H, fill=1, stroke=0)

    c.setFont("Helvetica", 8.5)
    c.setFillColor(TEAL)
    c.drawString(ML + 8, 0.83 * H, "THE PERFORMANCE LENS  ·  SAIGON YOUNG PROFESSIONALS")

    ty = 0.73 * H
    c.setFont("Helvetica-Bold", 38)
    c.setFillColor(WHITE)
    c.drawString(ML + 8, ty,      "TEAM DIAGNOSTIC")
    c.drawString(ML + 8, ty - 44, "REPORT")

    c.setFillColor(TEAL)
    c.rect(ML + 8, ty - 58, CW * 0.6, 2, fill=1, stroke=0)

    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(WHITE)
    c.drawString(ML + 8, ty - 83, company)

    c.setFont("Helvetica", 12)
    c.setFillColor(TEAL)
    c.drawString(ML + 8, ty - 106, workshop_date)

    c.setFont("Helvetica", 11)
    c.setFillColor(colors.HexColor("#B0BEC5"))
    c.drawString(ML + 8, ty - 133, f"Prepared for  {manager_name}")

    c.setFont("Helvetica", 8.5)
    c.setFillColor(colors.HexColor("#607D8B"))
    c.drawCentredString(W / 2, 0.09 * H, "Team Effectiveness Lab  ·  Confidential")


# ─── Page 2: Team at a Glance + Comm + Decision bars ───────────────────────────

def draw_page2(c, company, participants, n, overall_avg,
               avg_comm, avg_decision, comm_high, comm_low, decision_high, decision_low,
               strengths, dev_areas, archetype_counts):
    header_band(c, company, 2)
    y = H - 18 * mm - 5 * mm

    y = section_title(c, "Team at a Glance", y)

    strengths_str = " and ".join(strengths) if strengths else "none of the measured dimensions"
    dev_sentence  = (
        f"Development opportunities were identified in {' and '.join(dev_areas)}."
        if dev_areas else
        "All dimensions exceeded the 60-point performance threshold."
    )
    intro = (
        f"This report summarises data from <b>{n} participant{'s' if n != 1 else ''}</b> who completed "
        f"the Team Effectiveness Lab. Across all three dimensions, the team averaged "
        f"<b>{overall_avg:.1f} out of 100</b>. Collective strengths emerged in {strengths_str}. "
        f"{dev_sentence}"
    )
    y = draw_para(c, intro, ML, y, CW)
    y -= 5 * mm

    # Stat boxes
    gap   = 3 * mm
    box_w = (CW - 3 * gap) / 4
    box_h = 18 * mm
    bx = ML
    stat_box(c, bx, y, box_w, box_h, "Participants", n);             bx += box_w + gap
    stat_box(c, bx, y, box_w, box_h, "Avg Score", f"{overall_avg:.0f}"); bx += box_w + gap
    stat_box(c, bx, y, box_w, box_h, "Strengths", len(strengths), "dims ≥ 60"); bx += box_w + gap
    stat_box(c, bx, y, box_w, box_h, "Dev Areas",  len(dev_areas),  "dims < 60")
    y -= box_h + 7 * mm

    h_rule(c, y);  y -= 6 * mm

    # Archetype Distribution
    y = section_title(c, "Archetype Distribution", y)

    col_w = [CW * 0.24, CW * 0.11, CW * 0.11, CW * 0.54]
    hx = ML
    c.setFont("Helvetica-Bold", 7.5);  c.setFillColor(MID_GREY)
    for lbl, cw in zip(["Archetype", "Count", "% Team", "Profile"], col_w):
        c.drawString(hx, y, lbl.upper());  hx += cw
    y -= 3 * mm;  h_rule(c, y);  y -= 4 * mm

    desc_sty = ParagraphStyle("ds", fontName="Helvetica", fontSize=8,
                               textColor=colors.HexColor("#555555"), leading=11)
    shown = sorted(archetype_counts.items(),
                   key=lambda x: (-x[1], ARCHETYPE_ORDER.index(x[0]) if x[0] in ARCHETYPE_ORDER else 99))

    for arch, cnt in shown:
        pct = cnt / n * 100
        ac  = ARCHETYPE_COLORS.get(arch, MID_GREY)
        rx  = ML

        c.setFillColor(ac);  c.rect(rx, y - 9, 3, 11, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 9);  c.setFillColor(ac)
        c.drawString(rx + 5, y - 6, arch);  rx += col_w[0]

        c.setFont("Helvetica-Bold", 9);  c.setFillColor(NEAR_BLACK)
        c.drawString(rx + 2, y - 6, str(cnt));  rx += col_w[1]

        c.setFont("Helvetica", 9);  c.setFillColor(MID_GREY)
        c.drawString(rx + 2, y - 6, f"{pct:.0f}%");  rx += col_w[2]

        dp = Paragraph(ARCHETYPE_DESCRIPTIONS.get(arch, ""), desc_sty)
        _, dph = dp.wrap(col_w[3] - 2, 40)
        dp.drawOn(c, rx, y - dph + 2)

        y -= max(dph, 12) + 4
        h_rule(c, y, RULE_GREY);  y -= 3 * mm

    y -= 3 * mm;  h_rule(c, y);  y -= 7 * mm

    # Dimension Analysis
    y = section_title(c, "Dimension Analysis", y)

    y = dimension_bar(c, ML, y, "Communication", avg_comm, comm_high, comm_low, n,
        f"Communication is {'a team strength' if avg_comm >= 60 else 'an area for development'} — "
        f"{comm_high} of {n} participants scored above threshold.",
        "Communication captures how clearly participants expressed information, listened under pressure, "
        "and adapted their style when instructions were ambiguous or roles shifted. High-scoring teams "
        "maintain clarity even when the environment is chaotic.")

    if y > MB + 55 * mm:
        dimension_bar(c, ML, y, "Decision Making", avg_decision, decision_high, decision_low, n,
            f"Decision Making is {'a team strength' if avg_decision >= 60 else 'an area for development'} — "
            f"{decision_high} of {n} participants performed above threshold.",
            "Decision Making reflects how participants assessed constraints, committed under uncertainty, "
            "and adapted their approach when new information emerged. High scores indicate participants "
            "who make timely, grounded decisions without overcorrecting when plans change.")


# ─── Page 3: Collaboration + Strengths / Dev Areas ──────────────────────────────

def draw_page3(c, company, n, avg_collab, collab_high, collab_low, strengths, dev_areas):
    header_band(c, company, 3)
    y = H - 18 * mm - 5 * mm

    y = section_title(c, "Dimension Analysis (continued)", y)

    y = dimension_bar(c, ML, y, "Collaboration", avg_collab, collab_high, collab_low, n,
        f"Collaboration is {'a team strength' if avg_collab >= 60 else 'an area for growth'} — "
        f"{collab_high} of {n} participants exceeded threshold.",
        "Collaboration measures how participants contributed to shared goals, supported others during "
        "difficulty, and adapted their role when team dynamics shifted. Strong collaborators raise the "
        "floor of overall team performance, not just their own output.")

    h_rule(c, y);  y -= 7 * mm

    # Team Strengths
    sh = 10 * mm + len(strengths) * 7.5 * mm if strengths else 14 * mm
    c.setFillColor(GREEN_LIGHT);  c.roundRect(ML, y - sh, CW, sh, 4, fill=1, stroke=0)
    c.setFillColor(GREEN_MID);    c.roundRect(ML, y - sh, 4, sh, 0, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 10);  c.setFillColor(GREEN_DARK)
    c.drawString(ML + 8, y - 7 * mm, "✓  Team Strengths")
    by = y - 13 * mm
    if strengths:
        for s in strengths:
            c.setFont("Helvetica", 9);  c.setFillColor(GREEN_DARK)
            c.drawString(ML + 14, by, f"• {s} — team average exceeds the 60-point performance threshold")
            by -= 7 * mm
    else:
        c.setFont("Helvetica", 9);  c.setFillColor(GREEN_DARK)
        c.drawString(ML + 14, by, "No dimensions reached the 60-point threshold in this session.")
    y -= sh + 5 * mm

    # Dev Areas
    dh = 10 * mm + len(dev_areas) * 7.5 * mm if dev_areas else 14 * mm
    c.setFillColor(AMBER_LIGHT);  c.roundRect(ML, y - dh, CW, dh, 4, fill=1, stroke=0)
    c.setFillColor(AMBER_MID);    c.roundRect(ML, y - dh, 4, dh, 0, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 10);  c.setFillColor(AMBER_DARK)
    c.drawString(ML + 8, y - 7 * mm, "⚡  Development Areas")
    by = y - 13 * mm
    if dev_areas:
        for d in dev_areas:
            c.setFont("Helvetica", 9);  c.setFillColor(AMBER_DARK)
            c.drawString(ML + 14, by, f"• {d} — team average is below the 60-point performance threshold")
            by -= 7 * mm
    else:
        c.setFont("Helvetica", 9);  c.setFillColor(AMBER_DARK)
        c.drawString(ML + 14, by, "All dimensions above threshold — no development areas identified.")


# ─── Page 4: Individual Profiles + Manager Recommendations ──────────────────────

def draw_page4(c, company, participants, recommendations):
    header_band(c, company, 4)
    y = H - 18 * mm - 5 * mm

    y = section_title(c, "Individual Profiles", y)

    col_w = [CW * 0.30, CW * 0.22, CW * 0.16, CW * 0.16, CW * 0.16]
    hx = ML
    c.setFont("Helvetica-Bold", 8);  c.setFillColor(MID_GREY)
    for lbl, cw in zip(["Name", "Archetype", "Comm", "Decision", "Collab"], col_w):
        c.drawString(hx, y, lbl.upper());  hx += cw
    y -= 3 * mm;  h_rule(c, y, RULE_GREY);  y -= 4 * mm

    for ri, p in enumerate(participants):
        name = p.get("name", "—")
        arch = p.get("archetype", "—")
        comm = p.get("comm_score", 0)
        dec  = p.get("decision_score", 0)
        col  = p.get("collab_score", 0)
        ac   = ARCHETYPE_COLORS.get(arch, MID_GREY)
        rh   = 7 * mm

        c.setFillColor(WHITE if ri % 2 == 0 else LIGHT_GREY)
        c.rect(ML, y - rh, CW, rh, fill=1, stroke=0)

        rx = ML
        c.setFont("Helvetica-Bold", 9);  c.setFillColor(NEAR_BLACK)
        c.drawString(rx + 2, y - 5, name[:30]);  rx += col_w[0]
        c.setFont("Helvetica-Bold", 8.5);  c.setFillColor(ac)
        c.drawString(rx + 2, y - 5, arch);  rx += col_w[1]
        for si, score in enumerate([comm, dec, col]):
            c.setFont("Helvetica", 9)
            c.setFillColor(GREEN_MID if score >= 60 else AMBER_DARK)
            c.drawString(rx + 2, y - 5, f"{'↑' if score >= 60 else '↓'} {score}")
            rx += col_w[2 + si]

        y -= rh;  h_rule(c, y, RULE_GREY)

    y -= 7 * mm;  h_rule(c, y);  y -= 7 * mm

    # Manager Recommendations
    y = section_title(c, "Manager Recommendations", y)

    title_sty = ParagraphStyle("rt", fontName="Helvetica-Bold", fontSize=10,
                                textColor=NAVY, leading=14)
    body_sty  = ParagraphStyle("rb", fontName="Helvetica", fontSize=9,
                                textColor=colors.HexColor("#333333"), leading=13,
                                alignment=TA_JUSTIFY)

    for i, (title, body) in enumerate(recommendations, 1):
        c.setFillColor(TEAL)
        c.circle(ML + 4 * mm, y - 3 * mm, 4 * mm, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 9);  c.setFillColor(WHITE)
        c.drawCentredString(ML + 4 * mm, y - 4.5 * mm, str(i))

        tp = Paragraph(title, title_sty)
        _, tph = tp.wrap(CW - 12 * mm, 40)
        tp.drawOn(c, ML + 12 * mm, y - tph)
        y -= tph + 2 * mm

        bp = Paragraph(body, body_sty)
        _, bph = bp.wrap(CW - 12 * mm, 300)
        bp.drawOn(c, ML + 12 * mm, y - bph)
        y -= bph + 7 * mm

    note_y = max(y - 4 * mm, MB + 8 * mm)
    h_rule(c, note_y)
    c.setFont("Helvetica", 7.5);  c.setFillColor(MID_GREY)
    c.drawString(ML, note_y - 5 * mm,
                 "Individual profile PDFs have been sent directly to each participant. "
                 "This report is for the manager's reference only.")


# ─── Recommendations engine ─────────────────────────────────────────────────────

def generate_recommendations(participants, strengths, dev_areas, archetype_counts, n):
    recs = []

    recs.append((
        "Facilitate a Team Debrief Using Individual Profiles",
        "Each participant has received their personal Team Effectiveness Profile PDF. Schedule a "
        "30–45 minute team debrief where each participant shares one insight from their profile. "
        "This converts individual self-awareness into shared team understanding — the highest-leverage "
        "next step after any team assessment, regardless of how scores landed."
    ))

    ember_count = archetype_counts.get("Ember", 0)
    if ember_count > 0 and len(recs) < 3:
        plural = ember_count > 1
        recs.append((
            f"Structured Mentoring for {'Emerging Contributors' if plural else 'an Emerging Contributor'}",
            f"{'Several participants' if plural else 'One participant'} received the Ember profile, "
            "indicating dimensions that are still developing. Pair these individuals with higher-scoring "
            "teammates as informal mentors, focusing on whichever dimension scored lowest. "
            "A bi-weekly 30-minute check-in over the next 90 days will accelerate growth significantly."
        ))

    if "Decision Making" in dev_areas and len(recs) < 3:
        avg_d = sum(p["decision_score"] for p in participants) / n
        recs.append((
            "Introduce a Lightweight Decision-Making Framework",
            f"The team averaged {avg_d:.1f} in Decision Making — below the 60-point threshold for reliable "
            "performance under pressure. Introduce a simple protocol (a RACI matrix or pre-mortem practice) "
            "for your next three significant decisions. This builds the muscle systematically without "
            "requiring major process overhaul."
        ))

    if "Collaboration" in dev_areas and len(recs) < 3:
        avg_co = sum(p["collab_score"] for p in participants) / n
        recs.append((
            "Structured Collaboration Practice",
            f"With a team Collaboration average of {avg_co:.1f}, the group benefits from making "
            "collaboration explicit rather than assumed. Run your next project kick-off using a simple "
            "working agreement — 30 minutes defining how decisions will be made, how disagreement will "
            "be handled, and how progress will be shared."
        ))

    if "Communication" in dev_areas and len(recs) < 3:
        avg_c = sum(p["comm_score"] for p in participants) / n
        recs.append((
            "Communication Clarity Initiative",
            f"The team's Communication average of {avg_c:.1f} signals consistent opportunities to improve "
            "how information flows. Introduce a 'clarity check' habit: after any briefing, ask the receiver "
            "to summarise what they heard. This single practice dramatically reduces miscommunication-driven "
            "rework and builds active listening as a team norm."
        ))

    return recs[:3]


# ─── Main entry point ────────────────────────────────────────────────────────────

def generate_manager_report_bytes(manager_name: str, company: str,
                                   workshop_date: str, participants: list) -> bytes:
    """
    Generate a 4-page team manager report PDF, return raw bytes.

    participants: list of dicts with keys:
        name (str), archetype (str),
        comm_score (int 0-100), decision_score (int 0-100), collab_score (int 0-100)
    """
    if not participants:
        raise ValueError("participants list must not be empty")

    buf = io.BytesIO()
    c   = rl_canvas.Canvas(buf, pagesize=A4)

    n            = len(participants)
    avg_comm     = sum(p["comm_score"]     for p in participants) / n
    avg_decision = sum(p["decision_score"] for p in participants) / n
    avg_collab   = sum(p["collab_score"]   for p in participants) / n
    overall_avg  = (avg_comm + avg_decision + avg_collab) / 3

    comm_high     = sum(1 for p in participants if p["comm_score"]     >= 60)
    decision_high = sum(1 for p in participants if p["decision_score"] >= 60)
    collab_high   = sum(1 for p in participants if p["collab_score"]   >= 60)
    comm_low      = n - comm_high
    decision_low  = n - decision_high
    collab_low    = n - collab_high

    strengths = [d for d, a in [("Communication", avg_comm),
                                  ("Decision Making", avg_decision),
                                  ("Collaboration", avg_collab)] if a >= 60]
    dev_areas = [d for d, a in [("Communication", avg_comm),
                                  ("Decision Making", avg_decision),
                                  ("Collaboration", avg_collab)] if a < 60]

    archetype_counts = {}
    for p in participants:
        arch = p.get("archetype", "Unknown")
        archetype_counts[arch] = archetype_counts.get(arch, 0) + 1

    recommendations = generate_recommendations(
        participants, strengths, dev_areas, archetype_counts, n
    )

    draw_cover(c, manager_name, company, workshop_date)
    c.showPage()

    draw_page2(c, company, participants, n, overall_avg,
               avg_comm, avg_decision, comm_high, comm_low, decision_high, decision_low,
               strengths, dev_areas, archetype_counts)
    c.showPage()

    draw_page3(c, company, n, avg_collab, collab_high, collab_low, strengths, dev_areas)
    c.showPage()

    draw_page4(c, company, participants, recommendations)
    c.save()

    buf.seek(0)
    return buf.read()
