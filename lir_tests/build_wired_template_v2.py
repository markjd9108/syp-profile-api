#!/usr/bin/env python3
"""
Build-time transformer v2: approved Claude Design bundle -> wired LIR template
per CHANGE ORDER 1 + Composition Spec v2.

Amendments over v1 build:
  CO1 §1  Page 2 restructure (verdict + 2x2 at-a-glance grid + ntw + one move)
  CO1 §2  Page 3: dimension strip, locked intro/legend, table pagination
  CO1 §3  Page 5: locked intro, group captions, group table pagination
  CO1 §4  Page 7: TARGETED · 90 MINUTES
  CO1 §5  Appendix: Focus groups locked block
  CO1 §6  Dynamic page count (8-10+), dynamic page numbers, no orphaned headers
Plus everything from the v1 build (payload hook, vendored React, guards).
Output: lir_template_wired.html with token __LIR_PAYLOAD_JSON__.
"""
import json, re

SRC = "bundle.html"
OUT = "lir_template_wired.html"

# ---------------------------------------------------------------------------
# Locked copy (Change Order 1 / Data Contract; ships verbatim)
FALLBACK_STRETCH_ALL = ("No members sit in the Stretch group this round. When every member "
    "flags on at least one dimension, the pattern belongs to the team as a whole. "
    "The Action Plan on the next page is built around it.")
FALLBACK_STRETCH_SHORT = "No members sit in the Stretch group this round."
FALLBACK_CHECKIN_ALL = ("No members sit in the Check-In group this round. When every member "
    "clears the threshold on every dimension, the work ahead is stretch, and the "
    "Action Plan on the next page is built around it.")
FALLBACK_CHECKIN_SHORT = "No members sit in the Check-In group this round."

P3_INTRO = ("The full team in one view. The Focus column marks who needs a supporting "
            "conversation (Check-In) and who is ready for more (Stretch).")
P3_LEGEND = ("Amber marks an area needing support. Check-In: at least one area needs "
             "support. Stretch: strong across the board, ready for more.")
P5_INTRO = ("Two groups deserve deliberate attention this quarter. The conversation "
            "themes are starting points for a 1:1, in your own words.")
CI_CAPTION = "At least one area needs support. Worth a conversation this quarter."
ST_CAPTION = "Strong across the board. Ready to be given more."
APPENDIX_FOCUS = ("Check-In marks members with at least one dimension below the 60 working "
                  "threshold. Stretch marks members above 60 on every dimension with an "
                  "average of 70 or higher. Members between the two appear in the team "
                  "table without a flag.")

FOOTER = """<div style="padding:0 60px 30px">
      <div style="border-top:1px solid var(--rule-200);padding-top:10px;display:flex;justify-content:space-between;align-items:flex-end">
        <div>
          <div style="font-size:11px;letter-spacing:0.13em;text-transform:uppercase;color:var(--slate-600);font-weight:600">The Performance Lens</div>
          <div style="font-size:11px;color:var(--slate-400);margin-top:3px">Human skills for a digital future.</div>
        </div>
        <div style="font-size:11px;letter-spacing:0.13em;text-transform:uppercase;color:var(--slate-400);font-weight:600">Page %%PAGE%% of %%TOTAL%%</div>
      </div>
    </div>"""

RUNNING_HEADER = """<div style="padding:44px 60px 0">
      <x-import component-from-global-scope="ThePerformanceLensDesignSystem_4a127a.RunningHeader" doc-name="Team Effectiveness Workshop" brand="Leadership Insight Report" section="Confidential" hint-size="100%,32px"></x-import>
    </div>"""

TH = ('text-align:{al};font-size:11px;letter-spacing:0.1em;text-transform:uppercase;'
      'color:var(--navy-900);font-weight:700;padding:{pad};border-bottom:2px solid var(--navy-900)')

def glance_card(label, binding):
    return f"""<div style="border:1px solid var(--rule-200);border-radius:6px;padding:16px 20px">
            <div style="font-family:var(--font-body);font-weight:700;font-size:11px;letter-spacing:0.15em;text-transform:uppercase;color:var(--slate-600)">{label}</div>
            <p style="font-family:var(--font-body);font-size:13.5px;line-height:1.5;color:var(--text-body);margin:8px 0 0;text-wrap:pretty">{{{{ {binding} }}}}</p>
          </div>"""

