from __future__ import annotations
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx

def build_overview_metrics(df, alerts):
    return {
        "users": int(df["user_id"].nunique()) if not df.empty else 0,
        "events": int(len(df)),
        "anomalies": int(len(alerts)),
        "high": int((alerts["severity"] == "High").sum()) if not alerts.empty and "severity" in alerts else 0,
    }

def activity_timeline(df):
    if df.empty: return pd.DataFrame(columns=["date", "events"])
    temp = df.copy()
    temp["date"] = pd.to_datetime(temp["timestamp"], errors="coerce").dt.date
    return temp.groupby("date").size().rename("events").reset_index()

def behavior_profile(df, user, alerts):
    subset = df[df["user_id"].astype(str) == str(user)].copy()
    subset["timestamp"] = pd.to_datetime(subset["timestamp"], errors="coerce")
    counts = subset["activity"].value_counts().rename_axis("activity").to_frame("events")
    hours = subset["timestamp"].dt.hour.value_counts().sort_index().rename_axis("hour").to_frame("events")
    flagged = 0
    if not alerts.empty:
        flagged = int((alerts["user_id"].astype(str) == str(user)).sum())
    if subset.empty:
        interpretation = "No activity records are available for this identity."
    else:
        peak = int(subset["timestamp"].dt.hour.mode().iloc[0]) if subset["timestamp"].notna().any() else None
        common = str(subset["activity"].mode().iloc[0]) if not subset["activity"].mode().empty else "unknown"
        interpretation = f"The most frequently recorded action is '{common}'. The most common activity hour is {peak}:00. This profile describes only the records supplied; it should not be treated as a complete employee baseline."
    return {"events": len(subset), "active_days": int(subset["timestamp"].dt.date.nunique()), "flagged": flagged,
            "activity_counts": counts, "hour_counts": hours, "interpretation": interpretation}

def anomaly_histogram(alerts):
    fig = px.histogram(alerts, x="risk_score", nbins=18, title="Risk score distribution", color_discrete_sequence=["#57B8E8"])
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      margin=dict(l=15,r=15,t=55,b=15), height=300,
                      xaxis_title="Relative risk score", yaxis_title="Flagged records")
    return fig

def threat_network(df, alerts):
    # A lightweight graph of users linked to observed activity categories.
    graph = nx.Graph()
    flagged_users = set(alerts["user_id"].astype(str)) if not alerts.empty else set()
    grouped = df.groupby(["user_id", "activity"]).size().reset_index(name="count")
    grouped = grouped.sort_values("count", ascending=False).head(120)
    for _, row in grouped.iterrows():
        u, a = str(row["user_id"]), str(row["activity"])
        graph.add_node(u, kind="user")
        graph.add_node(a, kind="activity")
        graph.add_edge(u, a, weight=int(row["count"]))
    pos = nx.spring_layout(graph, seed=7, k=0.8)
    edge_x, edge_y = [], []
    for u, v in graph.edges():
        x0, y0 = pos[u]; x1, y1 = pos[v]
        edge_x += [x0, x1, None]; edge_y += [y0, y1, None]
    edge_trace = go.Scatter(x=edge_x, y=edge_y, mode="lines", line=dict(width=1, color="#29465E"),
                            hoverinfo="none")
    node_x, node_y, colors, sizes, labels, hover = [], [], [], [], [], []
    for node, attrs in graph.nodes(data=True):
        x, y = pos[node]
        node_x.append(x); node_y.append(y); labels.append(node)
        if attrs.get("kind") == "user":
            colors.append("#F28C68" if node in flagged_users else "#55B8F2")
            sizes.append(17)
            hover.append(f"User: {node}" + ("<br>Has flagged events" if node in flagged_users else ""))
        else:
            colors.append("#6DC9B2"); sizes.append(12); hover.append(f"Activity: {node}")
    node_trace = go.Scatter(x=node_x, y=node_y, mode="markers+text", text=labels, textposition="top center",
        hovertext=hover, hoverinfo="text", marker=dict(size=sizes, color=colors, line=dict(width=1, color="#D8E8F2")))
    fig = go.Figure([edge_trace, node_trace])
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=620, margin=dict(l=10,r=10,t=20,b=10), showlegend=False,
        xaxis=dict(visible=False), yaxis=dict(visible=False))
    return fig

