
from __future__ import annotations

import streamlit as st

from sentinel.config import APP_NAME, APP_SUBTITLE, PAGE_ORDER


# ============================================================
# GLOBAL DESIGN SYSTEM
# ============================================================

def inject_global_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700;800&display=swap');

        :root {
            --bg: #080e18;
            --panel: #101a29;
            --panel2: #142135;
            --border: rgba(148, 174, 207, 0.14);
            --text: #eaf2fc;
            --muted: #91a3b9;
            --blue: #55b8f2;
            --cyan: #58c4b8;
            --purple: #9b91f4;
            --red: #f47783;
            --green: #62d6a5;
        }

        html, body, [class*="css"] {
            font-family: 'DM Sans', sans-serif;
        }

        .stApp {
            background:
                radial-gradient(ellipse at 10% 0%, rgba(42, 105, 160, 0.12), transparent 35%),
                radial-gradient(ellipse at 90% 10%, rgba(79, 74, 150, 0.10), transparent 35%),
                var(--bg);
            color: var(--text);
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        [data-testid="stSidebar"] {
            background: #0b1422;
            border-right: 1px solid var(--border);
        }

        [data-testid="stSidebar"] > div:first-child {
            padding-top: 1.5rem;
        }

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
            color: var(--muted);
        }

        [data-testid="stSidebar"] .stRadio label {
            color: #c8d6e8;
            font-size: 0.91rem;
            padding: 5px 0;
        }

        [data-testid="stSidebar"] .stRadio label:hover {
            color: var(--blue);
        }

        .block-container {
            max-width: 1500px;
            padding-top: 2.2rem;
            padding-bottom: 3rem;
        }

        h1, h2, h3, h4 {
            color: var(--text);
            letter-spacing: -0.035em;
        }

        p, li {
            color: #b3c2d5;
        }

        .page-kicker {
            color: var(--cyan);
            font-family: 'DM Mono', monospace;
            font-size: 0.69rem;
            letter-spacing: 0.16em;
            font-weight: 500;
            margin-bottom: 0.55rem;
        }

        .page-title {
            font-size: clamp(2rem, 4vw, 2.8rem);
            font-weight: 800;
            line-height: 1.1;
            margin: 0 0 0.65rem 0;
            color: #f1f6ff;
        }

        .page-subtitle {
            color: var(--muted);
            font-size: 0.98rem;
            max-width: 850px;
            line-height: 1.7;
            margin-bottom: 1.8rem;
        }

        .metric-card {
            position: relative;
            overflow: hidden;
            background: linear-gradient(145deg, #142338, #0e1928);
            border: 1px solid var(--border);
            border-radius: 15px;
            padding: 21px 21px 19px;
            min-height: 145px;
            transition: transform 0.25s ease,
                        border-color 0.25s ease,
                        box-shadow 0.25s ease;
        }

        .metric-card:hover {
            transform: translateY(-5px);
            border-color: rgba(85, 184, 242, 0.48);
            box-shadow: 0 12px 32px rgba(0, 0, 0, 0.24);
        }

        .metric-card::after {
            content: "";
            position: absolute;
            width: 110px;
            height: 110px;
            right: -45px;
            top: -45px;
            border-radius: 50%;
            background: rgba(85, 184, 242, 0.07);
            pointer-events: none;
        }

        .metric-label {
            color: #8fa4bd;
            font-family: 'DM Mono', monospace;
            font-size: 0.68rem;
            letter-spacing: 0.12em;
            margin-bottom: 12px;
        }

        .metric-value {
            color: #f2f7ff;
            font-size: clamp(1.35rem, 2.2vw, 1.9rem);
            font-weight: 800;
            letter-spacing: -0.04em;
            overflow-wrap: anywhere;
            line-height: 1.2;
        }

        .metric-note {
            color: #8499b2;
            font-size: 0.77rem;
            margin-top: 9px;
            line-height: 1.5;
        }

        .metric-icon {
            position: absolute;
            right: 19px;
            bottom: 17px;
            color: rgba(85, 184, 242, 0.55);
            font-size: 1.3rem;
            transition: transform 0.3s ease;
        }

        .metric-card:hover .metric-icon {
            transform: rotate(-10deg) scale(1.2);
        }

        .section-heading {
            margin-top: 1.7rem;
            margin-bottom: 0.9rem;
        }

        .section-title {
            color: #eaf2fc;
            font-size: 1.12rem;
            font-weight: 700;
            margin-bottom: 3px;
        }

        .section-caption {
            color: #8499b2;
            font-size: 0.81rem;
        }

        .callout {
            background: linear-gradient(110deg, rgba(48, 123, 171, 0.15), rgba(52, 91, 139, 0.08));
            border: 1px solid rgba(85, 184, 242, 0.22);
            border-radius: 12px;
            padding: 17px 20px;
            margin: 1rem 0 1.4rem;
            color: #b8cce0;
            line-height: 1.65;
            font-size: 0.88rem;
        }

        .callout b {
            color: #eaf5ff;
        }

        .status-panel {
            background: #122438;
            border: 1px solid rgba(98, 214, 165, 0.22);
            border-radius: 13px;
            padding: 19px;
            margin: 0.6rem 0 1rem;
        }

        .status-panel b {
            color: #e7f8f1;
        }

        .status-panel p {
            font-size: 0.85rem;
            margin: 9px 0;
        }

        .status-panel small {
            color: #8da6b8;
        }

        .status-panel.muted {
            border-color: var(--border);
            background: #111c2b;
        }

        .status-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            background: var(--green);
            border-radius: 50%;
            margin-right: 9px;
            box-shadow: 0 0 12px rgba(98, 214, 165, 0.6);
            animation: pulse 1.8s infinite;
        }

        .status-dot.idle {
            background: #8393a8;
            box-shadow: none;
            animation: none;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.35; }
        }

        .algorithm-card {
            display: flex;
            align-items: center;
            gap: 20px;
            padding: 22px;
            background: linear-gradient(120deg, #14263b, #111b2b);
            border: 1px solid var(--border);
            border-radius: 15px;
            margin-bottom: 1.2rem;
            transition: border-color 0.25s ease,
                        transform 0.25s ease;
        }

        .algorithm-card:hover {
            border-color: rgba(155, 145, 244, 0.5);
            transform: translateY(-3px);
        }

        .algorithm-symbol {
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            width: 58px;
            height: 58px;
            border-radius: 15px;
            background: rgba(155, 145, 244, 0.14);
            border: 1px solid rgba(155, 145, 244, 0.3);
            color: #c5bdff;
            font-weight: 800;
            font-size: 1.2rem;
        }

        .algorithm-card h3 {
            margin: 0 0 6px 0;
        }

        .algorithm-card p {
            margin: 0;
            line-height: 1.6;
            font-size: 0.88rem;
        }

        .replay-banner {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 20px;
            padding: 22px 25px;
            border: 1px solid var(--border);
            border-radius: 15px;
            background: linear-gradient(110deg, #14263a, #111a2b);
            margin: 1rem 0 1.3rem;
        }

        .replay-banner h2 {
            margin: 0;
        }

        .replay-banner p {
            margin: 5px 0 0;
            font-size: 0.84rem;
        }

        .replay-count {
            font-size: 2rem;
            font-weight: 800;
            color: #f47783;
            text-align: center;
        }

        .replay-count small {
            display: block;
            color: #94a7bb;
            font-size: 0.7rem;
            font-weight: 500;
        }

        .alert-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            padding: 15px 18px;
            margin: 9px 0;
            border: 1px solid var(--border);
            border-radius: 11px;
            background: #111d2c;
            transition: border-color 0.2s ease,
                        transform 0.2s ease;
        }

        .alert-row:hover {
            border-color: rgba(244, 119, 131, 0.45);
            transform: translateX(3px);
        }

        .alert-row p {
            margin: 5px 0;
            font-size: 0.78rem;
        }

        .alert-row small {
            color: #9aacc0;
        }

        .risk-pill {
            color: #ffabb2;
            background: rgba(244, 119, 131, 0.12);
            border: 1px solid rgba(244, 119, 131, 0.25);
            border-radius: 30px;
            padding: 5px 11px;
            font-size: 0.7rem;
            white-space: nowrap;
        }

        .result-count {
            color: #91a3b9;
            font-size: 0.84rem;
            margin: 12px 0;
        }

        .result-count b {
            color: #eaf2fc;
        }

        .footer {
            text-align: center;
            color: #62758d;
            font-family: 'DM Mono', monospace;
            font-size: 0.67rem;
            letter-spacing: 0.08em;
            padding: 35px 0 10px;
            border-top: 1px solid var(--border);
            margin-top: 45px;
        }

        .stButton > button {
            border-radius: 9px;
            border: 1px solid rgba(85, 184, 242, 0.3);
            background: linear-gradient(110deg, #17618c, #245b91);
            color: white;
            font-weight: 600;
            transition: all 0.22s ease;
        }

        .stButton > button:hover {
            border-color: #75ccff;
            box-shadow: 0 5px 20px rgba(38, 139, 204, 0.2);
            transform: translateY(-2px);
            color: white;
        }

        .stDownloadButton > button {
            border-radius: 9px;
            background: #142338;
            color: #d9e9fa;
            border: 1px solid var(--border);
            transition: all 0.2s ease;
        }

        .stDownloadButton > button:hover {
            border-color: var(--blue);
            color: white;
        }

        [data-testid="stDataFrame"],
        [data-testid="stTable"] {
            border: 1px solid var(--border);
            border-radius: 10px;
            overflow: hidden;
        }

        [data-testid="stExpander"] {
            border: 1px solid var(--border);
            border-radius: 10px;
            background: rgba(17, 29, 44, 0.65);
        }

        [data-testid="stMetric"] {
            background: #111e2e;
            border: 1px solid var(--border);
            padding: 13px;
            border-radius: 10px;
        }

        [data-testid="stAlert"] {
            border-radius: 10px;
        }

        input, textarea {
            color: var(--text) !important;
        }

        @media (max-width: 700px) {
            .block-container {
                padding: 1.2rem 1rem 2rem;
            }

            .metric-card {
                min-height: 125px;
            }

            .replay-banner {
                padding: 17px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

def render_sidebar():
    with st.sidebar:
        st.markdown(
            """
            <div style="padding: 0 4px 20px;">
                <div style="
                    display:flex;
                    align-items:center;
                    gap:11px;
                    margin-bottom:12px;
                ">
                    <div style="
                        width:42px;
                        height:42px;
                        display:flex;
                        align-items:center;
                        justify-content:center;
                        border-radius:12px;
                        background:linear-gradient(135deg,#17618c,#514b9c);
                        font-size:21px;
                        box-shadow:0 5px 20px rgba(55,130,190,.2);
                    ">🛡️</div>
                    <div>
                        <div style="
                            font-size:1.22rem;
                            font-weight:800;
                            color:#edf5ff;
                            letter-spacing:.06em;
                        ">SENTINEL</div>
                        <div style="
                            color:#7f98b3;
                            font-size:.65rem;
                            letter-spacing:.12em;
                        ">THREAT INTELLIGENCE</div>
                    </div>
                </div>
                <div style="
                    height:1px;
                    background:rgba(148,174,207,.14);
                    margin:15px 0;
                "></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div style="
                color:#7189a4;
                font-family:monospace;
                font-size:.65rem;
                letter-spacing:.14em;
                margin:0 0 10px 5px;
            ">WORKSPACE NAVIGATION</div>
            """,
            unsafe_allow_html=True,
        )

        pages = list(PAGE_ORDER)

        if not pages:
            pages = ["Command Centre"]

        if "active_page" not in st.session_state:
            st.session_state.active_page = pages[0]

        if st.session_state.active_page not in pages:
            st.session_state.active_page = pages[0]

        selected = st.radio(
            "Navigation",
            pages,
            index=pages.index(st.session_state.active_page),
            label_visibility="collapsed",
            key="sentinel_navigation",
        )

        st.session_state.active_page = selected

        st.markdown(
            """
            <div style="
                margin-top:35px;
                padding:15px;
                border:1px solid rgba(148,174,207,.13);
                border-radius:11px;
                background:rgba(17,29,44,.65);
            ">
                <div style="
                    color:#58c4b8;
                    font-family:monospace;
                    font-size:.64rem;
                    letter-spacing:.12em;
                ">SYSTEM STATUS</div>
                <div style="
                    display:flex;
                    align-items:center;
                    gap:8px;
                    margin-top:10px;
                    color:#d9e9f8;
                    font-size:.82rem;
                ">
                    <span style="
                        height:7px;
                        width:7px;
                        border-radius:50%;
                        background:#62d6a5;
                        box-shadow:0 0 10px #62d6a5;
                    "></span>
                    Interface operational
                </div>
                <div style="
                    color:#7189a4;
                    font-size:.7rem;
                    margin-top:6px;
                ">Local analysis workspace</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div style="
                color:#647990;
                font-size:.65rem;
                text-align:center;
                margin-top:25px;
            ">SENTINEL · EDUCATIONAL PROTOTYPE</div>
            """,
            unsafe_allow_html=True,
        )

    return selected


# ============================================================
# METRIC CARDS
# ============================================================

def metric_card(label, value, note="", symbol=""):
    """
    Display a metric card.

    Supports integers, floats, strings and other values.
    Numeric values receive comma formatting.
    Text values are converted safely to strings.
    """

    if value is None:
        display_value = "—"

    elif isinstance(value, bool):
        display_value = "Yes" if value else "No"

    elif isinstance(value, int):
        display_value = f"{value:,}"

    elif isinstance(value, float):
        if value.is_integer():
            display_value = f"{int(value):,}"
        else:
            display_value = f"{value:,.2f}"

    else:
        display_value = str(value)

    safe_label = str(label)
    safe_note = str(note)
    safe_symbol = str(symbol)

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{safe_label}</div>
            <div class="metric-value">{display_value}</div>
            <div class="metric-note">{safe_note}</div>
            <div class="metric-icon">{safe_symbol}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# SECTION HEADINGS
# ============================================================

def section_heading(title, caption=""):
    safe_title = str(title)
    safe_caption = str(caption)

    st.markdown(
        f"""
        <div class="section-heading">
            <div class="section-title">{safe_title}</div>
            <div class="section-caption">{safe_caption}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# EMPTY STATES
# ============================================================

def empty_state(title, message):
    safe_title = str(title)
    safe_message = str(message)

    st.markdown(
        f"""
        <div style="
            display:flex;
            flex-direction:column;
            align-items:center;
            justify-content:center;
            text-align:center;
            min-height:175px;
            padding:28px 20px;
            background:rgba(17,29,44,.55);
            border:1px dashed rgba(148,174,207,.25);
            border-radius:14px;
            margin:12px 0 20px;
        ">
            <div style="
                font-size:1.8rem;
                margin-bottom:12px;
                opacity:.8;
            ">◈</div>
            <div style="
                color:#e5effb;
                font-size:1rem;
                font-weight:700;
                margin-bottom:7px;
            ">{safe_title}</div>
            <div style="
                color:#8da1b9;
                font-size:.83rem;
                max-width:520px;
                line-height:1.6;
            ">{safe_message}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
