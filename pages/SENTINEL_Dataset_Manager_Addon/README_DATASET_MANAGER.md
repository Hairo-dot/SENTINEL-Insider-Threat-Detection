# SENTINEL Dataset Manager add-on

This add-on provides the dataset-handling choice agreed for SENTINEL:

1. **Automatic local loading**: searches recursively for CSV files inside `datasets/`.
2. **Manual upload**: accepts one or more CSV files through the Streamlit interface.
3. **Synthetic demo data**: does not replace or delete your existing synthetic-data generator.

## Installation

1. Extract this ZIP.
2. Copy `sentinel/dataset_manager.py` into your existing project's `sentinel/` folder.
3. Copy `pages/09_Dataset_Manager.py` into your existing project's `pages/` folder.
   - If your project uses custom navigation rather than Streamlit's `pages/` folder, use the integration snippet below instead.
4. Create a `datasets/` folder in the project root.
5. Restart Streamlit.

No new Python packages are required beyond the project's existing Streamlit and Pandas dependencies.

## Folder example

```text
SENTINEL_Insider_Threat_Detection/
├── app.py
├── sentinel/
│   ├── __init__.py
│   └── dataset_manager.py
├── pages/
│   └── 09_Dataset_Manager.py
└── datasets/
    ├── CERT/
    │   └── r4.2/
    │       ├── logon.csv
    │       ├── device.csv
    │       ├── file.csv
    │       ├── email.csv
    │       ├── http.csv
    │       └── LDAP.csv
    └── imported/
```

The exact CERT folder layout may differ. The manager searches subfolders recursively.

## Access the selected dataset from another page

Add this to a detection page after the Dataset Manager has selected a dataset:

```python
from sentinel.dataset_manager import get_active_dataset

df = get_active_dataset()

if df is None:
    st.info("Choose a dataset in Dataset Manager first.")
    st.stop()

# Pass df to your existing preprocessing/detection functions.
```

The selected dataframe is stored in Streamlit session state, so it is available across pages in the same browser session.

## Important data and evaluation notes

- Original source CSVs are not modified.
- Uploads are saved under `datasets/imported/`.
- CERT answer-key / ground-truth files must not be included as model input features. Keep them separate and use them only to evaluate predictions.
- A CSV being imported successfully does not mean it is ready for Isolation Forest. CERT's event logs need dataset-specific preprocessing and per-user/time-window feature engineering first.
- The page previews data and reports missing/duplicate values; it does not claim model accuracy.
- Add `datasets/` to `.gitignore` if the dataset files are large or redistribution is not permitted. Commit instructions and scripts, not restricted dataset contents.

## Run

From the project root:

```bash
streamlit run app.py
```

The Dataset Manager page should appear in Streamlit's multipage navigation.