PAGE2_NEW = f"""<div class="page" data-screen-label="02 The One-Page Read" style="width:794px;min-height:1123px;background:#fff;box-sizing:border-box;box-shadow:0 3px 26px rgba(10,22,69,0.12);display:flex;flex-direction:column">
    {RUNNING_HEADER}
    <div style="padding:28px 60px 20px;flex:1">
      <x-import component-from-global-scope="ThePerformanceLensDesignSystem_4a127a.SectionLabel" hint-size="120px,16px">The One-Page Read</x-import>
      <h2 style="font-family:var(--font-display);font-weight:900;text-transform:uppercase;font-size:34px;color:var(--navy-900);margin:6px 0 22px;line-height:1">Where your team stands</h2>

      <!-- Element 1: personal verdict -->
      <div style="background:var(--navy-900);color:#fff;border-radius:6px;padding:26px 30px">
        <div style="font-family:var(--font-body);font-weight:700;font-size:12px;letter-spacing:0.18em;text-transform:uppercase;color:var(--blue-300)">For {{{{ leaderName }}}}</div>
        <p style="font-family:var(--font-body);font-size:16px;line-height:1.55;color:#fff;margin:12px 0 0;text-wrap:pretty">{{{{ leaderVerdict }}}}</p>
      </div>

      <!-- Element 2: at-a-glance grid -->
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:16px">
          {glance_card("Working well", "workingWell")}
          {glance_card("Needs support", "needsSupport")}
          {glance_card("The risk", "teamRisk")}
          {glance_card("The opportunity", "teamOpportunity")}
      </div>

      <p style="font-family:var(--font-heading);font-weight:600;font-size:15px;color:var(--navy-900);margin:14px 2px 0">{{{{ numberToWatch }}}}</p>

      <!-- Element 4: start-here box -->
      <div style="background:var(--callout);border-left:3px solid var(--blue-500);border-radius:6px;padding:20px 24px;margin-top:16px">
        <div style="font-family:var(--font-body);font-weight:700;font-size:12px;letter-spacing:0.16em;text-transform:uppercase;color:var(--blue-600)">One move to start with</div>
        <p style="font-family:var(--font-body);font-size:15px;line-height:1.55;color:var(--ink-900);margin:11px 0 0;text-wrap:pretty">{{{{ firstMove }}}}</p>
      </div>
    </div>
    {FOOTER.replace("%%PAGE%%", "2")}
  </div>
"""

WIW_ROW = """<sc-raw-tr>
              <sc-raw-td style="padding:11px 12px 11px 0;border-bottom:1px solid var(--rule-200);font-weight:700;font-size:14px;color:var(--navy-900)">{{ m.name }}</sc-raw-td>
              <sc-raw-td style="padding:11px 12px;border-bottom:1px solid var(--rule-200);font-size:13px;color:var(--text-muted)">{{ m.archetype }}</sc-raw-td>
              <sc-raw-td style="{{ m.commStyle }}">{{ m.comm }}</sc-raw-td>
              <sc-raw-td style="{{ m.dmStyle }}">{{ m.dm }}</sc-raw-td>
              <sc-raw-td style="{{ m.collabStyle }}">{{ m.collab }}</sc-raw-td>
              <sc-raw-td style="{{ m.avgStyle }}">{{ m.avg }}</sc-raw-td>
              <sc-raw-td style="padding:11px 0 11px 12px;border-bottom:1px solid var(--rule-200)"><span style="{{ m.flagStyle }}">{{ m.flag }}</span></sc-raw-td>
            </sc-raw-tr>"""

WIW_THEAD = f"""<sc-raw-thead>
          <sc-raw-tr>
            <sc-raw-th style="{TH.format(al='left', pad='0 12px 9px 0')}">Name</sc-raw-th>
            <sc-raw-th style="{TH.format(al='left', pad='0 12px 9px')}">Archetype</sc-raw-th>
            <sc-raw-th style="{TH.format(al='center', pad='0 8px 9px')}">Comm.</sc-raw-th>
            <sc-raw-th style="{TH.format(al='center', pad='0 8px 9px')}">Decision-Making</sc-raw-th>
            <sc-raw-th style="{TH.format(al='center', pad='0 8px 9px')}">Collab.</sc-raw-th>
            <sc-raw-th style="{TH.format(al='center', pad='0 8px 9px')}">Avg</sc-raw-th>
            <sc-raw-th style="{TH.format(al='left', pad='0 0 9px 12px')}">Focus</sc-raw-th>
          </sc-raw-tr>
        </sc-raw-thead>"""

AVG_TD = ('padding:12px 8px;border-top:2px solid var(--navy-900);text-align:center;'
          'font-weight:800;font-size:14px;color:var(--navy-900);font-variant-numeric:tabular-nums')

