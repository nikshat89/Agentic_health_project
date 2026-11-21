# Agentic Health Monitoring & Clinical Decision Support — dataset-aligned update

This version is aligned to `data/Synthetic_patient-HealthCare-Monitoring_dataset.csv` (13 columns; expected schema is defined in `src/agents.py`). It replaces the old Da Fit JSON assumptions (`raw_export.json`, steps, sleep, BMI, dates) because those fields are not present in this CSV.

## 1. Run the Streamlit dashboard (Windows)

Open Command Prompt in this project folder and run:

```bat
py -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

The dashboard loads `data/Synthetic_patient-HealthCare-Monitoring_dataset.csv` by default. Alternatively, upload the CSV in the sidebar. Filters include patient number, supplied predicted-disease label, data-accuracy floor and records with any `ABNORMAL` alert. The agents use the dataset's supplied alert labels rather than silently inventing new clinical classifications.

### Optional local Ollama explanation

Install/start Ollama and pull a model first, e.g. `ollama pull llama3.2`. Keep Ollama running, then enable **Use local Ollama** in the dashboard. Optional environment variables:

```bat
set OLLAMA_BASE_URL=http://127.0.0.1:11434
set OLLAMA_MODEL=llama3.2
```

If Ollama is not reachable, the explanation agent falls back to deterministic rule-based text. The workflow/dashboard remain usable without Ollama.

## 2. Import and run the static n8n workflow (no webhook)

Import `n8n/health_monitoring_static_workflow.json` into n8n. It uses a **Manual Trigger**, not a webhook. It reads the CSV, extracts rows, runs a Data Quality Agent, Monitoring Agent, then a Clinical Summary Agent. The final node outputs one summary object with counts and up to 25 sample review records.

The workflow JSON defaults to the path previously used in your Windows project:

`C:/Users/Nikshat Sharma/OneDrive/Desktop/agentic_health_project/data/Synthetic_patient-HealthCare-Monitoring_dataset.csv`

If your folder differs, open **Read Health Dataset CSV** and change `fileSelector` to the actual full path. Ensure the CSV is at that location.

### Important: n8n file permission

For n8n 2.x, allow the project folder for file access. Close the running n8n process first, then in Command Prompt run:

```bat
set "N8N_RESTRICT_FILE_ACCESS_TO=C:\Users\Nikshat Sharma\OneDrive\Desktop\agentic_health_project"
n8n
```

If you launch n8n from another terminal/service, set the same environment variable in that launch environment. If you use another folder, change the path in both the environment variable and workflow node. Restart n8n after changing it. Do not enable broad file access to the whole computer.

After import: open the workflow, click **Execute Workflow** / **Test workflow**, then select **Clinical Summary Agent** and inspect its Output. The workflow is inactive by default and requires no activation toggle because it is manually triggered.

## Agent responsibilities

1. **Data Ingestion Agent** — checks required columns, missing cells, numeric convertibility and duplicate patient numbers.
2. **Monitoring Agent** — summarises supplied `NORMAL`/`ABNORMAL` alert fields and fall flags.
3. **Trend Agent** — provides cross-sectional metric summaries. This CSV has no timestamp/date column, so longitudinal trends are intentionally not fabricated.
4. **Clinical Decision Support Agent** — provides cautious human-review prompts based on flags.
5. **Explanation Agent** — optionally uses local Ollama; deterministic fallback is available.
6. **Orchestrator** — coordinates agents for the dashboard.

## Limitations

- The CSV's `Predicted Disease` and alert labels are treated as supplied dataset fields; this project does not independently validate them.
- The optional 80% data-accuracy review threshold is an engineering setting, not a clinical standard.
- No timestamps are present, so this data cannot support a real time-series / week-over-week trend without an additional timestamped dataset.
- This is a research/educational prototype, not a medical device, diagnostic service or emergency service. It must not be used to make treatment decisions.
