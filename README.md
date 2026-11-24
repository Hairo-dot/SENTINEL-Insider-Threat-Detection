# SENTINEL — Anomaly-Based Insider Threat Detection

SENTINEL is an educational Python application that explores insider-threat detection through user behaviour analytics. It uses Streamlit for the interface, Pandas for data handling, Scikit-learn's Isolation Forest for unsupervised anomaly detection, Plotly/NetworkX for visual analytics, and SQLite for local review records.

> **Important:** The built-in and generated records are synthetic demonstration data. This project is not a production security monitoring tool and its alerts are not proof of malicious intent.

## Features

- Command Centre overview
- Behaviour DNA user profiles
- Isolation Forest Detection Lab
- User–activity relationship graph
- Chronological Incident Replay
- Searchable Activity Explorer
- Universal CSV importer with automatic column suggestions and manual mapping
- Synthetic workforce generator for 500 fictional employees
- Configurable 30–180 day history and suspicious-activity scenarios
- Ground-truth label-aware evaluation (labels are excluded from model features)
- Downloadable investigation summary and dataset export
- Model explanation and limitations guide
- Local SQLite persistence for detection-run summaries and analyst review decisions

## Requirements

- Python 3.10 or newer
- Internet access during first dependency installation (to install packages)
- Windows, macOS or Linux

## Run on Windows

1. Extract the ZIP.
2. Open PowerShell in the extracted `SENTINEL_Insider_Threat_Detection` folder.
3. Create a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

4. Install dependencies:

   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. Start the app:

   ```powershell
   streamlit run app.py
   ```

6. Open the local URL printed in the terminal (normally `http://localhost:8501`).

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

## First-time walkthrough

1. Open **Data & Sources**.
2. Use **Synthetic Generator** to create the 500-employee demonstration dataset, or import a CSV using **CSV Importer**.
3. Check the active dataset in **Current Dataset**.
4. Open **Detection Lab** and run Isolation Forest.
5. Explore **Behaviour DNA**, **Threat Map**, and **Incident Replay**.
6. Download the dataset or investigation summary when needed.

## Universal CSV importer

The importer makes best-effort suggestions for these fields and provides manual mapping when column names differ:

| SENTINEL field | Recognised examples |
|---|---|
| timestamp | timestamp, date, datetime, time, event_time |
| user_id | user_id, user, employee, employee_id, username, actor |
| activity | activity, action, event, event_type, operation, command |
| device | device, device_id, host, computer, machine, hostname |
| resource | resource, file, object, target, file_name, url |
| label (optional) | label, insider, is_malicious, ground_truth, class |

Only user identity and activity/action are required. Timestamp, device and resource fields are optional and receive safe defaults when absent. The importer cannot automatically infer the meaning of every research dataset: inspect the preview and confirm the mapping before importing. CERT-style datasets may contain several separate event files; each log needs an appropriate mapping and potentially dataset-specific preprocessing.

### Ground-truth labels

If a recognised label column is mapped, SENTINEL retains it for a separate evaluation after detection. The label is not used by the Isolation Forest feature builder. Supported positive values include `1`, `true`, `malicious`, `insider`, `anomaly` and `abnormal`; supported negative values include `0`, `false`, `normal`, `benign` and `legitimate`. Other label vocabularies need preprocessing or a manual mapping to these classes.

## Synthetic generator

The generator creates 500 fictional employee identities, a selectable 30–180 day event history, and optional injected scenarios:
- After-hours activity
- Bulk file downloads
- External USB usage
- Sensitive resource access

The default is 90 days and 5% of employees receiving injected scenarios. A random seed makes a generated dataset reproducible. The output includes a `label` column (`normal` / `anomaly`) for evaluation. It is synthetic ground truth, not a claim that the model should detect every injected event.

## Detection methodology

The application creates event-level features including hour, weekday, weekend indicator, activity category, device, resource, per-user event volume and activity rarity. Categorical features are encoded and Isolation Forest ranks unusual combinations.

The `risk_score` is a min-max scaled anomaly score within the current run. It is **not** a calibrated probability of threat. The contamination parameter is a modelling assumption, not an estimate of actual insider-threat prevalence. If a labelled dataset is imported, precision, recall, F1 and accuracy are calculated after model fitting against recognised labels; these metrics are not fed into training.

## Known limitations

- Synthetic data does not represent real organisational activity.
- The universal importer standardises common event schemas; it does not replace dataset-specific feature engineering.
- Multi-file datasets (such as separate login, device, file and email logs) may require preprocessing or separate imports.
- The graph displays co-occurrence relationships, not causal links.
- The model can produce false positives and false negatives.
- Metrics depend on correct ground-truth mapping, class balance and dataset quality.
- Review feedback is stored locally in SQLite; it is not yet used for automated model retraining.

## Privacy and safety

Use only data you are authorised to process. Minimise personal information, secure the project folder, and avoid uploading real employee records to public repositories. Do not commit private datasets, database files, credentials or identifiable information to GitHub.

## GitHub

Before publishing:
- Keep private or licensed datasets out of the repository.
- Check the dataset licence and citation requirements.
- Review `.gitignore`.
- Do not commit `data/sentinel.sqlite3` or uploaded activity files.
- Add screenshots only after capturing the actual running application.

## Academic honesty

Describe the generated sample as synthetic. Do not claim real-world detection performance or CERT dataset integration unless those steps have actually been completed and evaluated.