PAGE3_NEW = f"""<sc-for list="{{{{ wiwPages }}}}" as="wp" hint-placeholder-count="1">
  <div class="page" data-screen-label="03 Who Is Who" style="width:794px;min-height:1123px;background:#fff;box-sizing:border-box;box-shadow:0 3px 26px rgba(10,22,69,0.12);display:flex;flex-direction:column">
    {RUNNING_HEADER}
    <div style="padding:28px 60px 20px;flex:1">
      <x-import component-from-global-scope="ThePerformanceLensDesignSystem_4a127a.SectionLabel" hint-size="120px,16px">Who Is Who</x-import>
      <sc-if value="{{{{ wp.first }}}}" hint-placeholder-val="{{{{ true }}}}">
      <h2 style="font-family:var(--font-display);font-weight:900;text-transform:uppercase;font-size:34px;color:var(--navy-900);margin:6px 0 14px;line-height:1">The team in one view</h2>

      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:0 0 16px">
        <sc-for list="{{{{ cards }}}}" as="card" hint-placeholder-count="3">
          <div style="border:1px solid var(--rule-200);border-radius:6px;padding:12px 16px;display:flex;align-items:center;gap:12px">
            <div style="flex:1;min-width:0">
              <div style="font-family:var(--font-body);font-weight:700;font-size:10px;letter-spacing:0.12em;text-transform:uppercase;color:var(--slate-600);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{{{ card.label }}}}</div>
              <div style="height:5px;border-radius:3px;background:var(--rule-200);margin-top:9px;overflow:hidden"><div style="{{{{ card.barStyle }}}}"></div></div>
            </div>
            <div style="font-family:var(--font-display);font-weight:900;font-size:32px;line-height:1;color:var(--navy-900);font-variant-numeric:tabular-nums">{{{{ card.score }}}}</div>
          </div>
        </sc-for>
      </div>

      <p style="font-family:var(--font-body);font-size:14px;line-height:1.55;color:var(--text-muted);margin:0 0 16px;text-wrap:pretty">{P3_INTRO}</p>

      <sc-if value="{{{{ isSmallTeam }}}}" hint-placeholder-val="{{{{ true }}}}">
        <div style="border-left:3px solid #C77D1A;background:#FBEFD6;padding:12px 18px;border-radius:4px;margin-bottom:16px">
          <p style="font-family:var(--font-body);font-size:13px;line-height:1.5;color:#6E4400;margin:0;text-wrap:pretty"><strong style="color:#8A5200">A note on reading this table:</strong> with a team this size, one person moves the average significantly. Read the individual rows before the averages.</p>
        </div>
      </sc-if>
      </sc-if>
      <sc-if value="{{{{ wp.cont }}}}" hint-placeholder-val="{{{{ false }}}}">
      <h2 style="font-family:var(--font-display);font-weight:900;text-transform:uppercase;font-size:28px;color:var(--navy-900);margin:6px 0 18px;line-height:1">The team in one view · continued</h2>
      </sc-if>

      <sc-raw-table style="width:100%;border-collapse:collapse;font-family:var(--font-body)">
        {WIW_THEAD}
        <sc-raw-tbody>
          <sc-for list="{{{{ wp.rows }}}}" as="m" hint-placeholder-count="3">{WIW_ROW}</sc-for>
          <sc-if value="{{{{ wp.last }}}}" hint-placeholder-val="{{{{ true }}}}">
          <sc-raw-tr>
            <sc-raw-td style="padding:12px 12px 12px 0;border-top:2px solid var(--navy-900);font-family:var(--font-heading);font-weight:700;font-size:13px;letter-spacing:0.08em;text-transform:uppercase;color:var(--navy-900)">Team average</sc-raw-td>
            <sc-raw-td style="padding:12px 12px;border-top:2px solid var(--navy-900)"></sc-raw-td>
            <sc-raw-td style="{AVG_TD}">{{{{ avgComm }}}}</sc-raw-td>
            <sc-raw-td style="{AVG_TD}">{{{{ avgDm }}}}</sc-raw-td>
            <sc-raw-td style="{AVG_TD}">{{{{ avgCollab }}}}</sc-raw-td>
            <sc-raw-td style="{AVG_TD}">{{{{ avgOverall }}}}</sc-raw-td>
            <sc-raw-td style="padding:12px 0;border-top:2px solid var(--navy-900)"></sc-raw-td>
          </sc-raw-tr>
          </sc-if>
        </sc-raw-tbody>
      </sc-raw-table>

      <sc-if value="{{{{ wp.last }}}}" hint-placeholder-val="{{{{ true }}}}">
      <div style="font-size:12px;color:var(--slate-400);margin-top:10px">{P3_LEGEND}</div>

      <div style="display:grid;grid-template-columns:1.15fr 1fr;gap:26px;margin-top:28px;align-items:start">
        <div>
          <div style="font-family:var(--font-body);font-weight:700;font-size:11px;letter-spacing:0.15em;text-transform:uppercase;color:var(--slate-600);margin-bottom:12px">Team composition</div>
          <sc-raw-table style="width:100%;border-collapse:collapse;font-family:var(--font-body)">
            <sc-raw-thead>
              <sc-raw-tr>
                <sc-raw-th style="text-align:left;font-size:10px;letter-spacing:0.1em;text-transform:uppercase;color:var(--slate-600);font-weight:700;padding:0 10px 7px 0;border-bottom:1px solid var(--rule-300)">Archetype</sc-raw-th>
                <sc-raw-th style="text-align:center;font-size:10px;letter-spacing:0.1em;text-transform:uppercase;color:var(--slate-600);font-weight:700;padding:0 10px 7px;border-bottom:1px solid var(--rule-300)">Count</sc-raw-th>
                <sc-raw-th style="text-align:left;font-size:10px;letter-spacing:0.1em;text-transform:uppercase;color:var(--slate-600);font-weight:700;padding:0 0 7px 10px;border-bottom:1px solid var(--rule-300)">Members</sc-raw-th>
              </sc-raw-tr>
            </sc-raw-thead>
            <sc-raw-tbody>
              <sc-for list="{{{{ archetypes }}}}" as="a" hint-placeholder-count="3">
              <sc-raw-tr>
                  <sc-raw-td style="padding:8px 10px 8px 0;border-bottom:1px solid var(--rule-200);font-weight:700;font-size:13px;color:var(--navy-900)">{{{{ a.arch }}}}</sc-raw-td>
                  <sc-raw-td style="padding:8px 10px;border-bottom:1px solid var(--rule-200);text-align:center;font-weight:700;font-size:13px;color:var(--navy-900);font-variant-numeric:tabular-nums">{{{{ a.count }}}}</sc-raw-td>
                  <sc-raw-td style="padding:8px 0 8px 10px;border-bottom:1px solid var(--rule-200);font-size:12px;color:var(--text-muted)">{{{{ a.members }}}}</sc-raw-td>
                </sc-raw-tr>
              </sc-for>
            </sc-raw-tbody>
          </sc-raw-table>
        </div>
        <div style="background:var(--grey-50);border-radius:6px;padding:18px 22px">
          <p style="font-family:var(--font-body);font-size:13px;line-height:1.55;color:var(--text-muted);margin:0;text-wrap:pretty">Each team member has received their own private profile. This report is the team layer: it shows what the collective data says.</p>
        </div>
      </div>
      </sc-if>
    </div>
    {FOOTER.replace("%%PAGE%%", "{{ wp.num }}")}
  </div>
  </sc-for>
"""

