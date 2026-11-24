from __future__ import annotations

from pathlib import Path
from typing import Any
import io
import re

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASETS_DIR = PROJECT_ROOT / "datasets"
UPLOADS_DIR = DATASETS_DIR / "imported"

CERT_LOGS = {
    "logon": "Login and logout activity",
    "device": "USB and removable-device activity",
    "file": "File access and file operations",
    "email": "Email activity",
    "http": "Web browsing activity",
    "ldap": "Employee and organisational directory information",
}

ALIASES = {
    "logon": ("logon", "login", "logins"),
    "device": ("device", "usb", "removable"),
    "file": ("file", "files", "filesystem"),
    "email": ("email", "mail"),
    "http": ("http", "web", "browser", "browsing"),
    "ldap": ("ldap", "employee", "user_directory"),
}


def _safe_name(name: str) -> str:
    name = Path(name).name
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    return name[:120] or "uploaded.csv"


def identify_log_type(filename: str) -> str:
    stem = Path(filename).stem.lower()
    for kind, aliases in ALIASES.items():
        if any(alias in stem for alias in aliases):
            return kind
    return "custom"


def discover_local_datasets(root: Path | str | None = None) -> list[dict[str, Any]]:
    """Find CSV files in datasets/ without assuming a particular CERT folder layout."""
    folder = Path(root) if root else DATASETS_DIR
    if not folder.exists():
        return []

    found = []
    for path in sorted(folder.rglob("*.csv")):
        if "imported" in path.parts:
            source = "Uploaded"
        else:
            source = "Local dataset"
        found.append({
            "name": path.name,
            "path": path,
            "relative_path": str(path.relative_to(folder)),
            "log_type": identify_log_type(path.name),
            "source": source,
        })
    return found


def read_csv_file(file_or_path: Any) -> pd.DataFrame:
    """Read an uploaded file or local CSV with practical encoding fallbacks."""
    if isinstance(file_or_path, (str, Path)):
        path = Path(file_or_path)
        raw = path.read_bytes()
        label = path.name
    else:
        raw = file_or_path.getvalue()
        label = getattr(file_or_path, "name", "uploaded.csv")

    errors = []
    for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return pd.read_csv(io.BytesIO(raw), encoding=encoding, low_memory=False)
        except Exception as exc:
            errors.append(f"{encoding}: {exc}")

    raise ValueError(
        f"Could not read {label} as a CSV file. "
        + " | ".join(errors[-2:])
    )


