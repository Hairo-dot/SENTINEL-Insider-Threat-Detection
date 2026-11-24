# SENTINEL project implementation notes

## Current build status
- Existing multi-section Streamlit interface and custom navigation preserved.
- Existing synthetic demonstration data preserved.
- Universal CSV importer integrated into Data & Sources.
- Best-effort column detection plus manual source-column mapping.
- Common event schema normalisation and missing optional-field handling.
- 500-employee synthetic workforce generator added.
- Configurable 30–180 day history and suspicious activity scenarios.
- Ground-truth labels kept out of Isolation Forest features.
- Label-aware precision, recall, F1 and accuracy displayed after detection when recognised labels are available.
- Isolation Forest event scoring and behavioural analytics preserved.
- Threat relationship graph and incident timeline preserved.
- Markdown and CSV report export preserved.
- SQLite review/run persistence foundation preserved.

## Validation checklist
- [x] Python syntax compilation for changed modules.
- [x] Existing core tests (3) pass.
- [x] CSV normalisation tested with alternate column headings.
- [x] Synthetic generator tested at 500 employees and 90 days.
- [x] Isolation Forest tested on generated dataset.
- [ ] Install dependencies in a clean Windows virtual environment.
- [ ] Start Streamlit and visit every page in the user's local browser.
- [ ] Test manual mapping with the user's downloaded research CSV.
- [ ] Integrate and evaluate any external research dataset after checking its schema, licence and citation requirements.
- [ ] Capture screenshots from the actual running app.
- [ ] Complete the academic report using measured results from the final dataset.

## Important modelling note
An Isolation Forest output is an anomaly candidate, not a confirmed insider threat. Risk score is relative to the current dataset/run and must not be interpreted as a calibrated probability. Ground-truth labels are used only after prediction for evaluation, never as model features.