GROUP_TH = ('text-align:{al};font-size:10px;letter-spacing:{ls};text-transform:uppercase;'
            'color:var(--slate-600);font-weight:700;padding:{pad};border-bottom:1px solid var(--rule-300)')

def group_table(kind, theme_header):
    return f"""<sc-raw-table style="width:100%;border-collapse:collapse;font-family:var(--font-body);margin-bottom:6px">
          <sc-raw-thead>
            <sc-raw-tr>
              <sc-raw-th style="{GROUP_TH.format(al='left', ls='0.1em', pad='0 10px 8px 0')}">Member</sc-raw-th>
              <sc-raw-th style="{GROUP_TH.format(al='center', ls='0.08em', pad='0 6px 8px')}">Comm.</sc-raw-th>
              <sc-raw-th style="{GROUP_TH.format(al='center', ls='0.08em', pad='0 6px 8px')}">Dec.-Mk.</sc-raw-th>
              <sc-raw-th style="{GROUP_TH.format(al='center', ls='0.08em', pad='0 6px 8px')}">Collab.</sc-raw-th>
              <sc-raw-th style="{GROUP_TH.format(al='left', ls='0.1em', pad='0 0 8px 14px')};width:52%">{theme_header}</sc-raw-th>
            </sc-raw-tr>
          </sc-raw-thead>
          <sc-raw-tbody>
            <sc-for list="{{{{ b.rows }}}}" as="m" hint-placeholder-count="2">
            <sc-raw-tr>
                <sc-raw-td style="padding:13px 10px 13px 0;border-bottom:1px solid var(--rule-200);vertical-align:top">
                  <div style="font-weight:700;font-size:14px;color:var(--navy-900)">{{{{ m.name }}}}</div>
                  <div style="font-size:12px;color:var(--text-muted);margin-top:2px">{{{{ m.archetype }}}}</div>
                </sc-raw-td>
                <sc-raw-td style="{{{{ m.commStyleTop }}}}">{{{{ m.comm }}}}</sc-raw-td>
                <sc-raw-td style="{{{{ m.dmStyleTop }}}}">{{{{ m.dm }}}}</sc-raw-td>
                <sc-raw-td style="{{{{ m.collabStyleTop }}}}">{{{{ m.collab }}}}</sc-raw-td>
                <sc-raw-td style="padding:13px 0 13px 14px;border-bottom:1px solid var(--rule-200);font-size:13px;line-height:1.5;color:var(--text-body);vertical-align:top;text-wrap:pretty">{{{{ m.theme }}}}</sc-raw-td>
              </sc-raw-tr>
            </sc-for>
          </sc-raw-tbody>
        </sc-raw-table>"""

