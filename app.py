from html import escape
from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from agents import REQUIRED_COLUMNS, ALERT_COLUMNS, Orchestrator, load_dataset

st.set_page_config(
    page_title="Agentic Health Monitoring CDSS",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)
DATA_PATH = ROOT / "data" / "Synthetic_patient-HealthCare-Monitoring_dataset.csv"

# ----------------------------------------------------------------------------
# Design system
# ----------------------------------------------------------------------------
TEAL = "#0F766E"
TEAL_LIGHT = "#14B8A6"
AMBER = "#F59E0B"
ROSE = "#E11D48"
INDIGO = "#6366F1"
SLATE = "#64748B"
INK = "#0F172A"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"], .stMarkdown, .stText, button, input, select, textarea {
    font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif !important;
}
#MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }
.stApp { background: #F5F7FA; }
.block-container { padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1320px; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0B2B2A 0%, #0F3D3A 100%);
    border-right: none;
}
section[data-testid="stSidebar"] * { color: #E6F4F1; }
section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: #FFFFFF !important; letter-spacing: .2px; }
section[data-testid="stSidebar"] label p { font-size: .82rem; font-weight: 500; color: #BFE3DD !important; }
section[data-testid="stSidebar"] [data-baseweb="select"] > div,
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
    background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.14); border-radius: 10px;
}
section[data-testid="stSidebar"] [data-baseweb="select"] * { color: #FFFFFF !important; }
section[data-testid="stSidebar"] small, section[data-testid="stSidebar"] .stCaption { color: #8FC7BE !important; }
section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.12); }
.sb-brand { display:flex; align-items:center; gap:.65rem; padding:.2rem 0 1rem 0; }
.sb-brand .logo { width:38px; height:38px; border-radius:10px; background:rgba(20,184,166,.22);
    display:flex; align-items:center; justify-content:center; font-size:1.3rem; }
.sb-brand .name { font-weight:700; font-size:1.02rem; color:#fff; line-height:1.1; }
.sb-brand .sub { font-size:.72rem; color:#8FC7BE; }
.sb-section { font-size:.7rem; text-transform:uppercase; letter-spacing:1.2px; color:#6FB3A8;
    margin:1.1rem 0 .3rem 0; font-weight:600; }

/* Hero */
.hero {
    background: linear-gradient(120deg, #0B2B2A 0%, #0F766E 62%, #14B8A6 130%);
    border-radius: 18px; padding: 1.7rem 2rem; color: #fff; margin-bottom: 1.2rem;
    box-shadow: 0 10px 30px -12px rgba(15,118,110,.55); position: relative; overflow: hidden;
}
.hero::after { content:""; position:absolute; right:-60px; top:-60px; width:240px; height:240px;
    border-radius:50%; background: rgba(255,255,255,.07); }
.hero h1 { margin:0; font-size:1.7rem; font-weight:700; letter-spacing:-.3px; color:#fff; }
.hero p { margin:.35rem 0 0 0; color:#CFEDE8; font-size:.93rem; }
.badge { display:inline-block; padding:.18rem .65rem; border-radius:999px; font-size:.7rem; font-weight:600;
    background:rgba(255,255,255,.16); color:#fff; margin-right:.4rem; margin-top:.8rem; border:1px solid rgba(255,255,255,.2); }

/* KPI cards */
.kpi { background:#fff; border:1px solid #E6EBF1; border-radius:14px; padding:1rem 1.15rem;
    box-shadow:0 1px 2px rgba(15,23,42,.04); height:100%; border-top:3px solid var(--accent,#0F766E); }
.kpi .label { font-size:.72rem; text-transform:uppercase; letter-spacing:.9px; color:#64748B; font-weight:600; }
.kpi .value { font-size:1.85rem; font-weight:700; color:#0F172A; margin-top:.15rem; letter-spacing:-.5px; }
.kpi .sub { font-size:.76rem; color:#94A3B8; margin-top:.1rem; }

/* Section titles */
.section-title { font-size:1.05rem; font-weight:600; color:#0F172A; margin:.4rem 0 .2rem 0; }
.section-sub { font-size:.82rem; color:#64748B; margin-bottom:.8rem; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap:.3rem; border-bottom:1px solid #E2E8F0; }
.stTabs [data-baseweb="tab"] { height:44px; padding:0 1.1rem; border-radius:10px 10px 0 0;
    color:#64748B; font-weight:500; background:transparent; }
.stTabs [aria-selected="true"] { color:#0F766E !important; font-weight:600; }
.stTabs [data-baseweb="tab-highlight"] { background-color:#0F766E; height:3px; }

/* Chart + dataframe containers */
div[data-testid="stPlotlyChart"], div[data-testid="stDataFrame"] {
    background:#fff; border:1px solid #E6EBF1; border-radius:14px; padding:.5rem;
    box-shadow:0 1px 2px rgba(15,23,42,.04);
}

/* Buttons */
.stButton > button[kind="primary"], .stDownloadButton > button {
    background:#0F766E; color:#fff; border:none; border-radius:10px; padding:.55rem 1.3rem; font-weight:600;
    box-shadow:0 4px 12px -4px rgba(15,118,110,.5); transition:all .15s ease;
}
.stButton > button[kind="primary"]:hover, .stDownloadButton > button:hover { background:#0B5F58; color:#fff; transform:translateY(-1px); }

/* Finding / info cards */
.card { background:#fff; border:1px solid #E6EBF1; border-left:5px solid var(--c,#64748B);
    border-radius:12px; padding:1rem 1.2rem; margin-bottom:.8rem; box-shadow:0 1px 2px rgba(15,23,42,.04); }
.card .t { font-weight:600; color:#0F172A; font-size:.97rem; display:flex; align-items:center; gap:.5rem; }
.card .e { color:#475569; font-size:.88rem; margin:.4rem 0; line-height:1.55; }
.card .a { color:#0F172A; font-size:.84rem; background:#F8FAFC; border-radius:8px; padding:.5rem .7rem; margin-top:.4rem; }
.pill { font-size:.65rem; font-weight:700; letter-spacing:.8px; text-transform:uppercase; padding:.15rem .55rem;
    border-radius:999px; color:#fff; background:var(--c,#64748B); }
.explain { background:linear-gradient(135deg,#ECFDF9 0%,#F0F9FF 100%); border:1px solid #CDEFE8;
    border-radius:14px; padding:1.1rem 1.3rem; color:#134E4A; line-height:1.65; font-size:.93rem; }
.explain .src { font-size:.7rem; text-transform:uppercase; letter-spacing:1px; color:#0F766E; font-weight:700; margin-bottom:.35rem; }
.rec { display:flex; gap:.7rem; background:#fff; border:1px solid #E6EBF1; border-radius:12px;
    padding:.75rem 1rem; margin-bottom:.5rem; color:#334155; font-size:.9rem; line-height:1.5; }
.rec .n { flex:0 0 26px; height:26px; border-radius:50%; background:#E6F6F3; color:#0F766E;
    font-weight:700; font-size:.78rem; display:flex; align-items:center; justify-content:center; }
.chips { margin:.2rem 0 .9rem 0; }
.chip { display:inline-block; background:#fff; border:1px solid #D9E2EC; color:#334155; border-radius:999px;
    padding:.2rem .75rem; font-size:.76rem; margin-right:.4rem; font-weight:500; }
.chip b { color:#0F766E; }
.disclaimer { background:#FFFBEB; border:1px solid #FDE68A; color:#92400E; border-radius:12px;
    padding:.9rem 1.1rem; font-size:.82rem; line-height:1.55; margin-top:1rem; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# UI helpers
# ----------------------------------------------------------------------------
def kpi(label, value, sub="", accent=TEAL):
    return (f'<div class="kpi" style="--accent:{accent}"><div class="label">{escape(label)}</div>'
            f'<div class="value">{escape(str(value))}</div><div class="sub">{escape(sub)}&nbsp;</div></div>')


def section(title, sub=""):
    st.markdown(f'<div class="section-title">{escape(title)}</div>'
                f'<div class="section-sub">{escape(sub)}</div>', unsafe_allow_html=True)


def style_fig(fig, height=340, legend=False):
    fig.update_layout(
        template="plotly_white", height=height,
        margin=dict(l=12, r=12, t=52, b=12),
        font=dict(family="Inter, sans-serif", size=12, color="#334155"),
        title=dict(font=dict(size=15, color=INK), x=0.01),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        bargap=0.08, showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=None),
        hoverlabel=dict(bgcolor="white", font_size=12),
    )
    fig.update_xaxes(showgrid=False, linecolor="#E2E8F0", title_font=dict(size=11, color=SLATE))
    fig.update_yaxes(gridcolor="#EEF2F6", zeroline=False, title_font=dict(size=11, color=SLATE))
    return fig


def histogram(data, col, title, nbins, color):
    fig = px.histogram(data, x=col, nbins=nbins, title=title, color_discrete_sequence=[color])
    fig.update_traces(marker_line_color="white", marker_line_width=1, opacity=0.92)
    series = data[col].dropna()
    if not series.empty:
        fig.add_vline(x=float(series.median()), line_dash="dot", line_color=INK, line_width=1.2,
                      annotation_text=f"median {series.median():.1f}", annotation_position="top",
                      annotation_font=dict(size=10, color=INK))
    fig.update_yaxes(title="Records")
    return style_fig(fig)


LEVEL_STYLE = {
    "attention": (AMBER, "Attention"),
    "good": (TEAL_LIGHT, "Stable"),
}


def finding_card(finding):
    color, tag = LEVEL_STYLE.get(finding["level"], (INDIGO, "Info"))
    evidence = escape(str(finding["evidence"])).replace("\n", "<br>")
    action = escape(str(finding["action"])).replace("\n", "<br>")
    st.markdown(
        f'<div class="card" style="--c:{color}"><div class="t"><span class="pill">{tag}</span>'
        f'{escape(str(finding["title"]))}</div><div class="e">{evidence}</div>'
        f'<div class="a"><b>Next step:</b> {action}</div></div>',
        unsafe_allow_html=True,
    )


# ----------------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------------
st.markdown(
    """
    <div class="hero">
        <h1>🩺 Agentic Health Monitoring &amp; Clinical Decision Support</h1>
        <p>Multi-agent analysis of patient vitals, alert labels and data quality, with optional local-LLM explanations.</p>
        <span class="badge">Research prototype</span>
        <span class="badge">Synthetic dataset</span>
        <span class="badge">Monitoring prompts, not diagnoses</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# Sidebar: data source
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        '<div class="sb-brand"><div class="logo">🩺</div><div><div class="name">Health CDSS</div>'
        '<div class="sub">Agentic monitoring console</div></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="sb-section">Data source</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("Optional: upload the same CSV dataset", type=["csv"])
    st.markdown('<div class="sb-section">AI explanation</div>', unsafe_allow_html=True)
    use_ollama = st.checkbox(
        "Use local Ollama for plain-language explanation", value=False,
        help="Requires Ollama running locally and the model in OLLAMA_MODEL. Rule-based fallback is used if unavailable.",
    )
    st.caption("No webhook is needed for this Streamlit dashboard.")

try:
    df = pd.read_csv(uploaded) if uploaded is not None else load_dataset(str(DATA_PATH))
except Exception as exc:
    st.error(f"Could not load dataset: {exc}")
    st.info("Put Synthetic_patient-HealthCare-Monitoring_dataset.csv in the project's data folder or upload it in the sidebar.")
    st.stop()

missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
if missing:
    st.error("This CSV does not match the expected dataset schema. Missing columns: " + ", ".join(missing))
    st.stop()

for col in ["Patient Number", "Heart Rate (bpm)", "SpO2 Level (%)", "Systolic Blood Pressure (mmHg)",
            "Diastolic Blood Pressure (mmHg)", "Body Temperature (°C)", "Data Accuracy (%)"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Filters use supplied dataset labels; no medical reclassification is performed.
with st.sidebar:
    st.markdown('<div class="sb-section">Filters</div>', unsafe_allow_html=True)
    patients = sorted(df["Patient Number"].dropna().unique().tolist())
    patient_options = ["All records"] + patients
    selected_patient = st.selectbox(
        "Patient Number", patient_options, index=0,
        format_func=lambda x: x if isinstance(x, str) else f"Patient {int(x)}",
    )
    disease_options = ["All"] + sorted(df["Predicted Disease"].fillna("Unknown").astype(str).unique().tolist())
    selected_disease = st.selectbox("Predicted Disease", disease_options)
    accuracy_floor = st.slider("Minimum Data Accuracy (%)", 0, 100, 0)
    only_alerts = st.checkbox("Show records with any ABNORMAL alert", value=False)

filtered = df.copy()
if selected_patient != "All records":
    filtered = filtered[filtered["Patient Number"] == float(selected_patient)]
if selected_disease != "All":
    filtered = filtered[filtered["Predicted Disease"].fillna("Unknown").astype(str) == selected_disease]
filtered = filtered[filtered["Data Accuracy (%)"].fillna(-1) >= accuracy_floor]
if only_alerts:
    abnormal_mask = pd.Series(False, index=filtered.index)
    for c in ALERT_COLUMNS:
        abnormal_mask |= filtered[c].astype(str).str.strip().str.upper().eq("ABNORMAL")
    fall = filtered["Fall Detection"].astype(str).str.strip().str.lower().isin(["yes", "true", "1", "detected", "fall"])
    filtered = filtered[abnormal_mask | fall]

if filtered.empty:
    st.warning("No records match the current filters.")
    st.stop()

# Active-filter chips
chips = []
chips.append(f'<span class="chip">Patient: <b>{"All" if selected_patient == "All records" else int(selected_patient)}</b></span>')
chips.append(f'<span class="chip">Disease: <b>{escape(selected_disease)}</b></span>')
chips.append(f'<span class="chip">Accuracy ≥ <b>{accuracy_floor}%</b></span>')
if only_alerts:
    chips.append('<span class="chip"><b>Alerts only</b></span>')
st.markdown('<div class="chips">' + "".join(chips) + "</div>", unsafe_allow_html=True)

# Cohort-level KPIs
cohort = Orchestrator().run(filtered, patient_number=None, use_ollama=False)
mon = cohort["monitoring_summary"]
alert_total = sum(v["abnormal"] for v in mon["alert_counts"].values())
fall_total = mon["fall_detected_records"]

share = len(filtered) / len(df) * 100 if len(df) else 0
cols = st.columns(5, gap="medium")
cols[0].markdown(kpi("Dataset rows", f"{len(df):,}", "Total loaded", SLATE), unsafe_allow_html=True)
cols[1].markdown(kpi("Filtered records", f"{len(filtered):,}", f"{share:.0f}% of dataset", TEAL), unsafe_allow_html=True)
cols[2].markdown(kpi("Unique patients", f"{filtered['Patient Number'].nunique():,}", "In current view", TEAL_LIGHT), unsafe_allow_html=True)
cols[3].markdown(kpi("ABNORMAL labels", f"{alert_total:,}", "Across all alert fields", AMBER), unsafe_allow_html=True)
cols[4].markdown(kpi("Positive fall flags", f"{fall_total:,}", "Fall detection", ROSE), unsafe_allow_html=True)

st.write("")
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Alert analysis", "Patient agent analysis", "Dataset & quality"])

# ----------------------------------------------------------------------------
# Tab 1: Overview
# ----------------------------------------------------------------------------
with tab1:
    section("Vital sign distributions", "Dotted line marks the median of the filtered records.")
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        st.plotly_chart(histogram(filtered, "Heart Rate (bpm)", "Heart rate (bpm)", 30, TEAL), use_container_width=True)
    with c2:
        st.plotly_chart(histogram(filtered, "SpO2 Level (%)", "SpO₂ level (%)", 20, INDIGO), use_container_width=True)
    c3, c4 = st.columns(2, gap="medium")
    with c3:
        st.plotly_chart(histogram(filtered, "Systolic Blood Pressure (mmHg)", "Systolic blood pressure (mmHg)", 30, AMBER), use_container_width=True)
    with c4:
        st.plotly_chart(histogram(filtered, "Body Temperature (°C)", "Body temperature (°C)", 25, ROSE), use_container_width=True)

    st.write("")
    section("Predicted disease labels", "Labels supplied by the dataset for the filtered records.")
    disease_counts = (filtered["Predicted Disease"].fillna("Unknown").value_counts()
                      .rename_axis("Predicted Disease").reset_index(name="Records"))
    fig = px.bar(disease_counts, x="Predicted Disease", y="Records", color_discrete_sequence=[TEAL], text="Records")
    fig.update_traces(textposition="outside", marker_line_width=0, cliponaxis=False)
    st.plotly_chart(style_fig(fig, height=360), use_container_width=True)

# ----------------------------------------------------------------------------
# Tab 2: Alert analysis
# ----------------------------------------------------------------------------
with tab2:
    section("Alert label summary", "Normal vs. abnormal counts for each alert field.")
    alert_rows = []
    for col, counts in mon["alert_counts"].items():
        normal = counts.get("normal", 0)
        abnormal = counts.get("abnormal", 0)
        total = normal + abnormal
        alert_rows.append({
            "Alert field": col, **counts,
            "Abnormal rate (%)": round(abnormal / total * 100, 1) if total else 0.0,
        })
    if alert_rows:
        table = pd.DataFrame(alert_rows)
        st.dataframe(
            table, use_container_width=True, hide_index=True,
            column_config={
                "Abnormal rate (%)": st.column_config.ProgressColumn(
                    "Abnormal rate (%)", min_value=0, max_value=100, format="%.1f%%"),
            },
        )
        st.write("")
        ch1, ch2 = st.columns([3, 2], gap="medium")
        with ch1:
            chart_df = table.melt(id_vars="Alert field", value_vars=["normal", "abnormal"],
                                  var_name="Label", value_name="Records")
            chart_df["Label"] = chart_df["Label"].str.title()
            fig = px.bar(chart_df, x="Alert field", y="Records", color="Label", barmode="group",
                         title="Label counts by alert field",
                         color_discrete_map={"Normal": TEAL_LIGHT, "Abnormal": ROSE})
            st.plotly_chart(style_fig(fig, height=380, legend=True), use_container_width=True)
        with ch2:
            totals = pd.DataFrame({"Label": ["Normal", "Abnormal"],
                                   "Records": [int(table["normal"].sum()), int(table["abnormal"].sum())]})
            fig = px.pie(totals, names="Label", values="Records", hole=0.62, title="Overall label share",
                         color="Label", color_discrete_map={"Normal": TEAL_LIGHT, "Abnormal": ROSE})
            fig.update_traces(textinfo="percent", marker=dict(line=dict(color="white", width=2)))
            st.plotly_chart(style_fig(fig, height=380, legend=True), use_container_width=True)
    st.caption("Counts are based on the dataset's supplied NORMAL/ABNORMAL labels; they are not independently validated clinical outcomes.")

# ----------------------------------------------------------------------------
# Tab 3: Patient agent analysis
# ----------------------------------------------------------------------------
with tab3:
    section("Run the agent pipeline", "Select a record to generate findings, explanation and decision-support prompts.")
    patient_choices = sorted(filtered["Patient Number"].dropna().unique().tolist())
    sel_col, btn_col = st.columns([3, 1], gap="medium", vertical_alignment="bottom")
    with sel_col:
        if selected_patient != "All records" and patient_choices:
            focus_patient = float(selected_patient)
            st.markdown(f'<div class="chip">Focused record: <b>Patient {int(focus_patient)}</b></div>', unsafe_allow_html=True)
        else:
            focus_patient = st.selectbox("Choose a record for agent analysis", patient_choices, key="agent_patient",
                                         format_func=lambda x: f"Patient {int(x)}")
    with btn_col:
        run_clicked = st.button("Run agents", type="primary", use_container_width=True)
    if run_clicked:
        with st.spinner("Agents are analysing the record…"):
            st.session_state["last_agent_result"] = Orchestrator().run(
                filtered, patient_number=focus_patient, use_ollama=use_ollama)

    result = st.session_state.get("last_agent_result")
    st.write("")
    if result:
        st.markdown(
            f'<div class="explain"><div class="src">Plain-language summary · {escape(str(result["explanation"]["provider"]))}</div>'
            f'{escape(str(result["explanation"]["text"])).replace(chr(10), "<br>")}</div>',
            unsafe_allow_html=True,
        )
        st.write("")
        left, right = st.columns([3, 2], gap="large")
        with left:
            section("Monitoring findings")
            for finding in result["findings"]:
                finding_card(finding)
        with right:
            section("Clinical decision-support prompts")
            for i, rec in enumerate(result["recommendations"], 1):
                st.markdown(f'<div class="rec"><div class="n">{i}</div><div>{escape(str(rec))}</div></div>',
                            unsafe_allow_html=True)
        with st.expander("Selected record details"):
            st.json(result["selected_patient"])
    else:
        st.info("Choose a record and click Run agents. Ollama is optional; rule-based fallback is available.")

# ----------------------------------------------------------------------------
# Tab 4: Dataset & quality
# ----------------------------------------------------------------------------
with tab4:
    q1, q2, q3 = st.columns(3, gap="medium")
    acc = filtered["Data Accuracy (%)"].dropna()
    q1.markdown(kpi("Mean data accuracy", f"{acc.mean():.1f}%" if not acc.empty else "n/a", "Filtered records", TEAL), unsafe_allow_html=True)
    q2.markdown(kpi("Min data accuracy", f"{acc.min():.1f}%" if not acc.empty else "n/a", "Lowest in view", AMBER), unsafe_allow_html=True)
    q3.markdown(kpi("Missing values", f"{int(filtered.isna().sum().sum()):,}", "Across all columns", SLATE), unsafe_allow_html=True)
    st.write("")

    j1, j2 = st.columns(2, gap="medium")
    with j1:
        section("Data ingestion agent report")
        st.json(cohort["ingestion_summary"], expanded=False)
    with j2:
        section("Cross-sectional summary")
        st.json(cohort["trend_summary"], expanded=False)
        st.caption(cohort["trend_summary"]["note"])

    st.write("")
    section("Filtered records", f"{len(filtered):,} rows")
    st.dataframe(filtered, use_container_width=True, hide_index=True, height=420)
    st.download_button("Download filtered CSV", data=filtered.to_csv(index=False).encode("utf-8"),
                       file_name="filtered_health_monitoring_records.csv", mime="text/csv")

st.markdown(
    '<div class="disclaimer"><b>Safety note:</b> this synthetic-data prototype is for research/demo use only. '
    'Dataset predictions and alert flags are not diagnoses; this is not a clinical device or emergency service. '
    'Always seek qualified professional assessment for real health concerns.</div>',
    unsafe_allow_html=True,
)
