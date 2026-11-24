from __future__ import annotations

import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
import io

from sentinel.config import APP_NAME, APP_SUBTITLE, PAGE_ORDER
from sentinel.data import load_demo_data, normalize_activity_data, save_uploaded_data, detect_column_mapping
from sentinel.dataset_generator import generate_workforce_dataset, SCENARIOS
from sentinel.database import initialize_database, save_alerts, load_feedback, save_feedback
from sentinel.detection import run_detection
from sentinel.ui import inject_global_css, render_sidebar, metric_card, section_heading, empty_state
from sentinel.analytics import (
    build_overview_metrics, user_risk_table, activity_timeline,
    behavior_profile, create_incident_report
)

st.set_page_config(
    page_title=f"{APP_NAME} | Insider Threat Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

initialize_database()
inject_global_css()

if "activity_df" not in st.session_state:
    st.session_state.activity_df = load_demo_data()
if "alerts_df" not in st.session_state:
    st.session_state.alerts_df = pd.DataFrame()
if "selected_user" not in st.session_state:
    st.session_state.selected_user = None
if "last_run" not in st.session_state:
    st.session_state.last_run = None
if "dataset_source" not in st.session_state:
    st.session_state.dataset_source = "Built-in demonstration dataset"
if "dataset_name" not in st.session_state:
    st.session_state.dataset_name = "18 employees · 28 days"

page = render_sidebar()
df = st.session_state.activity_df.copy()
alerts = st.session_state.alerts_df.copy()

def render_header(kicker: str, title: str, subtitle: str):
    st.markdown(f'<div class="page-kicker">{kicker}</div><h1 class="page-title">{title}</h1><p class="page-subtitle">{subtitle}</p>', unsafe_allow_html=True)

def run_model():
    with st.spinner("Analysing behavioural patterns and scoring unusual activity..."):
        detected, summary = run_detection(st.session_state.activity_df)
        st.session_state.alerts_df = detected
        st.session_state.last_run = datetime.now().strftime("%d %b %Y · %H:%M")
        if not detected.empty:
            save_alerts(detected, input_events=len(st.session_state.activity_df))
    return summary

if page == "Command Centre":
    render_header("SECURITY OPERATIONS / OVERVIEW", "Command Centre", "A live-style overview of user activity, behavioural deviations and investigation priorities.")
    metrics = build_overview_metrics(df, alerts)
    cols = st.columns(4, gap="medium")
    labels = [
        ("USERS MONITORED", metrics["users"], "Unique identities in the activity feed", "users"),
        ("ACTIVITY EVENTS", metrics["events"], "Records currently available for analysis", "activity"),
        ("OPEN ANOMALIES", metrics["anomalies"], "Alerts from the latest detection run", "alerts"),
        ("HIGH PRIORITY", metrics["high"], "Alerts requiring closer review", "priority"),
    ]
    for col, item in zip(cols, labels):
        with col:
            metric_card(item[0], item[1], item[2], item[3])

    st.markdown("")
    left, right = st.columns([1.65, 1], gap="large")
    with left:
        section_heading("Activity intelligence", "Recorded events across the selected dataset")
        timeline = activity_timeline(df)
        if not timeline.empty:
            st.line_chart(timeline.set_index("date")["events"], height=250, color="#55B8F2")
        else:
            empty_state("No activity data", "Import a CSV dataset or load the built-in demonstration data.")
    with right:
        section_heading("Detection status", "Current analysis state")
        if st.session_state.last_run:
            st.markdown(f'<div class="status-panel"><span class="status-dot"></span><b>Analysis completed</b><p>Last run: {st.session_state.last_run}</p><small>Isolation Forest · behavioural feature analysis</small></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-panel muted"><span class="status-dot idle"></span><b>Awaiting analysis</b><p>Run detection to identify activity that differs from learned behaviour.</p><small>Detection results will appear across the workspace.</small></div>', unsafe_allow_html=True)
        if st.button("▶  Run anomaly detection", type="primary", use_container_width=True):
            summary = run_model()
            st.success(f"Analysis complete. {summary['anomalies']} events flagged from {summary['events']} records.")
            st.rerun()

    section_heading("Investigation queue", "Latest flagged events")
    if alerts.empty:
        empty_state("No detection results yet", "Run anomaly detection to populate the investigation queue. This is not a claim that the environment is threat-free.")
    else:
        show = alerts.sort_values("risk_score", ascending=False).head(7)
        display_cols = [c for c in ["timestamp", "user_id", "activity", "risk_score", "severity", "explanation"] if c in show.columns]
        st.dataframe(show[display_cols], use_container_width=True, hide_index=True)

elif page == "Behaviour DNA":
    render_header("IDENTITY INTELLIGENCE", "Behaviour DNA", "Build a baseline for each identity and inspect how their activity differs from their own patterns.")
    users = sorted(df["user_id"].dropna().astype(str).unique().tolist())
    if not users:
        empty_state("No users available", "Load activity records to create behavioural profiles.")
    else:
        selected = st.selectbox("Select an identity", users, index=users.index(st.session_state.selected_user) if st.session_state.selected_user in users else 0)
        st.session_state.selected_user = selected
        profile = behavior_profile(df, selected, alerts)
        a, b, c = st.columns(3)
        with a: metric_card("TOTAL EVENTS", profile["events"], "Observed activity records", "activity")
        with b: metric_card("ACTIVE DAYS", profile["active_days"], "Distinct days represented", "calendar")
        with c: metric_card("FLAGGED EVENTS", profile["flagged"], "Events flagged in the latest run", "alerts")
        l, r = st.columns([1.15, 1], gap="large")
        with l:
            section_heading("Activity fingerprint", "Distribution of recorded actions")
            if not profile["activity_counts"].empty:
                st.bar_chart(profile["activity_counts"], height=290, color="#58C4B8")
        with r:
            section_heading("Typical activity hours", "When this identity is usually active")
            if not profile["hour_counts"].empty:
                st.bar_chart(profile["hour_counts"], height=290, color="#8B9CF6")
        section_heading("Profile interpretation", "Observed patterns, not a judgement of intent")
        st.info(profile["interpretation"])
        st.caption("A behavioural baseline is descriptive. A deviation is a signal for review, not proof of malicious intent.")

elif page == "Detection Lab":
    render_header("MODEL WORKSPACE", "Detection Lab", "Run unsupervised anomaly detection against the currently loaded activity records.")
    st.markdown('<div class="callout"><b>How this works</b><br/>Isolation Forest learns patterns from the available activity features and assigns an anomaly score. It does not determine intent, and flagged events require human review.</div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("#### Detection configuration")
        c1, c2, c3 = st.columns(3)
        with c1:
            contamination = st.slider("Expected anomaly fraction", 0.01, 0.20, 0.05, 0.01, help="A modelling assumption controlling how many observations the model is expected to flag.")
        with c2:
            estimators = st.select_slider("Number of trees", options=[50, 100, 150, 200, 300], value=150)
        with c3:
            st.metric("Input records", f"{len(df):,}")
        if st.button("Run Isolation Forest", type="primary", use_container_width=True):
            with st.spinner("Fitting model and scoring events..."):
                detected, summary = run_detection(df, contamination=contamination, n_estimators=estimators)
                st.session_state.alerts_df = detected
                st.session_state.last_run = datetime.now().strftime("%d %b %Y · %H:%M")
                if not detected.empty:
                    save_alerts(detected, input_events=len(st.session_state.activity_df))
            st.success(f"Finished: {summary['anomalies']} flagged events out of {summary['events']} analysed.")
            evaluation = summary.get("label_evaluation")
            if evaluation:
                st.markdown("#### Ground-truth evaluation")
                if "note" in evaluation:
                    st.info(evaluation["note"])
                else:
                    e1, e2, e3, e4 = st.columns(4)
                    e1.metric("Precision", f"{evaluation['precision']:.1%}")
                    e2.metric("Recall", f"{evaluation['recall']:.1%}")
                    e3.metric("F1 score", f"{evaluation['f1_score']:.1%}")
                    e4.metric("Accuracy", f"{evaluation['accuracy']:.1%}")
                    st.caption(f"Evaluation used {evaluation['labelled_events']:,} labelled events. Labels were not included in model features.")
    if not alerts.empty:
        section_heading("Model output", "Distribution of anomaly scores")
        st.plotly_chart(__import__("sentinel.analytics", fromlist=["anomaly_histogram"]).anomaly_histogram(alerts), use_container_width=True)
        st.caption("Scores rank unusual records within this model run. They are not calibrated probabilities or proof of malicious intent.")
        section_heading("Flagged records", "Review the model's highest-scoring deviations")
        st.dataframe(alerts.sort_values("risk_score", ascending=False), use_container_width=True, hide_index=True)
    else:
        empty_state("No model output yet", "Configure the model and run detection to generate scored events.")

elif page == "Threat Map":
    render_header("RELATIONSHIP ANALYSIS", "Threat Map", "Explore connections between identities, devices and activity types in the loaded records.")
    if df.empty:
        empty_state("No graph data available", "Load an activity dataset first.")
    else:
        from sentinel.analytics import threat_network
        fig = threat_network(df, alerts)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("The map visualises co-occurrence relationships present in the records. A connection does not establish causation or collusion.")
        section_heading("Relationship evidence", "Most frequently observed user–activity pairs")
        counts = df.groupby(["user_id", "activity"]).size().reset_index(name="events").sort_values("events", ascending=False).head(20)
        st.dataframe(counts, use_container_width=True, hide_index=True)

elif page == "Incident Replay":
    render_header("INCIDENT INVESTIGATION", "Incident Replay", "Step through a user's recorded activity in chronological order and inspect why events were flagged.")
    if df.empty:
        empty_state("No activity to replay", "Load records to create an investigation timeline.")
    else:
        users = sorted(df["user_id"].dropna().astype(str).unique().tolist())
        selected = st.selectbox("Identity to investigate", users, key="replay_user")
        user_events = df[df["user_id"].astype(str) == selected].copy().sort_values("timestamp")
        if not alerts.empty:
            flagged = set(alerts.loc[alerts["user_id"].astype(str) == selected, "event_id"].astype(str))
            user_events["detection_status"] = user_events["event_id"].astype(str).apply(lambda x: "Flagged" if x in flagged else "Baseline")
        else:
            user_events["detection_status"] = "Not analysed"
        st.markdown(f'<div class="replay-banner"><div><span class="page-kicker">IDENTITY TIMELINE</span><h2>{selected}</h2><p>{len(user_events)} chronological events</p></div><div class="replay-count">{int((user_events["detection_status"] == "Flagged").sum())}<small>flagged</small></div></div>', unsafe_allow_html=True)
        st.dataframe(user_events[["timestamp", "activity", "device", "resource", "detection_status"]], use_container_width=True, hide_index=True)
        if not alerts.empty:
            user_alerts = alerts[alerts["user_id"].astype(str) == selected].sort_values("risk_score", ascending=False)
            if not user_alerts.empty:
                section_heading("Investigation notes", "Why the model highlighted these events")
                for _, row in user_alerts.head(10).iterrows():
                    st.markdown(f'<div class="alert-row"><div><b>{row.get("activity","Activity")}</b><p>{row.get("timestamp","")} · {row.get("device","Unknown device")}</p><small>{row.get("explanation","Unusual feature combination")}</small></div><span class="risk-pill">{row.get("severity","Review")}</span></div>', unsafe_allow_html=True)
                section_heading("Analyst review", "Record a human decision for an individual flagged event")
                with st.form("analyst_review_form"):
                    event_options = user_alerts["event_id"].astype(str).tolist()
                    chosen_event = st.selectbox("Flagged event", event_options)
                    decision = st.selectbox("Review outcome", ["Needs investigation", "Expected / benign", "Confirmed suspicious"])
                    notes = st.text_area("Review notes", placeholder="Add context or evidence for this decision.")
                    submitted = st.form_submit_button("Save review decision", type="primary")
                    if submitted:
                        save_feedback(chosen_event, decision, notes)
                        st.success("Review decision saved to the local SQLite database.")
                review_history = load_feedback()
                if not review_history.empty:
                    st.markdown("#### Recent analyst decisions")
                    st.dataframe(review_history.head(20), use_container_width=True, hide_index=True)

elif page == "Activity Explorer":
    render_header("ACTIVITY FORENSICS", "Activity Explorer", "Search, filter and inspect the records currently loaded into SENTINEL.")
    if df.empty:
        empty_state("No records available", "Import a CSV file from Data & Sources.")
    else:
        c1, c2, c3 = st.columns([1.2, 1, 1])
        with c1:
            search = st.text_input("Search user, action, device or resource", placeholder="e.g. EMP004 or USB")
        with c2:
            actions = ["All"] + sorted(df["activity"].dropna().astype(str).unique().tolist())
            action_filter = st.selectbox("Activity type", actions)
        with c3:
            user_filter = st.selectbox("User", ["All"] + sorted(df["user_id"].dropna().astype(str).unique().tolist()))
        filtered = df.copy()
        if search:
            mask = filtered.astype(str).apply(lambda col: col.str.contains(search, case=False, na=False)).any(axis=1)
            filtered = filtered[mask]
        if action_filter != "All": filtered = filtered[filtered["activity"] == action_filter]
        if user_filter != "All": filtered = filtered[filtered["user_id"].astype(str) == user_filter]
        st.markdown(f'<div class="result-count">Showing <b>{len(filtered):,}</b> of {len(df):,} records</div>', unsafe_allow_html=True)
        st.dataframe(filtered, use_container_width=True, hide_index=True)
        st.download_button("Download filtered CSV", filtered.to_csv(index=False).encode("utf-8"), "sentinel_filtered_activity.csv", "text/csv")

elif page == "Data & Sources":
    render_header("DATA MANAGEMENT", "Data & Sources", "Import external activity logs, map unfamiliar CSV schemas, or generate a controlled 500-employee synthetic workforce.")

    current_source = st.session_state.get("dataset_source", "Built-in demonstration dataset")
    current_name = st.session_state.get("dataset_name", "Built-in demonstration dataset")
    st.markdown(
        f'<div class="callout"><b>Active source:</b> {current_source} · <b>Dataset:</b> {current_name}<br>'
        'Imported data is normalised into one event schema. Ground-truth labels, when present, are retained for evaluation and excluded from Isolation Forest features.</div>',
        unsafe_allow_html=True,
    )

    import_tab, synthetic_tab, active_tab = st.tabs(
        ["CSV Importer", "Synthetic Generator", "Current Dataset"]
    )

    with import_tab:
        st.markdown("#### Universal CSV importer")
        st.write("Upload a CSV from a research dataset or your own source. SENTINEL will suggest column matches and let you correct them before importing.")
        uploaded = st.file_uploader(
            "Choose a CSV file",
            type=["csv"],
            key="sentinel_universal_csv",
            help="CSV files with different column names can be mapped manually.",
        )
        if uploaded is not None:
            raw = None
            read_errors = []
            raw_bytes = uploaded.getvalue()
            for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
                try:
                    raw = pd.read_csv(io.BytesIO(raw_bytes), encoding=encoding, low_memory=False)
                    raw.columns = [str(column) for column in raw.columns]
                    break
                except Exception as exc:
                    read_errors.append(f"{encoding}: {exc}")
            if raw is None:
                st.error("Could not read this CSV. " + " | ".join(read_errors[-2:]))
            elif raw.empty:
                st.error("The uploaded CSV has no data rows.")
            else:
                detected = detect_column_mapping(raw.columns)
                st.success(f"File read successfully: {len(raw):,} rows · {len(raw.columns)} columns")
                st.caption("Suggested matches are best-effort. Check the mapping carefully, especially for research datasets with specialised schemas.")
                with st.expander("Source preview and detected headings", expanded=True):
                    st.dataframe(raw.head(8), use_container_width=True, hide_index=True)
                    st.write("**Suggested mapping**")
                    st.json({k: (str(v) if v is not None else "Not detected") for k, v in detected.items()})

                available = ["(not available)"] + [str(c) for c in raw.columns]
                def mapping_index(field):
                    candidate = detected.get(field)
                    try:
                        return available.index(str(candidate)) if candidate is not None else 0
                    except ValueError:
                        return 0

                with st.form("sentinel_csv_mapping_form"):
                    st.markdown("**Confirm or change column mapping**")
                    m1, m2 = st.columns(2)
                    with m1:
                        user_col = st.selectbox("User / employee identity *", available, index=mapping_index("user_id"))
                        activity_col = st.selectbox("Activity / action *", available, index=mapping_index("activity"))
                        time_col = st.selectbox("Timestamp", available, index=mapping_index("timestamp"))
                    with m2:
                        device_col = st.selectbox("Device / host", available, index=mapping_index("device"))
                        resource_col = st.selectbox("Resource / target", available, index=mapping_index("resource"))
                        label_col = st.selectbox("Ground-truth label (evaluation only)", available, index=mapping_index("label"))
                    submitted = st.form_submit_button("Normalise and import dataset", type="primary", use_container_width=True)

                if submitted:
                    mapping = {
                        "user_id": user_col,
                        "activity": activity_col,
                        "timestamp": time_col,
                        "device": device_col,
                        "resource": resource_col,
                        "label": label_col,
                    }
                    try:
                        normalised = normalize_activity_data(raw, mapping)
                        st.session_state.activity_df = normalised
                        st.session_state.alerts_df = pd.DataFrame()
                        st.session_state.last_run = None
                        st.session_state.dataset_source = "External CSV import"
                        st.session_state.dataset_name = uploaded.name
                        save_uploaded_data(normalised)
                        st.success(
                            f"Imported {len(normalised):,} events from {uploaded.name}. "
                            f"{normalised['user_id'].nunique():,} unique identities detected."
                        )
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Import could not be completed: {exc}")

        st.info("Required fields: user identity and activity/action. Timestamp, device, resource and label are optional. Missing optional values receive safe defaults.")

    with synthetic_tab:
        st.markdown("#### Synthetic workforce generator")
        st.write("Create a repeatable demonstration dataset with 500 fictional employees and selectable unusual-activity scenarios.")
        with st.form("sentinel_synthetic_form"):
            st.caption("Employee count is fixed at 500 fictional identities for the project demonstration profile.")
            g1, g2 = st.columns(2)
            with g1:
                days_count = st.slider("Activity history (days)", min_value=30, max_value=180, value=90, step=15)
            with g2:
                anomaly_percent = st.slider("Employees with injected scenarios (%)", min_value=1, max_value=15, value=5)
            employee_count = 500
            selected_scenarios = st.multiselect(
                "Include suspicious activity scenarios",
                options=list(SCENARIOS.keys()),
                default=list(SCENARIOS.keys()),
            )
            seed_value = st.number_input("Random seed", min_value=1, max_value=999999, value=42, step=1)
            generate_clicked = st.form_submit_button("Generate 500-employee dataset", type="primary", use_container_width=True)

        if generate_clicked:
            try:
                generated = generate_workforce_dataset(
                    employees=int(employee_count),
                    days=int(days_count),
                    anomaly_employee_percent=int(anomaly_percent),
                    scenarios=selected_scenarios,
                    seed=int(seed_value),
                )
                st.session_state.activity_df = generated
                st.session_state.alerts_df = pd.DataFrame()
                st.session_state.last_run = None
                st.session_state.dataset_source = "SENTINEL synthetic generator"
                st.session_state.dataset_name = f"500 employees · {days_count} days · seed {seed_value}"
                save_uploaded_data(generated)
                st.success(
                    f"Generated {len(generated):,} events for "
                    f"{generated['user_id'].nunique():,} fictional employees. "
                    f"{int((generated['label'] == 'anomaly').sum()):,} events carry synthetic scenario labels."
                )
                st.rerun()
            except Exception as exc:
                st.error(f"Could not generate dataset: {exc}")

        st.caption("All identities and events are fictional. The label column is ground truth for demonstration/evaluation only; it is not passed into model training.")

    with active_tab:
        active = st.session_state.activity_df.copy()
        section_heading("Active dataset", f"{len(active):,} events · {active['user_id'].nunique() if not active.empty else 0} identities")
        if not active.empty:
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Events", f"{len(active):,}")
            k2.metric("Identities", f"{active['user_id'].nunique():,}")
            k3.metric("Date range", f"{(pd.to_datetime(active['timestamp']).max() - pd.to_datetime(active['timestamp']).min()).days + 1} days")
            k4.metric("Label field", "Available" if "label" in active.columns else "Not provided")
            st.dataframe(active.head(100), use_container_width=True, hide_index=True)
            st.download_button(
                "Download current dataset",
                active.to_csv(index=False).encode("utf-8"),
                "sentinel_activity_data.csv",
                "text/csv",
                use_container_width=True,
            )
        else:
            empty_state("No activity data", "Import a CSV or generate a synthetic dataset to begin.")
        if st.button("Restore original small demo dataset", use_container_width=True):
            st.session_state.activity_df = load_demo_data()
            st.session_state.alerts_df = pd.DataFrame()
            st.session_state.last_run = None
            st.session_state.dataset_source = "Built-in demonstration dataset"
            st.session_state.dataset_name = "18 employees · 28 days"
            save_uploaded_data(st.session_state.activity_df)
            st.rerun()

elif page == "Reports":
    render_header("REPORTING & EVIDENCE", "Investigation Reports", "Create a concise, downloadable summary of the current detection run and supporting evidence.")
    if alerts.empty:
        empty_state("No investigation report yet", "Run detection first. Reports are generated from actual records and the latest model output.")
    else:
        report = create_incident_report(df, alerts, st.session_state.last_run)
        st.markdown(report)
        st.download_button("Download investigation report (.md)", report.encode("utf-8"), "sentinel_investigation_report.md", "text/markdown")
        st.download_button("Download flagged events (.csv)", alerts.to_csv(index=False).encode("utf-8"), "sentinel_flagged_events.csv", "text/csv")

elif page == "Model Centre":
    render_header("MODEL GOVERNANCE", "Model Centre", "Understand the current detection method, its assumptions and its limitations.")
    section_heading("Active algorithm", "Isolation Forest")
    st.markdown('<div class="algorithm-card"><div class="algorithm-symbol">IF</div><div><h3>Isolation Forest</h3><p>An unsupervised tree-based algorithm that isolates observations. Unusual combinations of activity features tend to be isolated with fewer splits.</p></div></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: metric_card("LEARNING MODE", "Unsupervised", "Does not require attack labels to fit", "brain")
    with c2: metric_card("FEATURES", "Behavioural", "Hour, action, device, resource and frequency", "layers")
    with c3: metric_card("OUTPUT", "Anomaly score", "A review signal, not a verdict", "target")
    section_heading("Responsible interpretation", "What this model can and cannot tell you")
    st.markdown("""
    - **Can:** rank events that differ from the patterns represented in the input data.
    - **Cannot:** prove malicious intent, establish motive, or guarantee that unflagged activity is safe.
    - **Depends on:** data quality, feature coverage, baseline duration, contamination setting and the organisation's context.
    - **Requires:** human review, documented decisions and careful handling of employee data.
    """)
    st.warning("This project is an educational analytics prototype. It is not a production security monitoring or employee disciplinary system.")

elif page == "System Guide":
    render_header("DOCUMENTATION", "System Guide", "A plain-language guide to the application, its workflow and the Python concepts used.")
    sections = [
        ("01 · Data ingestion", "CSV records are loaded and normalised into a consistent event schema. Missing optional fields receive safe defaults."),
        ("02 · Behavioural features", "Events are converted into numerical features such as event hour, activity category, device category and resource category."),
        ("03 · Anomaly detection", "Isolation Forest learns the distribution of the feature vectors and assigns anomaly scores. Higher risk scores indicate stronger deviation within this run."),
        ("04 · Investigation", "Flagged records are enriched with a readable explanation based on unusual event context and are available in the Threat Map and Incident Replay."),
        ("05 · Feedback and reporting", "Analysts can export evidence and record a review outcome. A human review is important because anomaly detection can produce false positives."),
    ]
    for title, body in sections:
        with st.expander(title, expanded=False):
            st.write(body)
    section_heading("Project implementation", "Python concepts demonstrated")
    st.markdown("""
    - Modular programming and reusable functions
    - Object-oriented design through data and detection components
    - Lists, dictionaries, sets and data structures
    - CSV and file handling with validation and exception handling
    - Pandas data cleaning and transformation
    - Scikit-learn model training and evaluation
    - SQLite persistence for review feedback
    - Interactive data visualisation with Plotly and Streamlit
    """)
    st.caption("Dataset integration is intentionally kept configurable. The built-in sample is synthetic and clearly identified as such.")

st.markdown('<div class="footer">SENTINEL · Educational insider-threat analytics prototype · Handle workforce data responsibly.</div>', unsafe_allow_html=True)