PAGE5_NEW = f"""<sc-for list="{{{{ p5Pages }}}}" as="pg" hint-placeholder-count="1">
  <div class="page" data-screen-label="05 Who to Focus On" style="width:794px;min-height:1123px;background:#fff;box-sizing:border-box;box-shadow:0 3px 26px rgba(10,22,69,0.12);display:flex;flex-direction:column">
    {RUNNING_HEADER}
    <div style="padding:28px 60px 20px;flex:1">
      <x-import component-from-global-scope="ThePerformanceLensDesignSystem_4a127a.SectionLabel" hint-size="120px,16px">Who to Focus On</x-import>
      <sc-if value="{{{{ pg.first }}}}" hint-placeholder-val="{{{{ true }}}}">
      <h2 style="font-family:var(--font-display);font-weight:900;text-transform:uppercase;font-size:34px;color:var(--navy-900);margin:6px 0 14px;line-height:1">Two groups this quarter</h2>
      <p style="font-family:var(--font-body);font-size:14px;line-height:1.55;color:var(--text-muted);margin:0 0 20px;text-wrap:pretty">{P5_INTRO}</p>
      </sc-if>
      <sc-if value="{{{{ pg.cont }}}}" hint-placeholder-val="{{{{ false }}}}">
      <h2 style="font-family:var(--font-display);font-weight:900;text-transform:uppercase;font-size:28px;color:var(--navy-900);margin:6px 0 18px;line-height:1">Two groups this quarter · continued</h2>
      </sc-if>

      <sc-for list="{{{{ pg.blocks }}}}" as="b" hint-placeholder-count="4">

        <sc-if value="{{{{ b.ciHeader }}}}" hint-placeholder-val="{{{{ true }}}}">
        <div style="display:flex;align-items:baseline;gap:10px;margin:14px 0 10px">
          <span style="font-family:var(--font-body);font-weight:700;font-size:12px;letter-spacing:0.16em;text-transform:uppercase;color:#8A5200;white-space:nowrap">Check-In · {{{{ checkInCount }}}} of {{{{ teamSize }}}}</span>
          <span style="font-family:var(--font-body);font-size:11.5px;color:var(--text-muted);white-space:nowrap">{CI_CAPTION}</span>
          <span style="height:1px;flex:1;background:var(--rule-200);align-self:center"></span>
        </div>
        </sc-if>

        <sc-if value="{{{{ b.stHeader }}}}" hint-placeholder-val="{{{{ false }}}}">
        <div style="display:flex;align-items:baseline;gap:10px;margin:22px 0 10px">
          <span style="font-family:var(--font-body);font-weight:700;font-size:12px;letter-spacing:0.16em;text-transform:uppercase;color:var(--blue-600);white-space:nowrap">Stretch · {{{{ stretchCount }}}} of {{{{ teamSize }}}}</span>
          <span style="font-family:var(--font-body);font-size:11.5px;color:var(--text-muted);white-space:nowrap">{ST_CAPTION}</span>
          <span style="height:1px;flex:1;background:var(--rule-200);align-self:center"></span>
        </div>
        </sc-if>

        <sc-if value="{{{{ b.ciTable }}}}" hint-placeholder-val="{{{{ true }}}}">
        {group_table("ci", "What the data shows, and the theme for a 1:1")}
        </sc-if>

        <sc-if value="{{{{ b.stTable }}}}" hint-placeholder-val="{{{{ false }}}}">
        {group_table("st", "Where they are strong, and one way to stretch them")}
        </sc-if>

        <sc-if value="{{{{ b.ciFallback }}}}" hint-placeholder-val="{{{{ false }}}}">
        <div style="background:var(--grey-50);border-radius:6px;padding:18px 22px">
          <p style="font-family:var(--font-body);font-size:14px;line-height:1.55;color:var(--text-body);margin:0;text-wrap:pretty">{{{{ checkInFallback }}}}</p>
        </div>
        </sc-if>

        <sc-if value="{{{{ b.stFallback }}}}" hint-placeholder-val="{{{{ false }}}}">
        <div style="background:var(--grey-50);border-radius:6px;padding:18px 22px">
          <p style="font-family:var(--font-body);font-size:14px;line-height:1.55;color:var(--text-body);margin:0;text-wrap:pretty">{{{{ stretchFallback }}}}</p>
        </div>
        </sc-if>

        <sc-if value="{{{{ b.caveat }}}}" hint-placeholder-val="{{{{ true }}}}">
        <div style="border-left:3px solid var(--rule-300);padding:4px 0 4px 18px;margin-top:24px">
          <p style="font-family:var(--font-body);font-size:13px;line-height:1.55;color:var(--text-muted);margin:0;text-wrap:pretty">These scores are a snapshot of behaviour under structured pressure, one data point. Use them to open conversations.</p>
        </div>
        </sc-if>

      </sc-for>
    </div>
    {FOOTER.replace("%%PAGE%%", "{{ pg.num }}")}
  </div>
  </sc-for>
"""

APPENDIX_BLOCK = f"""<div style="margin-top:30px">
        <h3 style="font-family:var(--font-heading);font-weight:700;font-size:16px;color:var(--navy-900);margin:0 0 14px">Focus groups</h3>
        <p style="font-family:var(--font-body);font-size:13.5px;line-height:1.55;color:var(--text-body);margin:0;text-wrap:pretty">{APPENDIX_FOCUS}</p>
      </div>

      """

