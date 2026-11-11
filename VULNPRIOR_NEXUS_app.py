from __future__ import annotations

from datetime import datetime
from io import BytesIO
import html
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.pipeline import run_risk_assessment
from src.data_loader import load_profiles
from src.repository_scanner import scan_dependency_upload

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"

st.set_page_config(
    page_title="VULNPRIOR NEXUS | Cyber Risk Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Brand system: Obsidian + electric cyan + ultraviolet ---
CUSTOM_CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
:root { --cyan:#4DEBFF; --purple:#A78BFA; --ink:#080B14; --panel:#101522; --panel2:#141B2B; --muted:#8F9BB3; --line:rgba(151,169,207,.16); }
html, body, [class*="css"] { font-family:'Manrope',Inter,system-ui,sans-serif; }
.stApp { background: radial-gradient(ellipse at 8% 0%, rgba(25,151,194,.12), transparent 34%), radial-gradient(ellipse at 92% 10%, rgba(125,78,220,.14), transparent 30%), #080B14; color:#F4F7FF; }
[data-testid="stHeader"] { background:rgba(8,11,20,.72); }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#0C1220 0%,#0A0E18 100%); border-right:1px solid var(--line); }
[data-testid="stSidebar"] > div { padding-top:1.4rem; }
.block-container { padding-top:1.7rem; padding-bottom:3rem; max-width:1500px; }
#MainMenu, footer { visibility:hidden; }
[data-testid="stToolbar"] { right:1rem; }
.brand { display:flex; align-items:center; gap:13px; margin-bottom:7px; }
.brand-mark { width:46px;height:46px;display:grid;place-items:center;border-radius:15px;color:#061018;font-size:24px;font-weight:900;background:linear-gradient(135deg,var(--cyan),var(--purple));box-shadow:0 0 28px rgba(77,235,255,.16); }
.brand-name { font-size:1.2rem;letter-spacing:.16em;font-weight:800;color:#F4F7FF; }
.brand-sub { color:#8F9BB3;font-size:.69rem;letter-spacing:.17em;text-transform:uppercase;margin-top:3px; }
.eyebrow { color:var(--cyan);font:500 .73rem 'DM Mono',monospace;letter-spacing:.19em;text-transform:uppercase;margin:0 0 8px 0; }
.hero-title { font-size:clamp(2rem,4vw,3.25rem);line-height:1.05;letter-spacing:-.055em;font-weight:800;margin:0;color:#F5F7FF; }
.hero-title span { background:linear-gradient(95deg,var(--cyan),#9ADFFF 42%,var(--purple));-webkit-background-clip:text;background-clip:text;color:transparent; }
.hero-copy { color:#9CA8BE;max-width:780px;line-height:1.7;margin-top:13px;font-size:.96rem; }
.status-pill { display:inline-flex;align-items:center;gap:8px;border:1px solid rgba(77,235,255,.23);border-radius:999px;padding:7px 11px;color:#A5F5FF;background:rgba(77,235,255,.055);font:500 .7rem 'DM Mono',monospace;letter-spacing:.08em; }
.status-dot { width:7px;height:7px;border-radius:50%;background:#4DEBFF;box-shadow:0 0 12px #4DEBFF; }
.section-kicker { color:#9BA7BE;font:500 .72rem 'DM Mono',monospace;letter-spacing:.16em;text-transform:uppercase;margin:1.1rem 0 .7rem; }
.metric-card { background:linear-gradient(145deg,rgba(21,29,46,.96),rgba(13,18,30,.96));border:1px solid var(--line);border-radius:18px;padding:18px 19px 16px;min-height:126px;position:relative;overflow:hidden; }
.metric-card:after { content:'';position:absolute;top:-34px;right:-28px;width:100px;height:100px;border-radius:50%;background:var(--glow,rgba(77,235,255,.08));filter:blur(5px); }
.metric-label { color:#9AA7BE;font-size:.76rem;font-weight:600;letter-spacing:.06em;text-transform:uppercase; }
.metric-value { color:#F4F7FF;font-size:2rem;font-weight:800;letter-spacing:-.05em;margin-top:9px;line-height:1.1; }
.metric-note { color:#75829B;font-size:.72rem;margin-top:8px; }
.panel { background:linear-gradient(145deg,rgba(17,23,38,.94),rgba(12,17,29,.96));border:1px solid var(--line);border-radius:20px;padding:19px 21px; }
.panel-title { font-size:1rem;font-weight:800;color:#F0F4FF;margin:0 0 4px; }
.panel-sub { color:#8794AC;font-size:.78rem;line-height:1.5;margin-bottom:15px; }
.tag { display:inline-block;padding:4px 8px;border-radius:7px;font:500 .68rem 'DM Mono',monospace;letter-spacing:.04em; }
.tag-cyan { color:#8BF5FF;background:rgba(77,235,255,.09);border:1px solid rgba(77,235,255,.19); }
.tag-purple { color:#C9B7FF;background:rgba(167,139,250,.10);border:1px solid rgba(167,139,250,.22); }
.tag-red { color:#FF9DAA;background:rgba(255,95,117,.10);border:1px solid rgba(255,95,117,.2); }
.finding { background:rgba(16,22,36,.82);border:1px solid var(--line);border-radius:14px;padding:15px 16px;margin:8px 0; }
.finding:hover { border-color:rgba(77,235,255,.4); }
.finding-id { font:500 .78rem 'DM Mono',monospace;color:#72EFFF; }
.finding-title { font-weight:750;color:#F2F5FF;margin:5px 0 9px; }
.finding-meta { color:#9BA7BD;font-size:.78rem;line-height:1.65; }
.sidebar-label { color:#74829B;font:500 .68rem 'DM Mono',monospace;letter-spacing:.16em;text-transform:uppercase; }
div.stButton > button { border-radius:11px;border:1px solid rgba(77,235,255,.35);background:linear-gradient(110deg,rgba(77,235,255,.13),rgba(167,139,250,.13));color:#EAFBFF;font-weight:750;transition:all .18s ease; }
div.stButton > button:hover { border-color:var(--cyan);box-shadow:0 0 22px rgba(77,235,255,.12);color:white; }
button[kind="primary"] { background:linear-gradient(100deg,#36CFE8,#8B72F3)!important;color:#07101A!important;border:0!important; }
.stTabs [data-baseweb="tab-list"] { gap:8px;border-bottom:1px solid var(--line); }
.stTabs [data-baseweb="tab"] { background:transparent;border-radius:10px 10px 0 0;color:#8E9AB1;padding:12px 17px;font-weight:700; }
.stTabs [aria-selected="true"] { color:#B8F8FF!important;border-bottom:2px solid var(--cyan)!important;background:rgba(77,235,255,.045)!important; }
[data-testid="stDataFrame"] { border:1px solid var(--line);border-radius:13px;overflow:hidden; }
[data-testid="stExpander"] { background:rgba(15,21,35,.8);border:1px solid var(--line);border-radius:12px; }
.stAlert { border-radius:12px; }
hr { border-color:var(--line)!important; }
small, .muted { color:#8F9BB3; }
@media (max-width:760px) { .block-container{padding-left:1rem;padding-right:1rem}.metric-value{font-size:1.55rem}.brand-name{font-size:1rem}.panel{padding:15px} }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Manrope, sans-serif", color="#AEB9CE", size=11),
    margin=dict(l=8, r=8, t=12, b=8),
    xaxis=dict(gridcolor="rgba(151,169,207,.10)", zerolinecolor="rgba(151,169,207,.10)"),
    yaxis=dict(gridcolor="rgba(151,169,207,.10)", zerolinecolor="rgba(151,169,207,.10)"),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#AEB9CE")),
)

@st.cache_data(show_spinner=False)
def get_orgs():
    return load_profiles(str(DATA_DIR / "profiles.json")).get("organizations", [])

def get_available_orgs():
    """Backward-compatible name used by the original project tests."""
    return get_orgs()


@st.cache_data(show_spinner=False)
def run_profile_assessment(org_id: str):
    return run_risk_assessment(org_id, top_k=1000, vuln_path=str(DATA_DIR / "vulnerabilities.csv"),
                               prof_path=str(DATA_DIR / "profiles.json"), gold_path=str(DATA_DIR / "gold_set.csv"))


def metric_card(label, value, note, glow="rgba(77,235,255,.08)"):
    st.markdown(f"<div class='metric-card' style='--glow:{glow}'><div class='metric-label'>{label}</div><div class='metric-value'>{value}</div><div class='metric-note'>{note}</div></div>", unsafe_allow_html=True)


def section(title, subtitle=None):
    st.markdown(f"<div class='section-kicker'>{title}</div>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<div class='panel-sub'>{subtitle}</div>", unsafe_allow_html=True)


def risk_color(score):
    if score >= 80: return "#FF647C"
    if score >= 60: return "#FFB86B"
    if score >= 35: return "#C5A7FF"
    return "#4DEBFF"


def build_pdf(org_name, scan_result, profile_result):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
    buff = BytesIO()
    doc = SimpleDocTemplate(buff, pagesize=A4, rightMargin=16*mm, leftMargin=16*mm, topMargin=15*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="NexusTitle", parent=styles["Title"], textColor=colors.HexColor("#18243A"), fontSize=23, leading=28, spaceAfter=6))
    styles.add(ParagraphStyle(name="NexusHeading", parent=styles["Heading2"], textColor=colors.HexColor("#087E91"), spaceBefore=12, spaceAfter=6))
    styles.add(ParagraphStyle(name="NexusBody", parent=styles["BodyText"], leading=14, spaceAfter=5))
    story = [Paragraph("VULNPRIOR NEXUS", styles["NexusTitle"]), Paragraph("Cyber Risk Intelligence | Security Assessment Report", styles["NexusBody"]),
             Paragraph(f"Generated: {datetime.now().strftime('%d %b %Y, %H:%M')}", styles["BodyText"]), Spacer(1, 8)]
    if profile_result:
        meta = profile_result["metadata"]
        org = profile_result["organisation"]
        story += [Paragraph("Organisation-aware risk assessment", styles["NexusHeading"]),
                  Paragraph(f"Organisation: {html.escape(org['organisation_name'])} | Sector: {html.escape(org.get('sector',''))}", styles["NexusBody"]),
                  Paragraph(f"Unique CVEs evaluated: {meta['total_unique_cves_after_filtering']} | Critical products: {len(org['critical_products'])}", styles["NexusBody"])]
        rows = [["Rank", "CVE", "Product", "Risk", "CVSS", "CISA KEV"]]
        for v in profile_result["top_vulnerabilities"][:25]:
            rows.append([str(v["rank"]), v["cve_id"], str(v["representative_product"])[:30], f"{v['risk_score']:.1f}", str(v["cvss_base_score"]), "Yes" if v["cisa_kev"] else "No"])
        table = Table(rows, repeatRows=1, colWidths=[12*mm, 32*mm, 55*mm, 17*mm, 16*mm, 22*mm])
        table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#111A2B")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),7.5),("GRID",(0,0),(-1,-1),.35,colors.HexColor("#D8DFEA")),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#F3F6FA")]),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)]))
        story += [table, Spacer(1, 8)]
    if scan_result:
        story += [Paragraph("Repository dependency scan", styles["NexusHeading"]),
                  Paragraph(f"Status: {html.escape(scan_result.get('status','unknown'))} | Manifests: {html.escape(', '.join(scan_result.get('manifests', [])))} | Exact-version dependencies: {len(scan_result.get('packages', []))}", styles["NexusBody"]),
                  Paragraph(f"Known vulnerability matches: {len(scan_result.get('findings', []))}", styles["NexusBody"])]
        rows = [["Package", "Version", "Vulnerability", "Summary"]]
        for finding in scan_result.get("findings", [])[:35]:
            rows.append([finding["package"], finding["version"], finding["cve_id"], str(finding["summary"])[:100]])
        if len(rows) == 1:
            rows.append(["No matches returned", "-", "-", "This does not prove the repository is vulnerability-free."])
        table = Table(rows, repeatRows=1, colWidths=[28*mm, 20*mm, 33*mm, 73*mm])
        table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#111A2B")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),7),("GRID",(0,0),(-1,-1),.35,colors.HexColor("#D8DFEA")),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#F3F6FA")]),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)]))
        story.append(table)
        if scan_result.get("warnings") or scan_result.get("skipped"):
            story += [Paragraph("Coverage notes", styles["NexusHeading"])]
            for note in (scan_result.get("warnings", []) + scan_result.get("skipped", []))[:12]:
                story.append(Paragraph("• " + html.escape(str(note)), styles["NexusBody"]))
    story += [Spacer(1, 12), Paragraph("Method note: Risk scores are prioritization aids, not proof of exploitability. Repository checks inspect supported dependency manifests and query OSV for exact versions. Review results and validate fixes in a test environment.", styles["NexusBody"])]
    doc.build(story)
    return buff.getvalue()

# --- Sidebar ---
orgs = get_orgs()
if not orgs:
    st.error("Organisation profiles could not be loaded. Check data/profiles.json.")
    st.stop()
org_map = {f"{o['name']}": o for o in orgs}

with st.sidebar:
    st.markdown("<div class='brand'><div class='brand-mark'>⌁</div><div><div class='brand-name'>VULNPRIOR</div><div class='brand-sub'>Nexus · Risk Intelligence</div></div></div>", unsafe_allow_html=True)
    st.markdown("<br><div class='sidebar-label'>WORKSPACE</div>", unsafe_allow_html=True)
    selected_name = st.selectbox("Organisation profile", list(org_map.keys()), label_visibility="collapsed")
    selected_org = org_map[selected_name]
    st.markdown(f"<div class='panel' style='padding:14px;margin-top:10px'><div class='sidebar-label'>ACTIVE PROFILE</div><div style='font-weight:800;margin:8px 0 4px'>{html.escape(selected_org['name'])}</div><div style='color:#9BA7BE;font-size:.8rem'>{html.escape(selected_org['sector'])}</div><div style='margin-top:10px'><span class='tag tag-purple'>{html.escape(selected_org['risk_appetite'])} RISK APPETITE</span></div><div style='color:#9BA7BE;font-size:.75rem;margin-top:12px'>Critical products<br><b style='color:#EAF0FF'>{len(selected_org.get('critical_products', []))} monitored assets</b></div></div>", unsafe_allow_html=True)
    st.markdown("<br><div class='sidebar-label'>SCORING MODEL</div>", unsafe_allow_html=True)
    weights = selected_org.get("weight_modifiers", {})
    for label, key, color in [("CVSS impact", "cvss_weight", "#4DEBFF"), ("CISA KEV", "cisa_kev_weight", "#A78BFA"), ("EPSS probability", "first_epss_weight", "#F5A9FF")]:
        pct = int(float(weights.get(key, 0)) * 100)
        st.markdown(f"<div style='display:flex;justify-content:space-between;color:#9BA7BE;font-size:.75rem;margin-top:12px'><span>{label}</span><b style='color:{color}'>{pct}%</b></div><div style='height:5px;background:#20283A;border-radius:8px;margin-top:6px'><div style='height:5px;width:{pct}%;background:{color};border-radius:8px'></div></div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    refresh = st.button("↻  Run risk assessment", type="primary", use_container_width=True)
    st.markdown("<div style='color:#66738C;font-size:.7rem;line-height:1.6;margin-top:13px'>LOCAL DATASET MODE<br>Repository scans query OSV when internet access is available.</div>", unsafe_allow_html=True)

if refresh or "profile_result" not in st.session_state or st.session_state.get("active_org") != selected_org["org_id"]:
    with st.spinner("Correlating CVSS, KEV and EPSS signals..."):
        try:
            st.session_state["profile_result"] = run_profile_assessment(selected_org["org_id"])
            st.session_state["active_org"] = selected_org["org_id"]
            st.session_state["profile_scan_time"] = datetime.now().strftime("%d %b %Y · %H:%M:%S")
        except Exception as exc:
            st.error(f"Risk assessment failed: {exc}")
            st.stop()

profile_result = st.session_state.get("profile_result")
if profile_result and st.session_state.get("active_org") != selected_org["org_id"]:
    profile_result = None

# --- Hero ---
st.markdown("<div style='display:flex;justify-content:space-between;align-items:flex-start;gap:18px;flex-wrap:wrap'><div><div class='eyebrow'>CYBER DEFENCE / RISK OPERATIONS</div><h1 class='hero-title'>Security <span>Intelligence</span><br>Command Center</h1><div class='hero-copy'>Turn vulnerability noise into a clear order of action. Context-aware prioritisation, dependency intelligence, and explainable risk signals in one workspace.</div></div><div class='status-pill'><span class='status-dot'></span> ENGINE READY &nbsp;·&nbsp; PYTHON</div></div>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# Main navigation
tab_overview, tab_repo, tab_findings, tab_analytics, tab_method, tab_demo = st.tabs(["◈  Command overview", "⌘  Repository scanner", "◎  Vulnerability explorer", "▥  Analytics", "⌁  Methodology", "✓  Demo readiness"])

with tab_overview:
    if profile_result:
        vulns = profile_result["top_vulnerabilities"]
        meta = profile_result["metadata"]
        org = profile_result["organisation"]
        df = pd.DataFrame(vulns)
        total = meta.get("total_unique_cves_after_filtering", len(df))
        top_score = float(df["risk_score"].max()) if not df.empty else 0
        critical = int((df["risk_score"] >= 80).sum()) if not df.empty else 0
        kev_count = int(df["cisa_kev"].astype(bool).sum()) if not df.empty and "cisa_kev" in df else 0
        section("LIVE RISK POSTURE", f"Organisation context: {org['organisation_name']} · Last assessment: {st.session_state.get('profile_scan_time','Just now')}")
        mcols = st.columns(4, gap="medium")
        with mcols[0]: metric_card("Highest risk score", f"{top_score:.1f}<span style='font-size:.85rem;color:#718099'> /100</span>", "Highest ranked CVE in current assessment", "rgba(77,235,255,.10)")
        with mcols[1]: metric_card("CVEs evaluated", f"{total:,}", "Unique records after asset filtering", "rgba(167,139,250,.11)")
        with mcols[2]: metric_card("Priority alerts", f"{critical:,}", "Ranked records scoring 80 or above", "rgba(255,100,124,.10)")
        with mcols[3]: metric_card("KEV-listed", f"{kev_count:,}", "CISA KEV flags in ranked results", "rgba(167,139,250,.12)")

        st.markdown("<br>", unsafe_allow_html=True)
        left, right = st.columns([1.45, 1], gap="large")
        with left:
            st.markdown("<div class='panel'><div class='panel-title'>Risk signal distribution</div><div class='panel-sub'>How the highest-priority findings spread across the risk spectrum.</div>", unsafe_allow_html=True)
            if not df.empty:
                bands = pd.cut(df["risk_score"], bins=[-0.01, 35, 60, 80, 100.01], labels=["LOW", "GUARDED", "HIGH", "CRITICAL"])
                counts = bands.value_counts().reindex(["CRITICAL", "HIGH", "GUARDED", "LOW"], fill_value=0).reset_index()
                counts.columns = ["Risk band", "Findings"]
                fig = px.bar(counts, x="Findings", y="Risk band", orientation="h", color="Risk band", color_discrete_map={"CRITICAL":"#FF647C","HIGH":"#FFB86B","GUARDED":"#A78BFA","LOW":"#4DEBFF"}, text="Findings")
                fig.update_layout(**PLOT_LAYOUT, height=245, showlegend=False, xaxis_title="Findings", yaxis_title="", bargap=.38)
                fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
            else:
                st.info("No matching vulnerabilities found for this organisation profile.")
            st.markdown("</div>", unsafe_allow_html=True)
        with right:
            st.markdown("<div class='panel'><div class='panel-title'>Scoring model composition</div><div class='panel-sub'>Organisation-specific weights used by the deterministic engine.</div>", unsafe_allow_html=True)
            w = profile_result["weights"]
            wdf = pd.DataFrame({"Signal":["CVSS impact","CISA KEV","EPSS probability"],"Weight":[w["cvss_weight"],w["cisa_kev_weight"],w["first_epss_weight"]]})
            fig = px.pie(wdf, values="Weight", names="Signal", hole=.72, color="Signal", color_discrete_map={"CVSS impact":"#4DEBFF","CISA KEV":"#A78BFA","EPSS probability":"#E879F9"})
            fig.update_layout(
                **{
                    **PLOT_LAYOUT,
                    "legend": {
                        **PLOT_LAYOUT.get("legend", {}),
                        "orientation": "h",
                        "y": -0.15,
                        "x": 0.05,
                        "font": {**PLOT_LAYOUT.get("legend", {}).get("font", {}), "size": 10},
                    },
                },
                height=245,
                showlegend=True,
                margin=dict(l=0, r=0, t=0, b=25),
            )
            fig.update_traces(textinfo="percent", textfont_size=11, marker=dict(line=dict(color="#101522", width=3)))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        section("PRIORITY QUEUE", "The top five items to investigate first, based on this organisation's configured weights.")
        if df.empty:
            st.info("No vulnerabilities matched this organisation's critical products in the supplied dataset.")
        else:
            for _, v in df.head(5).iterrows():
                score = float(v["risk_score"])
                badge = "tag-red" if score >= 80 else ("tag-purple" if score >= 60 else "tag-cyan")
                kev = "CISA KEV LISTED" if bool(v["cisa_kev"]) else "NOT KEV-LISTED IN DATASET"
                st.markdown(f"<div class='finding'><div style='display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap'><span class='finding-id'>#{int(v['rank']):02d} &nbsp; / &nbsp; {html.escape(str(v['cve_id']))}</span><span class='tag {badge}'>RISK {score:.1f} / 100</span></div><div class='finding-title'>{html.escape(str(v['representative_product']))}</div><div class='finding-meta'>CVSS <b>{v['cvss_base_score']}</b> &nbsp;·&nbsp; EPSS <b>{float(v['first_epss']):.3f}</b> &nbsp;·&nbsp; <span style='color:{'#FF8FA0' if bool(v['cisa_kev']) else '#92A0B8'}'>{kev}</span><br>Dominant signal: <b>{html.escape(str(v['dominant_factor']))}</b> &nbsp;·&nbsp; Affected critical products: {html.escape(', '.join(v['affected_critical_products']))}</div></div>", unsafe_allow_html=True)
                with st.expander(f"Inspect {v['cve_id']} · explanation and score breakdown"):
                    a, b = st.columns([1.15, 1])
                    with a:
                        st.markdown("**WHY IT MATTERS**")
                        st.write(v["why_this_matters"])
                        st.markdown("**WHY IT RANKED HERE**")
                        st.write(v["why_ranked_high"])
                        st.markdown("**RECOMMENDED NEXT STEP**")
                        st.write(v["what_to_do_next"])
                    with b:
                        contrib = pd.DataFrame({"Signal":["CVSS","CISA KEV","EPSS"],"Contribution":[v["cvss_contribution"],v["kev_contribution"],v["epss_contribution"]]})
                        cf = px.bar(contrib, x="Contribution", y="Signal", orientation="h", color="Signal", color_discrete_map={"CVSS":"#4DEBFF","CISA KEV":"#A78BFA","EPSS":"#E879F9"})
                        cf.update_layout(**PLOT_LAYOUT, height=175, showlegend=False, xaxis_title="Score contribution", yaxis_title="", margin=dict(l=0,r=12,t=5,b=0))
                        cf.update_traces(marker_line_width=0)
                        st.plotly_chart(cf, use_container_width=True, config={"displayModeBar":False})
    else:
        st.info("Run an assessment from the left panel to load the organisation risk posture.")

with tab_repo:
    section("DEPENDENCY INTELLIGENCE", "Upload a requirements file or a project ZIP. VULNPRIOR reads dependency manifests only and never executes uploaded code.")
    st.markdown("<div class='panel'><div class='panel-title'>Repository intake</div><div class='panel-sub'>Supported manifests: requirements.txt, poetry.lock, Pipfile.lock, and pyproject.toml. Best coverage is available when package versions are pinned.</div>", unsafe_allow_html=True)
    uploaded = st.file_uploader("Drop a Python project ZIP or requirements.txt", type=["zip", "txt"], key="repo_upload")
    scan_col1, scan_col2 = st.columns([1, 2])
    with scan_col1:
        scan_button = st.button("⌕  Scan dependencies", type="primary", disabled=uploaded is None, use_container_width=True)
    with scan_col2:
        st.caption("Live lookup uses the public OSV vulnerability database. Only dependency names and versions are sent for lookup, not your source code.")
    st.markdown("</div>", unsafe_allow_html=True)
    if scan_button and uploaded is not None:
        try:
            with st.spinner("Reading manifests and querying OSV vulnerability intelligence..."):
                scan = scan_dependency_upload(uploaded.getvalue(), uploaded.name)
            st.session_state["repo_scan"] = scan
            st.session_state["repo_scan_name"] = uploaded.name
            st.session_state["repo_scan_time"] = datetime.now().strftime("%d %b %Y · %H:%M:%S")
        except Exception as exc:
            st.error(f"Could not scan this upload: {exc}")
    scan = st.session_state.get("repo_scan")
    if scan:
        st.markdown("<br>", unsafe_allow_html=True)
        status = scan.get("status")
        if status == "offline":
            st.warning("The manifest was parsed, but OSV could not be reached. Check connectivity and retry. No vulnerability-free conclusion can be drawn from this run.")
        elif status == "no_pinned_dependencies":
            st.warning("No exact-version dependencies were found. Pin dependency versions for reliable OSV matching.")
        else:
            st.success(f"Scan completed · {st.session_state.get('repo_scan_name','uploaded project')} · {st.session_state.get('repo_scan_time','')}")
        packages = scan.get("packages", [])
        findings = scan.get("findings", [])
        a,b,c = st.columns(3)
        with a: metric_card("Pinned dependencies", str(len(packages)), "Exact package versions parsed")
        with b: metric_card("Known vuln matches", str(len(findings)), "Matches returned by OSV", "rgba(255,100,124,.1)")
        with c: metric_card("Manifest files", str(len(scan.get("manifests", []))), "Supported files inspected", "rgba(167,139,250,.1)")
        if findings:
            fdf = pd.DataFrame(findings)
            show_cols = [c for c in ["package","version","cve_id","vulnerability_id","summary","cvss_vector_or_score"] if c in fdf.columns]
            st.markdown("<br><div class='panel-title'>Detected vulnerability matches</div>", unsafe_allow_html=True)
            st.dataframe(fdf[show_cols], use_container_width=True, hide_index=True, column_config={"summary":st.column_config.TextColumn("Summary", width="large")})
            for finding in findings[:15]:
                with st.expander(f"{finding['cve_id']} · {finding['package']} {finding['version']}"):
                    st.write(finding["summary"])
                    st.caption(f"OSV ID: {finding['vulnerability_id']} · Modified: {finding.get('modified') or 'Not provided'}")
                    if finding.get("fixed_versions"):
                        st.markdown("**Potential fixed versions listed by OSV:** " + ", ".join(finding["fixed_versions"]))
                    st.info(finding["assessment_note"])
                    for ref in finding.get("references", []):
                        if ref:
                            st.markdown(f"- [{ref}]({ref})")
        else:
            st.info("No known-vulnerability matches were returned for the exact dependency versions queried. This is not proof that the repository is secure; this scan does not inspect source code or unpinned dependencies.")
        with st.expander("Coverage, skipped dependencies, and warnings"):
            st.write("**Manifests inspected**", scan.get("manifests", []))
            st.write("**Skipped / unpinned entries**", scan.get("skipped", []) or "None")
            st.write("**Warnings**", scan.get("warnings", []) or "None")
        if packages:
            inv_col, json_col = st.columns(2)
            with inv_col:
                st.download_button("Download dependency inventory (CSV)", pd.DataFrame(packages).to_csv(index=False).encode("utf-8"), file_name="vulnprior_dependency_inventory.csv", mime="text/csv")
            with json_col:
                st.download_button("Download scan evidence (JSON)", json.dumps(scan, indent=2, default=str).encode("utf-8"), file_name="vulnprior_dependency_scan.json", mime="application/json")

with tab_findings:
    section("VULNERABILITY EXPLORER", "Search, filter, and export the ranked findings produced by the existing organisation-aware engine.")
    if profile_result:
        findings_df = pd.DataFrame(profile_result["top_vulnerabilities"])
        if not findings_df.empty:
            filters1, filters2, filters3 = st.columns([1.2, 1, 1])
            with filters1:
                query = st.text_input("Search CVE or product", placeholder="e.g. CVE-2025…")
            with filters2:
                kev_filter = st.selectbox("CISA KEV", ["All findings", "KEV listed", "Not KEV listed"])
            with filters3:
                min_risk = st.slider("Minimum risk score", 0, 100, 0, 5)
            filtered = findings_df.copy()
            if query:
                filtered = filtered[filtered.apply(lambda row: query.lower() in str(row["cve_id"]).lower() or query.lower() in str(row["representative_product"]).lower(), axis=1)]
            if kev_filter == "KEV listed": filtered = filtered[filtered["cisa_kev"].astype(bool)]
            if kev_filter == "Not KEV listed": filtered = filtered[~filtered["cisa_kev"].astype(bool)]
            filtered = filtered[filtered["risk_score"] >= min_risk]
            st.caption(f"Showing {len(filtered):,} of {len(findings_df):,} ranked records. Risk scores are organisation-specific.")
            display_cols = ["rank","cve_id","representative_product","risk_score","cvss_base_score","cisa_kev","first_epss","dominant_factor"]
            st.dataframe(filtered[display_cols], use_container_width=True, hide_index=True, column_config={"risk_score":st.column_config.ProgressColumn("Risk score", min_value=0, max_value=100, format="%.1f"), "first_epss":st.column_config.NumberColumn("EPSS", format="%.4f"), "cisa_kev":st.column_config.CheckboxColumn("CISA KEV")})
            st.download_button("↓ Export filtered findings CSV", filtered.to_csv(index=False).encode("utf-8"), file_name="vulnprior_ranked_findings.csv", mime="text/csv")
        else:
            st.info("No findings to display for the selected organisation.")
    else:
        st.info("Run an assessment to explore ranked vulnerabilities.")

with tab_analytics:
    section("RISK ANALYTICS", "Explore the currently selected organisation assessment. These charts reflect the loaded dataset, not live telemetry.")
    if profile_result:
        analytics_df = pd.DataFrame(profile_result["top_vulnerabilities"])
        if not analytics_df.empty:
            left, right = st.columns(2, gap="large")
            with left:
                st.markdown("<div class='panel'><div class='panel-title'>Risk score distribution</div><div class='panel-sub'>Count of findings across the configured priority bands.</div>", unsafe_allow_html=True)
                risk_bands = pd.cut(analytics_df["risk_score"], bins=[-0.01, 35, 60, 80, 100.01], labels=["LOW", "GUARDED", "HIGH", "CRITICAL"])
                band_counts = risk_bands.value_counts().reindex(["CRITICAL", "HIGH", "GUARDED", "LOW"], fill_value=0).rename_axis("Risk band").reset_index(name="Findings")
                fig_risk = px.bar(band_counts, x="Risk band", y="Findings", color="Risk band", color_discrete_map={"CRITICAL":"#FF647C", "HIGH":"#FFB86B", "GUARDED":"#A78BFA", "LOW":"#4DEBFF"})
                fig_risk.update_layout(**{**PLOT_LAYOUT, "margin": dict(l=0,r=0,t=10,b=0)}, height=300, showlegend=False)
                st.plotly_chart(fig_risk, use_container_width=True, config={"displayModeBar":False})
                st.markdown("</div>", unsafe_allow_html=True)
            with right:
                st.markdown("<div class='panel'><div class='panel-title'>Severity distribution</div><div class='panel-sub'>CVSS severity bands in the current ranked findings.</div>", unsafe_allow_html=True)
                sev = pd.cut(analytics_df["cvss_base_score"], bins=[-0.01, 4, 7, 9, 10.01], labels=["LOW", "MEDIUM", "HIGH", "CRITICAL"], right=False)
                sev_counts = sev.value_counts().reindex(["CRITICAL", "HIGH", "MEDIUM", "LOW"], fill_value=0).rename_axis("Severity").reset_index(name="Findings")
                fig_sev = px.pie(sev_counts, names="Severity", values="Findings", hole=0.58, color="Severity", color_discrete_map={"CRITICAL":"#FF647C", "HIGH":"#FFB86B", "MEDIUM":"#A78BFA", "LOW":"#4DEBFF"})
                fig_sev.update_layout(**{**PLOT_LAYOUT, "margin": dict(l=0,r=0,t=10,b=0)}, height=300)
                st.plotly_chart(fig_sev, use_container_width=True, config={"displayModeBar":False})
                st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("<br><div class='panel-title'>Highest-priority findings</div>", unsafe_allow_html=True)
            st.dataframe(analytics_df[[c for c in ["rank", "cve_id", "representative_product", "risk_score", "dominant_factor"] if c in analytics_df.columns]].head(10), use_container_width=True, hide_index=True)
    else:
        st.info("Run an assessment to load analytics.")

with tab_demo:
    section("UNIVERSITY DEMONSTRATION READINESS", "A repeatable demo path and concise explanations for project evaluation.")
    st.markdown("<div class='panel'><div class='panel-title'>Suggested live demonstration</div><div class='panel-sub'>Use this sequence to show both technical substance and usability.</div>", unsafe_allow_html=True)
    demo_steps = [
        ("1. Select organisation profile", "Explain that the profile changes in-scope products and scoring weights."),
        ("2. Run the risk assessment", "Show CVSS, EPSS, CISA KEV, weighted risk score, and ranked findings."),
        ("3. Inspect one finding", "Explain why the record ranks where it does; describe the score as a triage aid, not compromise probability."),
        ("4. Scan a Python project", "Upload a ZIP or requirements file. Point out the OSV advisory IDs, fixed-version hints, skipped entries, and coverage warnings."),
        ("5. Export evidence", "Download ranked findings and dependency inventory, then generate the PDF assessment report."),
        ("6. State limitations", "Clarify that dependency scanning is not a full source-code, secret, runtime, or exploit-chain audit."),
    ]
    for title, detail in demo_steps:
        st.checkbox(f"{title} — {detail}", key="demo_" + str(demo_steps.index((title, detail))))
    st.markdown("</div>", unsafe_allow_html=True)
    with st.expander("Viva quick answers"):
        st.markdown("**Why combine CVSS, EPSS, and CISA KEV?**\n\nThey represent technical severity, exploitation likelihood, and known exploitation respectively. Combining distinct signals supports prioritisation beyond severity alone.")
        st.markdown("**Why does the organisation profile matter?**\n\nDifferent organisations protect different assets and can choose different risk weights, so a CVE may receive a different priority in different contexts.")
        st.markdown("**Does a high score prove a system is exploitable?**\n\nNo. It is a deterministic prioritisation score. Validate affected versions, exposure, reachability, and vendor guidance.")
        st.markdown("**What does the repository scanner actually do?**\n\nIt reads supported dependency manifests and queries OSV for exact package versions. It does not execute uploaded code and is not a full source-code audit.")
        st.markdown("**What if OSV returns no matches?**\n\nThat is not proof of safety. Coverage can be limited by unpinned dependencies, unsupported manifests, advisory availability, and network failures.")

with tab_method:
    section("ENGINEERING TRANSPARENCY", "Clear provenance and honest boundaries are part of the security product.")
    lcol, rcol = st.columns(2, gap="large")
    with lcol:
        st.markdown("<div class='panel'><div class='panel-title'>Risk prioritisation pipeline</div><div class='panel-sub'>Deterministic, organisation-aware, and explainable.</div><ol style='color:#B6C0D3;line-height:1.9'><li>Load the supplied vulnerability records and organisation profile.</li><li>Filter records to the organisation's configured critical products.</li><li>Normalize CVSS, CISA KEV, and EPSS inputs.</li><li>Apply profile-specific weights to calculate the composite score.</li><li>Deduplicate CVEs, rank deterministically, and generate evidence-based explanations.</li></ol></div>", unsafe_allow_html=True)
    with rcol:
        st.markdown("<div class='panel'><div class='panel-title'>Repository scanner coverage</div><div class='panel-sub'>Dependency manifest matching, not a full source-code audit.</div><ul style='color:#B6C0D3;line-height:1.9'><li>Reads supported dependency manifests from a ZIP without extracting or executing files.</li><li>Uses exact pinned package versions for OSV lookups.</li><li>Reports returned advisory IDs, aliases, summaries, references, and fixed-version hints where available.</li><li>Does not claim to detect every vulnerability, reachable code path, secret, or exploit chain.</li></ul></div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div class='panel'><div class='panel-title'>Scoring interpretation</div><div class='panel-sub'>Risk score is a prioritization signal, not a calibrated probability of compromise.</div><div style='display:flex;gap:9px;flex-wrap:wrap'><span class='tag tag-cyan'>0–34 · LOW</span><span class='tag tag-purple'>35–59 · GUARDED</span><span class='tag' style='color:#FFD09A;background:#FFB86B12;border:1px solid #FFB86B33'>60–79 · HIGH</span><span class='tag tag-red'>80–100 · CRITICAL</span></div><p style='color:#9BA7BE;font-size:.82rem;line-height:1.7;margin-top:15px'>CVSS approximates technical severity, CISA KEV indicates inclusion in the known-exploited catalogue, and EPSS estimates the probability of exploitation activity. Their weighted combination is configured per organisation and should be interpreted alongside asset exposure, reachability, and business impact.</p></div>", unsafe_allow_html=True)

# --- Exportable report ---
st.markdown("<br><hr><div style='display:flex;justify-content:space-between;align-items:center;gap:15px;flex-wrap:wrap'><div><div class='eyebrow'>ASSESSMENT ARTIFACTS</div><div style='font-size:1.1rem;font-weight:800'>Generate a portable security report</div><div style='color:#8794AC;font-size:.8rem;margin-top:5px'>Export the current profile assessment and, if available, the latest repository scan.</div></div></div>", unsafe_allow_html=True)
try:
    pdf_bytes = build_pdf(selected_org["name"], st.session_state.get("repo_scan"), profile_result)
    st.download_button("↓  Generate PDF assessment report", data=pdf_bytes, file_name=f"vulnprior_nexus_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf", mime="application/pdf", type="primary")
except Exception as exc:
    st.warning(f"PDF report generation is unavailable in this environment: {exc}")

st.markdown("<br><div style='border-top:1px solid rgba(151,169,207,.14);padding-top:14px;display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;color:#68758D;font-size:.7rem;letter-spacing:.06em'><span>VULNPRIOR NEXUS · CYBER RISK INTELLIGENCE</span><span>EXPLAINABLE BY DESIGN · PYTHON POWERED</span></div>", unsafe_allow_html=True)
