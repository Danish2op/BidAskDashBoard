from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import requests
import streamlit as st
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent / "src"))

from tickdash.analyzer import KEY_DEPTHS, analyze_snapshots
from tickdash.app_helpers import kaggle_auth, kaggle_dataset_download_url, materialize_downloaded_file, materialize_uploaded_csv
from tickdash.csv_loader import list_instrument_keys, load_snapshots_with_count
from tickdash.metadata_refresh import merge_metadata_rows
from tickdash.metadata_store import open_metadata_store
from tickdash.ui_model import chart_key, make_fill_rows, make_ladder_rows, preferred_default_key, select_snapshot_index
from tickdash.upstox_metadata import fetch_current_metadata_for_keys


LOT_SIZE = 65
ORDER_LOTS = 100
DOWNSAMPLE = 20
DEFAULT_CSV_PATH = "/Users/danishsharma/Downloads/market_ticks.csv"


load_dotenv(Path(__file__).with_name(".env"))

pio.templates["tickdash_dark"] = go.layout.Template(
    layout=go.Layout(
        paper_bgcolor="#0b1014",
        plot_bgcolor="#0b1014",
        font={"family": "Avenir Next, Helvetica Neue, sans-serif", "color": "#dbe6e8", "size": 12},
        title={"font": {"family": "DIN Condensed, Avenir Next Condensed, sans-serif", "color": "#f3fbfc", "size": 22}},
        colorway=["#69d2e7", "#38d68c", "#f4bf4f", "#ff5d5d", "#9bbcff", "#c6f56f"],
        xaxis={"gridcolor": "#1c282e", "linecolor": "#314047", "tickfont": {"color": "#9aa9ae"}, "zerolinecolor": "#314047"},
        yaxis={"gridcolor": "#1c282e", "linecolor": "#314047", "tickfont": {"color": "#9aa9ae"}, "zerolinecolor": "#314047"},
        legend={"font": {"color": "#c8d5d8"}, "bgcolor": "rgba(11,16,20,.72)"},
    )
)