def create_incident_report(df, alerts, last_run):
    generated = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
    high = int((alerts["severity"] == "High").sum()) if "severity" in alerts else 0
    users = alerts["user_id"].nunique() if not alerts.empty else 0
    lines = [
        "# SENTINEL — Investigation Summary", "",
        f"- Generated: {generated}", f"- Detection run: {last_run or 'Not recorded'}",
        f"- Input activity records: {len(df)}", f"- Identities in input: {df['user_id'].nunique() if not df.empty else 0}",
        f"- Flagged events: {len(alerts)}", f"- High-severity review signals: {high}",
        f"- Identities with flagged events: {users}", "",
        "## Interpretation", "",
        "This report summarises the output of an unsupervised Isolation Forest run. A flagged event is an anomaly candidate, not proof of insider threat or malicious intent. Human investigation and contextual validation are required.", "",
        "## Highest-ranked events", "",
        "| Timestamp | User | Activity | Device | Risk score | Severity |",
        "|---|---|---|---|---:|---|",
    ]
    for _, r in alerts.head(25).iterrows():
        lines.append(f"| {r.get('timestamp','')} | {r.get('user_id','')} | {r.get('activity','')} | {r.get('device','')} | {r.get('risk_score','')} | {r.get('severity','')} |")
    lines += ["", "## Limitations", "",
        "- Results depend on the quality and coverage of the supplied activity records.",
        "- The model is unsupervised and may generate false positives and false negatives.",
        "- Synthetic demonstration data is not evidence of real-world threat prevalence.",
        "- This educational prototype is not a production security monitoring system.", ""]
    return "\n".join(lines)

import pandas as pd


def user_risk_table(data, *args, **kwargs):
    """
    Creates a user-level risk summary from activity records.
    Compatible with common SENTINEL activity and anomaly columns.
    """

    if data is None:
        return pd.DataFrame(
            columns=[
                "User",
                "Total Activities",
                "Suspicious Activities",
                "Risk Score",
                "Risk Level"
            ]
        )

    if not isinstance(data, pd.DataFrame):
        data = pd.DataFrame(data)

    if data.empty:
        return pd.DataFrame(
            columns=[
                "User",
                "Total Activities",
                "Suspicious Activities",
                "Risk Score",
                "Risk Level"
            ]
        )

    df = data.copy()

    user_col = next(
        (c for c in ["user", "user_id", "employee", "employee_id"]
         if c in df.columns),
        None
    )

    if user_col is None:
        return pd.DataFrame(
            columns=[
                "User",
                "Total Activities",
                "Suspicious Activities",
                "Risk Score",
                "Risk Level"
            ]
        )

    anomaly_col = next(
        (c for c in ["is_anomaly", "anomaly", "suspicious", "flagged"]
         if c in df.columns),
        None
    )

    score_col = next(
        (c for c in ["risk_score", "anomaly_score", "score"]
         if c in df.columns),
        None
    )

    if anomaly_col:
        suspicious = df[anomaly_col].astype(str).str.lower().isin(
            ["true", "1", "yes", "anomaly", "suspicious", "-1"]
        )
        if pd.api.types.is_numeric_dtype(df[anomaly_col]):
            suspicious = df[anomaly_col].isin([-1, 1])
    else:
        suspicious = pd.Series(False, index=df.index)

    df["_suspicious"] = suspicious.astype(int)

    if score_col:
        scores = pd.to_numeric(df[score_col], errors="coerce")
        if scores.notna().any():
            df["_risk"] = scores.fillna(0)
            if df["_risk"].min() < 0:
                df["_risk"] = (
                    df["_risk"] - df["_risk"].min()
                )
            maximum = df["_risk"].max()
            if maximum > 1:
                df["_risk"] = df["_risk"] / maximum
            df["_risk"] = df["_risk"].clip(0, 1) * 100
        else:
            df["_risk"] = df["_suspicious"] * 100
    else:
        df["_risk"] = df["_suspicious"] * 100

    result = (
        df.groupby(user_col)
        .agg(
            **{
                "Total Activities": (user_col, "size"),
                "Suspicious Activities": ("_suspicious", "sum"),
                "Risk Score": ("_risk", "mean")
            }
        )
        .reset_index()
        .rename(columns={user_col: "User"})
    )

    result["Risk Score"] = result["Risk Score"].round(2)

    result["Risk Level"] = result["Risk Score"].apply(
        lambda score:
            "Critical" if score >= 80 else
            "High" if score >= 60 else
            "Medium" if score >= 30 else
            "Low"
    )

    return result.sort_values(
        by="Risk Score",
        ascending=False
    ).reset_index(drop=True)
