from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import OrdinalEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer

def _feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    ts = pd.to_datetime(data["timestamp"], errors="coerce")
    features = pd.DataFrame(index=data.index)
    features["hour"] = ts.dt.hour.fillna(12)
    features["weekday"] = ts.dt.dayofweek.fillna(2)
    features["is_weekend"] = (features["weekday"] >= 5).astype(int)
    features["activity"] = data["activity"].fillna("unknown").astype(str).str.lower()
    features["device"] = data["device"].fillna("unknown").astype(str)
    features["resource"] = data["resource"].fillna("unknown").astype(str)
    # User-level event rate and rarity are computed within the submitted dataset.
    user_counts = data.groupby("user_id")["event_id"].transform("count")
    features["user_event_volume"] = np.log1p(user_counts.astype(float))
    activity_freq = data["activity"].astype(str).value_counts(normalize=True)
    features["activity_rarity"] = data["activity"].astype(str).map(lambda x: -np.log(max(float(activity_freq.get(x, 1e-6)), 1e-6)))
    return features

def _explain(row: pd.Series) -> str:
    reasons = []
    hour = int(row.get("hour", 12))
    if hour < 6 or hour >= 22:
        reasons.append("activity occurred outside common daytime hours")
    if str(row.get("activity", "")).lower() in {"usb_connect", "file_download", "bulk_copy", "mass_download"}:
        reasons.append("activity type can warrant review in context")
    if str(row.get("device", "")).lower().startswith(("ext", "usb", "unknown")):
        reasons.append("device identifier is external or unavailable")
    if str(row.get("resource", "")).lower() in {"finance", "hr_records", "source_code"}:
        reasons.append("resource category may be sensitive")
    return "; ".join(reasons) if reasons else "unusual combination of behavioural features compared with this dataset"

def run_detection(df: pd.DataFrame, contamination: float = 0.05, n_estimators: int = 150):
    if df is None or len(df) < 10:
        raise ValueError("At least 10 activity records are required to fit the model.")
    data = df.copy().reset_index(drop=True)
    features = _feature_frame(data)
    numeric = ["hour", "weekday", "is_weekend", "user_event_volume", "activity_rarity"]
    categorical = ["activity", "device", "resource"]
    transformer = ColumnTransformer([
        ("numeric", Pipeline([("imputer", SimpleImputer(strategy="median"))]), numeric),
        ("categorical", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)),
        ]), categorical),
    ])
    matrix = transformer.fit_transform(features)
    model = IsolationForest(
        n_estimators=int(n_estimators),
        contamination=float(contamination),
        random_state=42,
        n_jobs=-1,
    )
    prediction = model.fit_predict(matrix)
    raw_score = -model.score_samples(matrix)
    low, high = float(raw_score.min()), float(raw_score.max())
    scaled = (raw_score - low) / (high - low) if high > low else np.zeros_like(raw_score)
    data["anomaly"] = prediction == -1
    data["anomaly_score"] = raw_score
    data["risk_score"] = np.round(scaled * 100, 1)
    data["severity"] = pd.cut(
        data["risk_score"], bins=[-0.01, 49.99, 74.99, 100.01],
        labels=["Low", "Medium", "High"], include_lowest=True
    ).astype(str)
    data["explanation"] = [
        _explain(features.iloc[i]) if data.loc[i, "anomaly"] else "Not flagged by this model run; absence of an alert is not proof of safety."
        for i in range(len(data))
    ]
    alerts = data[data["anomaly"]].copy().sort_values("risk_score", ascending=False).reset_index(drop=True)
    summary = {
        "events": int(len(data)),
        "anomalies": int(data["anomaly"].sum()),
        "users": int(data["user_id"].nunique()),
    }
    label_metrics = evaluate_if_labels_available(data)
    if label_metrics is not None:
        summary["label_evaluation"] = label_metrics
    return alerts, summary


def evaluate_if_labels_available(scored_data: pd.DataFrame):
    """Evaluate predictions against recognised labels without using labels as features."""
    if scored_data is None or scored_data.empty or "label" not in scored_data.columns:
        return None
    values = scored_data["label"].astype(str).str.strip().str.lower()
    positive_values = {"1", "true", "yes", "malicious", "insider", "positive", "anomaly", "abnormal"}
    negative_values = {"0", "false", "no", "normal", "benign", "negative", "legitimate"}
    recognised = values.isin(positive_values | negative_values)
    if not recognised.any():
        return {"note": "A label column exists, but its values were not recognised. Map labels to normal/1 and anomaly/0-style values before evaluation."}
    truth = values[recognised].isin(positive_values)
    if truth.nunique() < 2:
        return {"note": "Both normal and anomalous ground-truth classes are required for precision/recall evaluation."}
    predicted = scored_data.loc[recognised, "anomaly"].astype(bool)
    tp = int((predicted & truth).sum())
    fp = int((predicted & ~truth).sum())
    fn = int((~predicted & truth).sum())
    tn = int((~predicted & ~truth).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    accuracy = (tp + tn) / (tp + fp + fn + tn) if tp + fp + fn + tn else 0.0
    return {
        "labelled_events": int(recognised.sum()),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "true_negatives": tn,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1_score": round(f1, 3),
        "accuracy": round(accuracy, 3),
    }