def inspect_dataframe(df: pd.DataFrame) -> dict[str, Any]:
    """Return data-quality information without modifying the source dataframe."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Expected a pandas DataFrame.")

    missing_cells = int(df.isna().sum().sum()) if not df.empty else 0
    total_cells = int(df.shape[0] * df.shape[1])
    duplicate_rows = int(df.duplicated().sum()) if not df.empty else 0

    return {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "missing_cells": missing_cells,
        "missing_percent": round((missing_cells / total_cells) * 100, 2) if total_cells else 0.0,
        "duplicate_rows": duplicate_rows,
        "column_names": list(map(str, df.columns)),
        "dtypes": {str(col): str(dtype) for col, dtype in df.dtypes.items()},
    }


def save_uploaded_csv(uploaded_file, destination: Path | str | None = None) -> Path:
    folder = Path(destination) if destination else UPLOADS_DIR
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / _safe_name(uploaded_file.name)
    # Avoid silently overwriting an earlier upload.
    if target.exists():
        stem, suffix = target.stem, target.suffix
        counter = 2
        while (folder / f"{stem}_{counter}{suffix}").exists():
            counter += 1
        target = folder / f"{stem}_{counter}{suffix}"
    target.write_bytes(uploaded_file.getvalue())
    return target


def set_active_dataset(df: pd.DataFrame, name: str, source: str = "Unknown") -> None:
    """Store the selected dataframe for other SENTINEL pages in this session."""
    st.session_state["sentinel_active_dataset"] = df.copy()
    st.session_state["sentinel_active_dataset_name"] = name
    st.session_state["sentinel_active_dataset_source"] = source


def get_active_dataset() -> pd.DataFrame | None:
    """Get the currently selected dataset from Streamlit session state."""
    return st.session_state.get("sentinel_active_dataset")


def render_dataset_manager() -> None:
    """Render SENTINEL's Dataset Manager page."""
    st.markdown(
        """
        <style>
        .dm-hero {
            padding: 1.35rem 1.5rem;
            border: 1px solid rgba(80,150,255,.22);
            border-radius: 18px;
            background: linear-gradient(120deg, rgba(31,74,130,.28), rgba(20,184,166,.08));
            margin-bottom: 1rem;
        }
        .dm-hero h2 { margin: 0 0 .35rem 0; }
        .dm-muted { opacity: .72; font-size: .92rem; }
        div[data-testid="stMetric"] {
            border: 1px solid rgba(128,128,128,.18);
            padding: 12px 14px;
            border-radius: 14px;
            background: rgba(128,128,128,.035);
        }
        </style>
        <div class="dm-hero">
          <h2>Dataset Manager</h2>
          <div class="dm-muted">Import, inspect and select activity logs before behavioural analysis.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    DATASETS_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    active = get_active_dataset()
    active_name = st.session_state.get("sentinel_active_dataset_name", "No dataset selected")
    active_source = st.session_state.get("sentinel_active_dataset_source", "—")

    a, b, c = st.columns(3)
    a.metric("Local CSV files", len(discover_local_datasets()))
    b.metric("Active dataset rows", f"{len(active):,}" if active is not None else "—")
    c.metric("Current source", active_source)

    st.subheader("1. Import a dataset")
    upload_tab, local_tab = st.tabs(["Upload CSV files", "Load from datasets folder"])

    with upload_tab:
        uploads = st.file_uploader(
            "Choose one or more CSV files",
            type=["csv"],
            accept_multiple_files=True,
            help="You can upload CERT log files or your own activity CSV files.",
            key="sentinel_dataset_upload",
        )
        if uploads:
            for uploaded in uploads:
                try:
                    df = read_csv_file(uploaded)
                    saved_path = save_uploaded_csv(uploaded)
                    st.success(f"Imported {uploaded.name}: {len(df):,} rows × {len(df.columns)} columns.")
                    if st.button(f"Use {uploaded.name} as active dataset", key=f"use_upload_{uploaded.name}"):
                        set_active_dataset(df, uploaded.name, "Manual upload")
                        st.rerun()
                    with st.expander(f"Preview {uploaded.name}", expanded=False):
                        st.dataframe(df.head(15), use_container_width=True)
                        st.caption(f"Saved locally to: {saved_path.relative_to(PROJECT_ROOT)}")
                except Exception as exc:
                    st.error(f"Could not import {uploaded.name}: {exc}")

    with local_tab:
        st.caption(f"Place downloaded CSV files anywhere inside: `{DATASETS_DIR}`")
        st.caption("CERT folders are supported recursively; the app looks for logon, device, file, email, http and LDAP CSV files.")
        files = discover_local_datasets()
        if not files:
            st.info("No local CSV files found yet. Create a datasets folder and add your dataset CSV files.")
        else:
            options = {
                f"{item['relative_path']}  ·  {item['log_type'].upper()}": item
                for item in files
            }
            selected_label = st.selectbox("Select a local CSV file", list(options.keys()))
            selected = options[selected_label]
            if st.button("Load selected dataset", type="primary"):
                try:
                    df = read_csv_file(selected["path"])
                    set_active_dataset(df, selected["name"], selected["source"])
                    st.success(f"Loaded {selected['name']} successfully.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not load dataset: {exc}")

    st.divider()
    st.subheader("2. Active dataset")
    active = get_active_dataset()
    if active is None:
        st.info("No active dataset selected. Import a CSV or load one from the datasets folder.")
        return

    active_name = st.session_state.get("sentinel_active_dataset_name", "Selected dataset")
    active_source = st.session_state.get("sentinel_active_dataset_source", "Unknown")
    st.markdown(f"**{active_name}**  ·  {active_source}")

    quality = inspect_dataframe(active)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Rows", f"{quality['rows']:,}")
    m2.metric("Columns", quality["columns"])
    m3.metric("Missing values", f"{quality['missing_cells']:,}")
    m4.metric("Duplicate rows", f"{quality['duplicate_rows']:,}")

    with st.expander("Data preview", expanded=True):
        st.dataframe(active.head(30), use_container_width=True, height=360)

    with st.expander("Column information"):
        schema = pd.DataFrame({
            "Column": list(quality["dtypes"].keys()),
            "Data type": list(quality["dtypes"].values()),
            "Missing values": [int(active[col].isna().sum()) for col in active.columns],
        })
        st.dataframe(schema, use_container_width=True, hide_index=True)

    if quality["missing_cells"]:
        st.warning(
            f"This dataset contains {quality['missing_cells']:,} missing cells "
            f"({quality['missing_percent']}%). Review these before model training."
        )
    else:
        st.success("No missing cells detected in the active dataset.")

    st.download_button(
        "Download active dataset as CSV",
        data=active.to_csv(index=False).encode("utf-8"),
        file_name=f"{Path(active_name).stem}_export.csv",
        mime="text/csv",
    )

    if st.button("Clear active dataset", type="secondary"):
        for key in (
            "sentinel_active_dataset",
            "sentinel_active_dataset_name",
            "sentinel_active_dataset_source",
        ):
            st.session_state.pop(key, None)
        st.rerun()

    st.divider()
    st.subheader("3. CERT dataset guide")
    st.write(
        "SENTINEL recognises common CERT activity log filenames. "
        "Keep the original CSV files unchanged and load each log separately. "
        "The answer-key/ground-truth file should be kept separate from model input "
        "and used only for evaluation."
    )
    guide = pd.DataFrame(
        [{"Log file": f"{name}.csv", "Contents": description} for name, description in CERT_LOGS.items()]
    )
    st.dataframe(guide, use_container_width=True, hide_index=True)
    st.caption(
        "This manager imports and inspects files. Dataset-specific feature engineering "
        "and evaluation must be performed by the detection pipeline before claiming results."
    )
