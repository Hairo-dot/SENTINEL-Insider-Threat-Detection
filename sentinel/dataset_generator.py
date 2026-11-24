from __future__ import annotations

import numpy as np
import pandas as pd


SCENARIOS = {
    "After-hours activity": "after_hours",
    "Bulk file downloads": "bulk_download",
    "External USB usage": "external_usb",
    "Sensitive resource access": "sensitive_access",
}


def generate_workforce_dataset(
    employees: int = 500,
    days: int = 90,
    anomaly_employee_percent: int = 5,
    scenarios: list[str] | None = None,
    seed: int = 42,
) -> pd.DataFrame:
    """Generate reproducible, clearly-labelled synthetic workforce events.

    Labels are retained as ground truth for evaluation only. They are not used
    by SENTINEL's Isolation Forest feature extraction.
    """
    if employees < 10:
        raise ValueError("Generate at least 10 employees.")
    if days < 7:
        raise ValueError("Choose at least 7 days.")
    if not 0 <= anomaly_employee_percent <= 30:
        raise ValueError("The anomaly employee percentage must be between 0 and 30.")

    rng = np.random.default_rng(seed)
    selected = [SCENARIOS[name] for name in (scenarios or list(SCENARIOS)) if name in SCENARIOS]
    if not selected:
        raise ValueError("Select at least one suspicious activity scenario.")

    departments = ["Engineering", "Finance", "Human Resources", "Operations", "Research", "Sales"]
    actions = ["login", "logout", "file_access", "file_download", "email_sent", "web_access"]
    action_weights = [0.17, 0.14, 0.29, 0.08, 0.13, 0.19]
    resources = ["shared_drive", "project_docs", "public_web", "team_workspace", "source_code", "finance", "hr_records"]
    resource_weights = [0.25, 0.20, 0.18, 0.15, 0.10, 0.07, 0.05]
    start = pd.Timestamp.now().normalize() - pd.Timedelta(days=days)
    employee_ids = [f"EMP{i:04d}" for i in range(1, employees + 1)]
    anomaly_count = max(1, round(employees * anomaly_employee_percent / 100)) if anomaly_employee_percent else 0
    anomaly_users = set(rng.choice(employee_ids, size=anomaly_count, replace=False).tolist()) if anomaly_count else set()

    profiles = {}
    for user in employee_ids:
        profiles[user] = {
            "department": str(rng.choice(departments)),
            "device": f"WS-{int(rng.integers(1, max(10, employees // 5))):03d}",
            "usual_hour": float(rng.normal(10.5, 1.6)),
        }

    rows = []
    counter = 0
    # Approximately 50,000 baseline events for 500 employees over 90 days.
    for user in employee_ids:
        profile = profiles[user]
        for day in range(days):
            count = int(rng.poisson(1.1))
            for _ in range(count):
                counter += 1
                hour = int(np.clip(rng.normal(profile["usual_hour"], 2.0), 7, 20))
                minute = int(rng.integers(0, 60))
                rows.append({
                    "event_id": f"SYN-{counter:08d}",
                    "timestamp": start + pd.Timedelta(days=day, hours=hour, minutes=minute),
                    "user_id": user,
                    "activity": str(rng.choice(actions, p=action_weights)),
                    "device": profile["device"],
                    "resource": str(rng.choice(resources, p=resource_weights)),
                    "label": "normal",
                })

    # Add scenario-specific events for a small subset of synthetic identities.
    scenario_actions = {
        "after_hours": ("file_access", "source_code"),
        "bulk_download": ("file_download", "shared_drive"),
        "external_usb": ("usb_connect", "source_code"),
        "sensitive_access": ("file_access", "finance"),
    }
    for user in sorted(anomaly_users):
        profile = profiles[user]
        chosen = list(rng.choice(selected, size=min(len(selected), 2), replace=False))
        for scenario in chosen:
            action, resource = scenario_actions[scenario]
            event_count = int(rng.integers(7, 13))
            for j in range(event_count):
                counter += 1
                if scenario == "after_hours":
                    hour = int(rng.choice([0, 1, 2, 3, 23]))
                else:
                    hour = int(rng.integers(8, 19))
                day_offset = int(rng.integers(max(0, days - 14), days))
                rows.append({
                    "event_id": f"SYN-{counter:08d}",
                    "timestamp": start + pd.Timedelta(days=day_offset, hours=hour, minutes=int(rng.integers(0, 60))),
                    "user_id": user,
                    "activity": action,
                    "device": f"EXT-{user[-4:]}" if scenario == "external_usb" else profile["device"],
                    "resource": resource,
                    "label": "anomaly",
                })

    result = pd.DataFrame(rows).sort_values("timestamp").reset_index(drop=True)
    return result