# ---------------------------------------------------------------------------
# renderVals v2 compute block (replaces everything from `const avgStyleStr`
# through the end of the return object). Written against the payload contract
# as amended by Change Order 1.
RENDERVALS_V2 = r"""
    const avgStyleStr = 'padding:11px 8px;text-align:center;font-variant-numeric:tabular-nums;font-size:14px;font-weight:800;color:var(--navy-900);border-bottom:1px solid var(--rule-200);';
    const members = cfg.members.map(m => ({
      ...m,
      commStyle: this.cell(m.comm, false), dmStyle: this.cell(m.dm, false), collabStyle: this.cell(m.collab, false),
      commStyleTop: this.cell(m.comm, true), dmStyleTop: this.cell(m.dm, true), collabStyleTop: this.cell(m.collab, true),
      avgStyle: avgStyleStr,
      flagStyle: m.flag === 'Steady' ? 'display:none' : this.flagStyle(m.flag),
    }));
    const checkInMembers = members.filter(m => m.flag === 'Check-In').map(m => ({ ...m, theme: m.focusTheme }));
    const stretchMembers = members.filter(m => m.flag === 'Stretch').map(m => ({ ...m, theme: m.stretchTheme }));

    const order = []; const amap = {};
    cfg.members.forEach(m => { if (!amap[m.archetype]) { amap[m.archetype] = []; order.push(m.archetype); } amap[m.archetype].push(m.name); });
    const archetypes = order.map(a => ({ arch: a, count: amap[a].length, members: amap[a].join(', ') }));

    const cards = cfg.cards.map(c => ({ ...c, barStyle: this.bar(c.score) }));
    const hasMissing = Array.isArray(cfg.missingCards) && cfg.missingCards.length > 0;
    const splitPage4 = cfg.patternCards.length >= 4 && hasMissing;
    const inlineMissingFlag = cfg.patternCards.length < 4 && hasMissing;
    const patternGridCols = cfg.patternCards.length <= 3 ? ('repeat(' + cfg.patternCards.length + ',1fr)') : '1fr 1fr';

    const bands = [
      { band: 'Strong', range: '80–100', desc: 'Demonstrable strength under pressure.', dotStyle: 'width:11px;height:11px;border-radius:50%;background:var(--scale-strong);flex:none' },
      { band: 'Developing', range: '60–79', desc: 'Working capability, above threshold, with room to grow.', dotStyle: 'width:11px;height:11px;border-radius:50%;background:var(--scale-developing);flex:none' },
      { band: 'Emerging', range: '40–59', desc: 'A development priority. Targeted focus here moves the needle quickly.', dotStyle: 'width:11px;height:11px;border-radius:50%;background:var(--scale-emerging);flex:none' },
      { band: 'Foundation', range: '0–39', desc: 'Foundational stage. Structured attention recommended.', dotStyle: 'width:11px;height:11px;border-radius:50%;background:var(--scale-foundation);flex:none' },
    ];

    // ---- Who Is Who pagination (Change Order 1 §6.2) --------------------
    const n = members.length;
    const wiwChunks = [];
    if (n <= 8) { wiwChunks.push(members.slice()); }
    else if (n <= 12) {
      // 9-12 members: one page would also carry the legend and overflow A4
      // (first live 10-member cohort, BritCham Jul 2026). Split balanced so
      // the legend page holds at most 6 rows.
      const first = Math.ceil(n / 2);
      wiwChunks.push(members.slice(0, first));
      wiwChunks.push(members.slice(first));
    }
    else {
      const rest = members.slice();
      wiwChunks.push(rest.splice(0, 12));
      while (rest.length > 10) { wiwChunks.push(rest.splice(0, Math.min(20, rest.length - 8))); }
      if (rest.length) wiwChunks.push(rest);
    }

    // ---- Page 5 pagination ------------------------------------------------
    // Pixel budget per page (content region below the section label; the
    // first page also carries the h2 + locked intro). Costs are conservative
    // estimates per block; the endpoint's A4 fit check backstops them.
    const themeShort = !!cfg.themeShort;
    const ROW = themeShort ? 68 : 90;      // themed table row
    const HEADER = 52, THEAD = 36, FALLBACK = 90, CAVEAT = 80;
    const CAP_FIRST = 780, CAP_CONT = 880;
    const p5Raw = [];
    let cur = { blocks: [], used: 0, cap: CAP_FIRST };
    const newPage = () => { p5Raw.push(cur); cur = { blocks: [], used: 0, cap: CAP_CONT }; };
    const ensure = (cost) => { if (cur.used + cost > cur.cap && cur.blocks.length) newPage(); };
    const pushHeader = (kind) => { ensure(HEADER + THEAD + ROW); cur.blocks.push({ [kind + 'Header']: true }); cur.used += HEADER; };
    const pushRows = (kind, rows) => {
      let i = 0;
      while (i < rows.length) {
        if (cur.used + THEAD + ROW > cur.cap) newPage();
        const avail = Math.max(1, Math.floor((cur.cap - cur.used - THEAD) / ROW));
        const take = rows.slice(i, i + avail);
        cur.blocks.push({ [kind + 'Table']: true, rows: take });
        cur.used += THEAD + take.length * ROW;
        i += take.length;
      }
    };
    const pushFallback = (kind) => { ensure(FALLBACK); cur.blocks.push({ [kind + 'Fallback']: true }); cur.used += FALLBACK; };
    pushHeader('ci');
    if (checkInMembers.length) pushRows('ci', checkInMembers); else pushFallback('ci');
    pushHeader('st');
    if (stretchMembers.length) pushRows('st', stretchMembers); else pushFallback('st');
    if (cur.used + CAVEAT > cur.cap) newPage();
    cur.blocks.push({ caveat: true }); cur.used += CAVEAT;
    p5Raw.push(cur);

    // ---- Page numbering ---------------------------------------------------
    const wiwStart = 3;
    const pg4Num = wiwStart + wiwChunks.length;
    const pg4bNum = pg4Num + 1;
    const p5Start = pg4Num + 1 + (splitPage4 ? 1 : 0);
    const pg6Num = p5Start + p5Raw.length;
    const pg7Num = pg6Num + 1;
    const pg8Num = pg7Num + 1;
    const totalPages = pg8Num;

    const wiwPages = wiwChunks.map((rows, i) => ({
      rows, first: i === 0, cont: i > 0, last: i === wiwChunks.length - 1, num: wiwStart + i,
    }));
    const p5Pages = p5Raw.map((p, i) => ({
      blocks: p.blocks, first: i === 0, cont: i > 0, num: p5Start + i,
    }));

    return {
      team: cfg.team, date: cfg.date, leaderName: cfg.leaderName,
      leaderVerdict: cfg.leaderVerdict,
      workingWell: cfg.workingWell, needsSupport: cfg.needsSupport,
      teamRisk: cfg.teamRisk, teamOpportunity: cfg.teamOpportunity,
      cards, priorityDim: cfg.priorityDim, priorityScore: cfg.priorityScore, firstMove: cfg.firstMove,
      members, avgComm: cfg.avgComm, avgDm: cfg.avgDm, avgCollab: cfg.avgCollab, avgOverall: cfg.avgOverall,
      isSmallTeam: cfg.members.length <= 5,
      archetypes,
      patternLabel: cfg.patternLabel, patternTitle: cfg.patternTitle, definingPatternP1: cfg.definingPatternP1, definingPatternP2: cfg.definingPatternP2,
      patternCards: cfg.patternCards, missingCards: cfg.missingCards,
      splitPage4, inlineMissing: inlineMissingFlag, patternGridCols,
      checkInMembers, stretchMembers,
      checkInCount: checkInMembers.length, stretchCount: stretchMembers.length, teamSize: members.length,
      hasCheckIn: checkInMembers.length > 0, noCheckIn: checkInMembers.length === 0,
      hasStretch: stretchMembers.length > 0, noStretch: stretchMembers.length === 0,
      stretchFallback: checkInMembers.length === members.length ? __FB_ST_ALL__ : __FB_ST_SHORT__,
      checkInFallback: stretchMembers.length === members.length ? __FB_CI_ALL__ : __FB_CI_SHORT__,
      numberToWatch: cfg.priorityScore <= 59
        ? 'The number to watch: ' + cfg.priorityDim + ', ' + cfg.priorityScore + ' now, above 60 at re-assessment.'
        : 'The number to watch: ' + cfg.priorityDim + ', ' + cfg.priorityScore + ' now, the dimension with the most room at re-assessment.',
      risks: cfg.risks, prescription: cfg.prescription, closingVerdict: cfg.closingVerdict,
      bands,
      wiwPages, p5Pages, totalPages, pg4Num, pg4bNum, pg6Num, pg7Num, pg8Num,
    };
  }
"""