st.set_page_config(page_title="NIFTY Depth Analyzer", layout="wide")
st.markdown(
    """
    <style>
    :root, html, body, [data-testid="stAppViewContainer"] {
      --ink: #dbe6e8;
      --ink-strong: #f3fbfc;
      --muted: #84949a;
      --muted-strong: #a9b8bd;
      --panel: #10161a;
      --panel-2: #151d22;
      --field: #0b1115;
      --line: #27343a;
      --green: #38d68c;
      --red: #ff5d5d;
      --amber: #f4bf4f;
      --cyan: #69d2e7;
      color-scheme: dark;
    }
    .stApp, [data-testid="stAppViewContainer"], .main, section.main {
      background:
        linear-gradient(180deg, rgba(11,15,20,.96), rgba(8,10,13,.99)),
        radial-gradient(circle at 20% 0%, rgba(105,210,231,.10), transparent 32%);
      color: var(--ink) !important;
      font-family: "Avenir Next", "DIN Alternate", "Helvetica Neue", sans-serif;
    }
    h1, h2, h3, h4, h5, h6, .stMarkdown h4 {
      color: var(--ink-strong) !important;
      letter-spacing: .02em;
      font-family: "DIN Condensed", "Avenir Next Condensed", "Helvetica Neue", sans-serif;
    }
    p, span, label, div, small, caption, [data-testid="stMarkdownContainer"] {
      color: inherit;
    }
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stCaptionContainer"],
    [data-testid="stWidgetLabel"] label,
    [data-testid="stWidgetLabel"] p {
      color: var(--muted-strong) !important;
    }
    [data-testid="stSidebar"] {
      background: #0c1115 !important;
      border-right: 1px solid var(--line);
    }
    [data-testid="stSidebar"] * {
      color: var(--ink) !important;
    }
    input, textarea, select,
    [data-baseweb="input"] input,
    [data-baseweb="select"] > div,
    [data-baseweb="base-input"],
    [data-baseweb="tag"] {
      background: var(--field) !important;
      color: var(--ink-strong) !important;
      border-color: var(--line) !important;
    }
    [data-baseweb="select"] svg,
    [data-baseweb="select"] span {
      color: var(--ink-strong) !important;
      fill: var(--ink-strong) !important;
    }
    [role="listbox"], [role="option"] {
      background: #0c1115 !important;
      color: var(--ink-strong) !important;
    }
    [data-testid="stMetric"] {
      background: linear-gradient(180deg, rgba(21,29,34,.95), rgba(13,18,22,.95)) !important;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px 12px;
      box-shadow: inset 0 1px 0 rgba(255,255,255,.04);
    }
    [data-testid="stMetricValue"] {
      color: var(--ink-strong) !important;
      font-family: "SFMono-Regular", "Menlo", "IBM Plex Mono", monospace;
      font-size: 1.22rem;
    }
    [data-testid="stMetricLabel"] {
      color: var(--muted-strong) !important;
      text-transform: uppercase;
      letter-spacing: .08em;
      font-size: .68rem;
    }
    div[data-testid="stDataFrame"] {
      background: var(--panel) !important;
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
    }
    iframe, canvas, svg {
      color-scheme: dark;
    }
    [data-testid="stTable"], [data-testid="stDataFrameResizable"] {
      color: var(--ink) !important;
      background: var(--panel) !important;
    }
    .chart-card {
      border: 1px solid var(--line);
      background: linear-gradient(180deg, rgba(16,22,26,.86), rgba(11,15,19,.92)) !important;
      border-radius: 8px;
      padding: 10px 12px 4px;
      margin: 12px 0;
      box-shadow: 0 16px 40px rgba(0,0,0,.24);
    }
    .stButton > button {
      border-radius: 6px;
      border: 1px solid var(--line);
      background: #11191e !important;
      color: var(--ink-strong) !important;
      font-family: "SFMono-Regular", "Menlo", monospace;
      letter-spacing: .02em;
    }
    .stButton > button:hover {
      border-color: var(--cyan);
      color: #ffffff !important;
      box-shadow: 0 0 0 1px rgba(105,210,231,.25);
    }
    div[data-testid="stDialog"] {
      backdrop-filter: blur(10px);
      background: rgba(2,5,8,.68) !important;
    }
    div[data-testid="stDialog"] div[role="dialog"] {
      width: min(92vw, 1500px);
      max-width: min(92vw, 1500px);
      background: #0b1014 !important;
      color: var(--ink) !important;
      border: 1px solid var(--line);
      border-radius: 10px;
      box-shadow: 0 30px 120px rgba(0,0,0,.68);
    }
    .stAlert {
      background: #121a1f !important;
      color: var(--ink-strong) !important;
      border: 1px solid var(--line) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def cached_instrument_keys(csv_path: str) -> list[str]:
    return list_instrument_keys(csv_path)


@st.cache_data(show_spinner=True)
def cached_snapshots(csv_path: str, instrument_key: str, downsample: int) -> tuple[list, int]:
    return load_snapshots_with_count(csv_path, instrument_key, downsample=downsample)


@st.cache_data(show_spinner=True)
def cached_public_csv_url(public_url: str) -> str:
    download_url = kaggle_dataset_download_url(public_url)
    response = requests.get(download_url, timeout=180, auth=kaggle_auth(download_url, os.environ))
    response.raise_for_status()
    path = materialize_downloaded_file(
        download_url,
        response.content,
        Path(tempfile.gettempdir()) / "tickdashboard_downloads",
    )
    return str(path)


def refresh_metadata(keys: set[str]) -> dict[str, dict]:
    service_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    sheet_id = os.getenv("METADATA_SHEET_ID", "")
    tab = os.getenv("METADATA_SHEET_TAB", "MetaDataInstruments")
    if not service_json or not sheet_id:
        st.warning("Metadata sheet env missing. Set GOOGLE_SERVICE_ACCOUNT_JSON and METADATA_SHEET_ID.")
        return {}
    store = open_metadata_store(service_json, sheet_id, tab)
    existing = store.load_by_instrument_key()
    fetched = fetch_current_metadata_for_keys(keys)
    merged = merge_metadata_rows(keys, existing, fetched)
    store.replace_all(merged)
    return {row["instrument_key_as_seen"]: row for row in merged}


def instrument_label(key: str, meta: dict[str, dict]) -> str:
    row = meta.get(key) or {}
    symbol = row.get("trading_symbol") or key
    expiry = row.get("expiry") or ""
    side = row.get("instrument_type") or ""
    strike = row.get("strike_price") or ""
    if expiry or strike or side:
        return f"{symbol} | {expiry} | {strike} {side}".strip()
    return symbol


def get_atm(spot: float, interval: int = 50) -> int:
    lower = int(spot // interval) * interval
    midpoint = lower + interval / 2
    return lower if spot <= midpoint else lower + interval


def find_atm_key(keys: list[str], meta: dict[str, dict], atm: int) -> str | None:
    for desired_side in ("CE", "PE"):
        for key in keys:
            row = meta.get(key) or {}
            try:
                strike = int(float(row.get("strike_price") or -1))
            except ValueError:
                strike = -1
            if strike == atm and row.get("instrument_type") == desired_side:
                return key
    return None


def line_chart(title: str, labels: list[str], series: list[dict]) -> go.Figure:
    fig = go.Figure()
    for item in series:
        fig.add_trace(
            go.Scatter(
                x=labels,
                y=item["y"],
                name=item["name"],
                mode="lines+markers" if item.get("markers") else "lines",
                line={"dash": item.get("dash", "solid"), "width": item.get("width", 1.5)},
                marker={"size": item.get("marker_size", 6)},
            )
        )
    fig.update_layout(template="tickdash_dark", title=title, height=280, margin=dict(l=20, r=20, t=45, b=20))
    return fig


def bar_chart(title: str, x: list, y: list) -> go.Figure:
    fig = go.Figure(go.Bar(x=x, y=y))
    fig.update_layout(template="tickdash_dark", title=title, height=240, margin=dict(l=20, r=20, t=45, b=20))
    return fig


@st.dialog("Expanded chart", width="large")
def chart_modal(title: str, fig: go.Figure):
    modal_fig = go.Figure(fig)
    modal_fig.update_layout(height=760, title=title, margin=dict(l=28, r=28, t=58, b=32))
    st.plotly_chart(modal_fig, use_container_width=True, config={"displayModeBar": True})


def chart_panel(title: str, fig: go.Figure):
    key = chart_key(title)
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    if st.button(f"{title}  |  open large", key=f"open_{key}", use_container_width=True):
        chart_modal(title, fig)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    st.markdown("</div>", unsafe_allow_html=True)


def fmt(value, digits: int = 3) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def render_iqr_cell(label: str, stats: dict, suffix: str = ""):
    st.metric(label, f"{fmt(stats.get('median'))}{suffix}")
    st.caption(
        f"Q1 {fmt(stats.get('q1'))} | Q3 {fmt(stats.get('q3'))} | "
        f"IQR {fmt(stats.get('iqr'))} | Fence Hi {fmt(stats.get('fence_hi'))} | "
        f"Outliers {fmt(stats.get('outlier_pct'), 1)}%"
    )


st.title("NIFTY Depth Analyzer v2")
st.caption("Order-book depth, slippage, and fill simulation from local tick CSV with expiry-safe metadata")

with st.sidebar:
    source_mode = st.radio("Data source", ["Public URL", "Local path", "Upload CSV"], horizontal=False)
    csv_path = ""
    if source_mode == "Public URL":
        public_url = st.text_input("Public CSV / Kaggle dataset URL", "")
        if not public_url.strip():
            st.info("Paste public CSV URL or Kaggle dataset URL.")
            st.stop()
        try:
            csv_path = cached_public_csv_url(public_url.strip())
        except Exception:
            st.error("Could not download CSV. Use a direct public CSV URL or Kaggle dataset URL.")
            st.stop()
    elif source_mode == "Local path":
        csv_path = st.text_input("Market tick CSV path", DEFAULT_CSV_PATH)
        if not Path(csv_path).exists():
            st.error("CSV path not found.")
            st.stop()
    else:
        uploaded_csv = st.file_uploader("Upload market tick CSV", type=["csv"])
        if uploaded_csv is None:
            st.info("Upload CSV to run hosted dashboard.")
            st.stop()
        csv_path = str(
            materialize_uploaded_csv(
                uploaded_csv.name,
                uploaded_csv.getvalue(),
                Path(tempfile.gettempdir()) / "tickdashboard_uploads",
            )
        )

    with st.spinner("Reading instruments..."):
        keys = cached_instrument_keys(csv_path)

    if "metadata_by_key" not in st.session_state:
        with st.spinner("Refreshing metadata sheet..."):
            try:
                st.session_state.metadata_by_key = refresh_metadata(set(keys))
                st.success(f"Metadata mapped: {len(st.session_state.metadata_by_key)} instruments")
            except Exception:
                st.session_state.metadata_by_key = {}
                st.warning("Metadata refresh failed. Check Google Sheet sharing and service-account access.")

    if st.button("Refresh metadata now"):
        with st.spinner("Refreshing metadata sheet..."):
            try:
                st.session_state.metadata_by_key = refresh_metadata(set(keys))
            except Exception:
                st.warning("Metadata refresh failed. Check Google Sheet sharing and service-account access.")

    meta = st.session_state.metadata_by_key
    spot = st.number_input("Spot Price", value=0.0, step=50.0)
    atm_key = None
    if spot > 0:
        atm = get_atm(spot)
        st.caption(f"ATM {atm}")
        atm_key = find_atm_key(keys, meta, atm)

    labels = {instrument_label(key, meta): key for key in keys}
    default_key = atm_key or preferred_default_key(keys)
    default_label = next((label for label, key in labels.items() if key == default_key), list(labels)[0])
    selected_label = st.selectbox("Strike / Instrument", list(labels), index=list(labels).index(default_label))
    instrument_key = labels[selected_label]

    time_input = st.text_input("Time HH:MM:SS", "")
    side = st.radio("Side", ["buy", "sell"], horizontal=True)
    lots = st.number_input("Lots", min_value=1, value=ORDER_LOTS, step=1)
    selected_depths = st.multiselect("Depth levels", KEY_DEPTHS, default=[1, 2, 3, 4, 5])
    if not selected_depths:
        selected_depths = [1]

with st.spinner("Loading selected instrument snapshots..."):
    snapshots, total_snapshot_count = cached_snapshots(csv_path, instrument_key, DOWNSAMPLE)
if not snapshots:
    st.error("No snapshots found for selected instrument.")
    st.stop()

data = analyze_snapshots(snapshots, lot_size=LOT_SIZE, order_lots=ORDER_LOTS, total_snapshots=total_snapshot_count)
snap_idx = select_snapshot_index(data["ts_labels"], time_input)
snap = data["snapshots"][snap_idx]
snap_label = "latest" if snap_idx == -1 else data["ts_labels"][snap_idx]
max_depth = max(selected_depths)
dkey = str(max_depth)

st.subheader(selected_label)
st.caption(
    f"{data['summary']['time_start']} -> {data['summary']['time_end']} | "
    f"{data['summary']['total_snapshots']} source snapshots approx | "
    f"{data['summary']['sampled_snapshots']} sampled | selected {snap_label}"
)

fill = make_fill_rows(snap, side, int(lots), LOT_SIZE, selected_depths)
fill_stats = fill["stats"]
col1, col2 = st.columns(2)
with col1:
    st.markdown("#### Weighted Avg Slippage")
    weighted_value = fill_stats["weighted_slip"] if snap_idx != -1 else data["allday"][side][dkey]["w_slip"]["median"]
    st.metric("Current" if snap_idx != -1 else "Median all day", fmt(weighted_value))
    st.caption("Buy: avg fill - L1 ask. Sell: L1 bid - avg fill.")
    render_iqr_cell("Day weighted slip", data["allday"][side][dkey]["w_slip"])
with col2:
    st.markdown("#### Sweep Slippage")
    sweep_value = fill_stats["sweep_slip"] if snap_idx != -1 else data["allday"][side][dkey]["s_slip"]["median"]
    st.metric("Current" if snap_idx != -1 else "Median all day", fmt(sweep_value))
    st.caption("Buy: last touched ask - L1 ask. Sell: L1 bid - last touched bid.")
    render_iqr_cell("Day sweep slip", data["allday"][side][dkey]["s_slip"])

st.markdown("#### IQR")
i1, i2, i3, i4, i5 = st.columns(5)
with i1:
    render_iqr_cell("Spread all day", data["allday"]["spread"])
with i2:
    render_iqr_cell(f"Weighted slip L{max_depth}", data["allday"][side][dkey]["w_slip"])
with i3:
    render_iqr_cell(f"Sweep slip L{max_depth}", data["allday"][side][dkey]["s_slip"])
with i4:
    render_iqr_cell(f"Fill qty L{max_depth}", data["allday"][side][dkey]["fill"], "L")
with i5:
    render_iqr_cell(f"Min depth {int(lots)}L", data["allday"][f"min_depth_{side}"])

st.markdown("#### Summary")
s1, s2, s3, s4, s5, s6, s7 = st.columns(7)
s1.metric("LTP", fmt(snap["ltp"], 2))
s2.metric("Spread", fmt(snap["spread"]))
s3.metric("Spread IQR", fmt(data["summary"]["spread_iqr"]))
s4.metric(f"Fill L{max_depth}", f"{fill_stats['fill_qty'] / LOT_SIZE:.2f}L")
s5.metric("Weighted Slip", fmt(fill_stats["weighted_slip"]))
s6.metric("Sweep Slip", fmt(fill_stats["sweep_slip"]))
s7.metric("Min Depth", fill_stats["min_depth"] or "-")

marker = [None] * len(data["ltp_series"])
if snap_idx != -1:
    marker[snap_idx] = data["ltp_series"][snap_idx]
chart_panel(
    "LTP",
    line_chart(
        "LTP",
        data["ts_labels"],
        [
            {"name": "LTP", "y": data["ltp_series"]},
            {"name": "Selected", "y": marker, "markers": True, "width": 0, "marker_size": 10},
        ],
    ),
)

spread_stats = data["allday"]["spread"]
chart_panel(
    "Spread with IQR bands",
    line_chart(
        "Spread with IQR bands",
        data["ts_labels"],
        [
            {"name": "Spread", "y": data["spread_series"]},
            {"name": "Median", "y": [spread_stats["median"]] * len(data["ts_labels"])},
            {"name": "Q1", "y": [spread_stats["q1"]] * len(data["ts_labels"]), "dash": "dot"},
            {"name": "Q3", "y": [spread_stats["q3"]] * len(data["ts_labels"]), "dash": "dot"},
            {"name": "Outlier fence", "y": [spread_stats["fence_hi"]] * len(data["ts_labels"]), "dash": "dash"},
        ],
    ),
)

slip_src = data["ask_depth_slip"] if side == "buy" else data["bid_depth_slip"]
chart_panel(
    "Price slippage vs L1",
    bar_chart("Price slippage vs L1", [f"L{level}" for level in selected_depths], [slip_src[level - 1] for level in selected_depths]),
)

source = data["per_level_buy"] if side == "buy" else data["per_level_sell"]
chart_panel(
    "Weighted slippage over time",
    line_chart(
        "Weighted slippage over time",
        data["ts_labels"],
        [{"name": f"L{level}", "y": source[str(level)]["w_slip"]} for level in selected_depths],
    ),
)
chart_panel(
    "Sweep slippage over time",
    line_chart(
        "Sweep slippage over time",
        data["ts_labels"],
        [{"name": f"L{level}", "y": source[str(level)]["s_slip"], "dash": "dash"} for level in selected_depths],
    ),
)

q1, q2 = st.columns(2)
with q1:
    chart_panel(
        "Bid qty over time (lots)",
        line_chart(
            "Bid qty over time (lots)",
            data["ts_labels"],
            [{"name": f"L{level}", "y": data["cum_bid"][str(level)]} for level in selected_depths],
        ),
    )
with q2:
    chart_panel(
        "Ask qty over time (lots)",
        line_chart(
            "Ask qty over time (lots)",
            data["ts_labels"],
            [{"name": f"L{level}", "y": data["cum_ask"][str(level)]} for level in selected_depths],
        ),
    )

chart_panel(
    "Min depth over time",
    line_chart(
        "Min depth over time",
        data["ts_labels"],
        [
            {"name": "Buy", "y": data["min_depth_buy"]},
            {"name": "Sell", "y": data["min_depth_sell"]},
        ],
    ),
)

st.markdown(f"#### Order book ladder @ {snap_label} - selected levels (lots)")
st.dataframe(pd.DataFrame(make_ladder_rows(snap, selected_depths, LOT_SIZE)), use_container_width=True, hide_index=True)

st.markdown(f"#### Fill simulation @ {snap_label} - {side.upper()} {int(lots)} lots via {selected_depths}")
f1, f2, f3, f4, f5, f6 = st.columns(6)
f1.metric("Fill", f"{fill_stats['fill_qty'] / LOT_SIZE:.2f}L")
f2.metric("Unfilled", f"{fill_stats['unfilled'] / LOT_SIZE:.2f}L")
f3.metric("Avg Fill Price", fmt(fill_stats["avg_price"], 4))
f4.metric("L1 Ref", fmt(fill_stats["ref_price"], 4))
f5.metric("Weighted Slip", fmt(fill_stats["weighted_slip"], 4))
f6.metric("Sweep Slip", fmt(fill_stats["sweep_slip"], 4))
st.dataframe(pd.DataFrame(fill["rows"]), use_container_width=True, hide_index=True)
