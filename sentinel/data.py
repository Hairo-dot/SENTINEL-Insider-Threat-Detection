from __future__ import annotations

import uuid
from pathlib import Path

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = ["event_id", "timestamp", "user_id", "activity", "device", "resource"]

ALIASES = {
    "timestamp": ["timestamp", "date", "datetime", "time", "date_time", "event_time", "created_at", "occurred_at"],
    "user_id": ["user_id", "user", "employee", "employee_id", "username", "actor", "userid", "person", "account", "user_name"],
    "activity": ["activity", "action", "event", "event_type", "activity_type", "operation", "event_name", "activity_name", "command"],
    "device": ["device", "device_id", "host", "computer", "machine", "hostname", "workstation", "endpoint"],
    "resource": ["resource", "file", "object", "target", "resource_name", "file_name", "url", "destination"],
    "label": ["label", "insider", "is_malicious", "ground_truth", "class", "is_anomaly", "malicious", "scenario_label"],
}


def _find_column(columns, candidates):
    lookup = {str(c).strip().lower().replace(" ", "_"): c for c in columns}
    for candidate in candidates:
        if candidate in lookup:
            return lookup[candidate]
    return None


def detect_column_mapping(columns) -> dict:
    """Best-effort mapping from arbitrary CSV headings to SENTINEL's event schema."""
    return {
        target: _find_column(columns, aliases)
        for target, aliases in ALIASES.items()
    }


def normalize_activity_data(raw: pd.DataFrame, column_mapping: dict | None = None) -> pd.DataFrame:
    """Convert a user CSV into SENTINEL's common event schema.

    user_id and activity are the only mandatory source fields. Other fields receive
    explicit safe defaults. Any source label is retained for evaluation only;
    the detection feature builder does not use it.
    """
    if raw is None or raw.empty:
        raise ValueError("The uploaded CSV contains no rows.")
    raw = raw.copy()
    detected = detect_column_mapping(raw.columns)
    if column_mapping:
        for target, source in column_mapping.items():
            if source == "(not available)" or source is None or source == "":
                detected[target] = None
            else:
                detected[target] = source

    for required in ("user_id", "activity"):
        source = detected.get(required)
        if not source or source not in raw.columns:
            raise ValueError(
                f"Could not map the required '{required}' field. "
                "Choose the matching source column in the manual mapping controls."
            )

    n = len(raw)
    now = pd.Timestamp.now().floor("s")
    timestamp_source = detected.get("timestamp")
    if timestamp_source and timestamp_source in raw.columns:
        timestamps = pd.to_datetime(raw[timestamp_source], errors="coerce")
        # Missing or invalid timestamps are filled in a stable sequence, not discarded.
        fallback = pd.Series(
            [now - pd.Timedelta(seconds=n - i) for i in range(n)],
            index=raw.index,
        )
        timestamps = timestamps.fillna(fallback)
    else:
        timestamps = pd.Series(
            [now - pd.Timedelta(seconds=n - i) for i in range(n)],
            index=raw.index,
        )

    def source_values(target, default):
        source = detected.get(target)
        if source and source in raw.columns:
            values = raw[source]
        else:
            values = pd.Series([default] * n, index=raw.index)
        return values.fillna(default).astype(str).replace({"": default, "nan": default, "None": default})

    event_id = raw["event_id"].astype(str) if "event_id" in raw.columns else pd.Series(
        [f"IMP-{uuid.uuid4().hex[:12].upper()}" for _ in range(n)], index=raw.index
    )
    out = pd.DataFrame({
        "event_id": event_id.values,
        "timestamp": pd.to_datetime(timestamps).values,
        "user_id": source_values("user_id", "unknown").values,
        "activity": source_values("activity", "unknown").str.strip().str.lower().values,
        "device": source_values("device", "unknown").values,
        "resource": source_values("resource", "unknown").values,
    })
    label_source = detected.get("label")
    if label_source and label_source in raw.columns:
        out["label"] = raw[label_source].fillna("unknown").astype(str).values
    out = out[out["user_id"].astype(str).str.strip().ne("")]
    out = out[out["activity"].astype(str).str.strip().ne("")]
    if out.empty:
        raise ValueError("No usable rows remain after normalisation.")
    return out.sort_values("timestamp").reset_index(drop=True)


def load_demo_data(seed: int = 17, users: int = 18, days: int = 28) -> pd.DataFrame:
    """Create reproducible synthetic activity records; not real employee data."""
    rng = np.random.default_rng(seed)
    names = [f"EMP{i:03d}" for i in range(1, users + 1)]
    activities = ["login", "logout", "file_access", "file_download", "email_sent", "web_access", "usb_connect"]
    weights = [0.18, 0.15, 0.25, 0.10, 0.13, 0.16, 0.03]
    devices = [f"WS-{i:02d}" for i in range(1, 13)]
    resources = ["shared_drive", "project_docs", "finance", "hr_records", "source_code", "public_web"]
    start = pd.Timestamp.now().normalize() - pd.Timedelta(days=days)
    records = []
    event_no = 0
    for user in names:
        user_device = rng.choice(devices)
        for day in range(days):
            count = int(rng.integers(5, 14))
            for _ in range(count):
                event_no += 1
                hour = int(np.clip(rng.normal(10.5, 2.4), 7, 19))
                minute = int(rng.integers(0, 60))
                ts = start + pd.Timedelta(days=day, hours=hour, minutes=minute)
                action = str(rng.choice(activities, p=weights))
                resource = str(rng.choice(resources, p=[.25, .2, .08, .08, .19, .2]))
                records.append({
                    "event_id": f"EVT-{event_no:06d}", "timestamp": ts, "user_id": user,
                    "activity": action, "device": user_device if rng.random() < .94 else str(rng.choice(devices)),
                    "resource": resource,
                })
    for user in ["EMP003", "EMP011", "EMP016"]:
        for offset in range(7):
            event_no += 1
            ts = start + pd.Timedelta(days=days - 1, hours=1 + offset // 3, minutes=offset * 7)
            records.append({
                "event_id": f"EVT-{event_no:06d}", "timestamp": ts, "user_id": user,
                "activity": "usb_connect" if offset % 2 == 0 else "file_download",
                "device": f"EXT-{user[-3:]}",
                "resource": "finance" if user == "EMP011" else "source_code",
            })
    return pd.DataFrame(records).sort_values("timestamp").reset_index(drop=True)


def save_uploaded_data(df: pd.DataFrame):
    path = Path("data") / "current_activity.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