def page_bounds(tpl):
    """(start, end, label) for each top-level .page div, end = start of next page marker or known tail."""
    marks = [(m.start(), re.search(r'data-screen-label="([^"]+)"', tpl[m.start():m.start()+200]).group(1))
             for m in re.finditer(r'<div class="page"', tpl)]
    return marks

def replace_span(tpl, start, end, new):
    return tpl[:start] + new + tpl[end:]

def main():
    s = open(SRC).read()
    m = re.search(r'(<script type="__bundler/template">\s*)(".*")(\s*</script>)', s, re.S)
    assert m, "template script not found"
    tpl = json.loads(m.group(2))

    marks = page_bounds(tpl)
    idx = {label: pos for pos, label in marks}
    order = [label for _, label in marks]
    assert order == ["01 Cover", "02 The One-Page Read", "03 Who Is Who",
                     "04 How This Team Works Together",
                     "04 How This Team Works Together (continued)",
                     "05 Who to Focus On", "06 Action Plan",
                     "07 What to Expect Next", "08 Appendix"], order

    # ---- replace PAGE 5 (do later pages first so earlier offsets survive) --
    p5s, p6s = idx["05 Who to Focus On"], idx["06 Action Plan"]
    # keep the page-6 comment line between them if present
    seg = tpl[p5s:p6s]
    tail = seg[seg.rfind("<!--"):] if "<!--" in seg else ""
    tpl = replace_span(tpl, p5s, p6s, PAGE5_NEW + "\n  " + tail)

    # ---- replace PAGE 3 -----------------------------------------------------
    p3s, p4s = idx["03 Who Is Who"], idx["04 How This Team Works Together"]
    seg = tpl[p3s:p4s]
    tail = seg[seg.rfind("<!--"):] if "<!--" in seg else ""
    tpl = replace_span(tpl, p3s, p4s, PAGE3_NEW + "\n  " + tail)

    # ---- replace PAGE 2 -----------------------------------------------------
    p2s, p3s2 = idx["02 The One-Page Read"], idx["03 Who Is Who"]
    seg = tpl[p2s:p3s2]
    tail = seg[seg.rfind("<!--"):] if "<!--" in seg else ""
    tpl = replace_span(tpl, p2s, p3s2, PAGE2_NEW + "\n  " + tail)

    tpl = tpl.replace("%%TOTAL%%", "{{ totalPages }}")
    assert "%%PAGE%%" not in tpl

    # ---- page 7 label -------------------------------------------------------
    assert tpl.count("Targeted · Half-Day") == 1
    tpl = tpl.replace("Targeted · Half-Day", "Targeted · 90 Minutes")

    # ---- appendix Focus groups block ---------------------------------------
    anchor = '<div style="margin-top:34px;border-top:1px solid var(--rule-200);padding-top:16px">'
    assert tpl.count(anchor) == 1
    tpl = tpl.replace(anchor, APPENDIX_BLOCK + anchor)

    # ---- dynamic page numbers on remaining static pages ---------------------
    for old, new in [("Page 4 of 8", "Page {{ pg4Num }} of {{ totalPages }}"),
                     ("Page 4 · continued", "Page {{ pg4bNum }} of {{ totalPages }}"),
                     ("Page 6 of 8", "Page {{ pg6Num }} of {{ totalPages }}"),
                     ("Page 7 of 8", "Page {{ pg7Num }} of {{ totalPages }}"),
                     ("Page 8 of 8", "Page {{ pg8Num }} of {{ totalPages }}")]:
        assert tpl.count(old) == 1, (old, tpl.count(old))
        tpl = tpl.replace(old, new)
    # page 2/3/5 numbers are inside the authored markup already
    leftovers = re.findall(r"Page \d+ of 8", tpl)
    assert not leftovers, leftovers

    # ---- x-dc script surgery ------------------------------------------------
    # Guard 5: payload replaces the sample switch
    i = tpl.find("const D = {")
    j = tpl.find("const cfg = D[key];")
    assert i > 0 and j > i, "sample dataset block not found"
    j_end = j + len("const cfg = D[key];")
    tpl = (tpl[:i]
           + "const cfg = window.__LIR_PAYLOAD__;\n"
             "    if (!cfg || !Array.isArray(cfg.members)) { throw new Error('LIR payload missing or invalid'); }"
           + tpl[j_end:])
    tpl = re.sub(r'(data-props=")[^"]*(")', r'\1{}\2', tpl, count=1)

    # Replace the whole compute block + return with the v2 version
    i = tpl.find("const avgStyleStr")
    assert i > 0
    # end: the closing of renderVals: find "return {" then its matching "};\n  }" tail
    k = tpl.find("return {", i)
    assert k > 0
    k_end = tpl.find("};", tpl.find("bands,", k))
    assert k_end > 0
    # renderVals ends with "  }" after return; consume through the function close
    fn_close = tpl.find("}", k_end + 2)
    assert fn_close > 0
    body = (RENDERVALS_V2
            .replace("__FB_ST_ALL__", json.dumps(FALLBACK_STRETCH_ALL))
            .replace("__FB_ST_SHORT__", json.dumps(FALLBACK_STRETCH_SHORT))
            .replace("__FB_CI_ALL__", json.dumps(FALLBACK_CHECKIN_ALL))
            .replace("__FB_CI_SHORT__", json.dumps(FALLBACK_CHECKIN_SHORT)))
    tpl = tpl[:i] + body.strip() + "\n" + tpl[fn_close + 1:]

    # ---- payload hook + vendored React BEFORE the dc runtime ----------------
    react = open("vendor_react.js").read()
    react_dom = open("vendor_react_dom.js").read()
    pre = ("<script>window.__LIR_PAYLOAD__ = __LIR_PAYLOAD_JSON__;</script>\n"
           "<script>/* vendored react@18.3.1 */\n" + react + "\n</script>\n"
           "<script>/* vendored react-dom@18.3.1 */\n" + react_dom + "\n</script>\n")
    k = tpl.find('<script src="ad3137fb-6bfc-4585-8010-0ccf27d9d8af">')
    assert k > 0, "dc runtime script tag not found"
    tpl = tpl[:k] + pre + tpl[k:]

    # ---- sanity: no v1 leftovers -------------------------------------------
    for gone in ["{{ headline }}", "{{ priorityRead }}", "Priority — "]:
        assert gone not in tpl, gone
    for there in ["{{ workingWell }}", "{{ needsSupport }}", "{{ teamRisk }}",
                  "{{ teamOpportunity }}", "wiwPages", "p5Pages", "{{ totalPages }}",
                  "Targeted · 90 Minutes", "Focus groups"]:
        assert there in tpl, there

    encoded = json.dumps(tpl).replace("</", "<\\u002F")
    out = s[:m.start(2)] + encoded + s[m.end(2):]
    open(OUT, "w").write(out)
    print("wrote", OUT, len(out), "chars; token present:", "__LIR_PAYLOAD_JSON__" in out)

if __name__ == "__main__":
    main()
