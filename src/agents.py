"""Dataset-aligned multi-agent analysis for Synthetic_patient-HealthCare-Monitoring_dataset.csv.

This is a research prototype. Dataset alert columns are treated as supplied labels;
rule outputs are monitoring prompts, not medical diagnoses.
"""
from __future__ import annotations

import json
import os
import urllib.request
import urllib.error
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = [
    "Patient Number", "Heart Rate (bpm)", "SpO2 Level (%)",
    "Systolic Blood Pressure (mmHg)", "Diastolic Blood Pressure (mmHg)",
    "Body Temperature (°C)", "Fall Detection", "Predicted Disease",
    "Data Accuracy (%)", "Heart Rate Alert", "SpO2 Level Alert",
    "Blood Pressure Alert", "Temperature Alert",
]
NUMERIC_COLUMNS = [
    "Patient Number", "Heart Rate (bpm)", "SpO2 Level (%)",
    "Systolic Blood Pressure (mmHg)", "Diastolic Blood Pressure (mmHg)",
    "Body Temperature (°C)", "Data Accuracy (%)",
]
ALERT_COLUMNS = [
    "Heart Rate Alert", "SpO2 Level Alert", "Blood Pressure Alert", "Temperature Alert",
]

@dataclass
class Finding:
    level: str
    title: str
    evidence: str
    action: str

class DataIngestionAgent:
    """Checks schema, numeric convertibility, missingness, and duplicate IDs."""
    def run(self, df: pd.DataFrame) -> dict[str, Any]:
        missing_columns = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        missing_cells = int(df.isna().sum().sum()) if not df.empty else 0
        numeric_invalid = {}
        for col in NUMERIC_COLUMNS:
            if col in df.columns:
                parsed = pd.to_numeric(df[col], errors="coerce")
                numeric_invalid[col] = int((parsed.isna() & df[col].notna()).sum())
        duplicate_ids = 0
        if "Patient Number" in df.columns:
            duplicate_ids = int(df["Patient Number"].duplicated().sum())
        return {
            "rows": int(len(df)), "columns": int(len(df.columns)),
            "schema_valid": not missing_columns, "missing_required_columns": missing_columns,
            "missing_cells": missing_cells, "numeric_invalid_counts": numeric_invalid,
            "duplicate_patient_numbers": duplicate_ids,
            "data_accuracy_mean_pct": round(float(pd.to_numeric(df["Data Accuracy (%)"], errors="coerce").mean()), 2)
                if "Data Accuracy (%)" in df.columns and not df.empty else None,
        }

class MonitoringAgent:
    """Summarises the dataset's existing alert labels and fall-detection values."""
    def run(self, df: pd.DataFrame) -> dict[str, Any]:
        alert_counts = {}
        for col in ALERT_COLUMNS:
            if col in df.columns:
                s = df[col].astype(str).str.strip().str.upper()
                alert_counts[col] = {
                    "abnormal": int(s.eq("ABNORMAL").sum()),
                    "normal": int(s.eq("NORMAL").sum()),
                    "other_or_missing": int((~s.isin(["ABNORMAL", "NORMAL"])).sum()),
                }
        if "Fall Detection" in df.columns:
            fall = df["Fall Detection"].astype(str).str.strip().str.lower()
            fall_count = int(fall.isin(["yes", "true", "1", "detected", "fall"]).sum())
        else:
            fall_count = 0
        return {"alert_counts": alert_counts, "fall_detected_records": fall_count}

    def patient_findings(self, row: pd.Series | dict[str, Any]) -> list[Finding]:
        r = dict(row)
        findings: list[Finding] = []
        for col, label in [
            ("Heart Rate Alert", "Heart-rate alert"),
            ("SpO2 Level Alert", "SpO₂ alert"),
            ("Blood Pressure Alert", "Blood-pressure alert"),
            ("Temperature Alert", "Temperature alert"),
        ]:
            val = str(r.get(col, "")).strip().upper()
            if val == "ABNORMAL":
                metric_col = {
                    "Heart Rate Alert": "Heart Rate (bpm)",
                    "SpO2 Level Alert": "SpO2 Level (%)",
                    "Blood Pressure Alert": "Systolic Blood Pressure (mmHg)",
                    "Temperature Alert": "Body Temperature (°C)",
                }[col]
                metric_value = r.get(metric_col, "not available")
                findings.append(Finding(
                    "attention", label,
                    f"Dataset marks {col} as ABNORMAL; corresponding recorded value: {metric_value}.",
                    "Verify the measurement and context; seek qualified clinical review where appropriate. This label is not a diagnosis.",
                ))
            elif val not in ("NORMAL", ""):
                findings.append(Finding("info", f"Unrecognised {label.lower()} label", f"Supplied label: {val}.", "Check source-data definitions before interpreting this field."))
        fall = str(r.get("Fall Detection", "")).strip().lower()
        if fall in ("yes", "true", "1", "detected", "fall"):
            findings.append(Finding("attention", "Fall detection marked positive", "Dataset records a positive fall-detection value.", "Check the person's immediate safety and verify the event with a human responder; this prototype does not dispatch emergency services."))
        try:
            accuracy = float(r.get("Data Accuracy (%)"))
            if accuracy < 80:
                findings.append(Finding("info", "Low data-accuracy score", f"Recorded Data Accuracy is {accuracy:.1f}% (prototype review threshold: 80%).", "Verify signal quality and source definitions. The 80% threshold is a configurable engineering rule, not a clinical standard."))
        except (TypeError, ValueError):
            findings.append(Finding("info", "Data accuracy unavailable", "Data Accuracy (%) could not be interpreted as a number.", "Check source data and data-quality metadata."))
        if not findings:
            findings.append(Finding("good", "No supplied alert flags triggered", "The record's alert fields are NORMAL and no positive fall flag was detected.", "Continue routine monitoring; NORMAL labels do not prove that the person is healthy."))
        return findings

class TrendAgent:
    """Provides cross-sectional summaries; this dataset has no timestamp for time trends."""
    def run(self, df: pd.DataFrame) -> dict[str, Any]:
        result: dict[str, Any] = {"analysis_type": "cross-sectional", "time_trend_available": False,
                                  "note": "No timestamp/date column is present, so longitudinal trends are not calculated."}
        metrics = ["Heart Rate (bpm)", "SpO2 Level (%)", "Systolic Blood Pressure (mmHg)",
                   "Diastolic Blood Pressure (mmHg)", "Body Temperature (°C)", "Data Accuracy (%)"]
        result["metric_summary"] = {}
        for col in metrics:
            if col in df.columns:
                s = pd.to_numeric(df[col], errors="coerce").dropna()
                if len(s):
                    result["metric_summary"][col] = {
                        "mean": round(float(s.mean()), 2), "median": round(float(s.median()), 2),
                        "min": round(float(s.min()), 2), "max": round(float(s.max()), 2),
                    }
        if "Predicted Disease" in df.columns:
            result["predicted_disease_counts"] = {str(k): int(v) for k, v in df["Predicted Disease"].fillna("Unknown").value_counts().head(20).items()}
        return result

class ClinicalDecisionSupportAgent:
    """Converts dataset flags into cautious review prompts; never diagnoses or prescribes."""
    def run(self, findings: list[Finding]) -> list[str]:
        recs = [f.action for f in findings if f.level == "attention"]
        if not recs:
            recs.append("No supplied abnormal alert/fall flags were found for this record. Continue routine monitoring and do not interpret this as a medical clearance.")
        recs.append("Research prototype only: review source measurements and consult a qualified healthcare professional for clinical interpretation. Not an emergency service.")
        return recs

class ExplanationAgent:
    """Optional local Ollama explanation with a deterministic fallback."""
    def run(self, findings: list[Finding], patient: dict[str, Any], use_ollama: bool = False) -> dict[str, Any]:
        fallback = self._fallback(findings, patient)
        if not use_ollama:
            return {"text": fallback, "provider": "rule-based"}
        base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
        model = os.getenv("OLLAMA_MODEL", "llama3.2")
        prompt = (
            "Explain this synthetic healthcare dataset record in simple language. Use only supplied facts. "
            "Do not diagnose, prescribe, or invent missing data. Mention that dataset flags are not diagnoses. "
            "Keep under 100 words. Record: " + json.dumps(patient, default=str) +
            " Findings: " + json.dumps([asdict(f) for f in findings], default=str)
        )
        payload = json.dumps({"model": model, "prompt": prompt, "stream": False,
                              "options": {"temperature": 0.1}}).encode("utf-8")
        req = urllib.request.Request(base_url + "/api/generate", data=payload,
                                     headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                answer = json.loads(response.read().decode("utf-8")).get("response", "").strip()
            if answer:
                return {"text": answer, "provider": f"Ollama ({model})"}
        except (OSError, urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
            return {"text": fallback + f"\n\nLocal Ollama unavailable; used rule-based fallback ({type(exc).__name__}).", "provider": "rule-based fallback"}
        return {"text": fallback, "provider": "rule-based fallback"}

    @staticmethod
    def _fallback(findings: list[Finding], patient: dict[str, Any]) -> str:
        alerts = [f.title for f in findings if f.level == "attention"]
        pid = patient.get("Patient Number", "selected record")
        if alerts:
            return f"Record {pid} has monitoring flags: {', '.join(alerts)}. These are labels from the supplied dataset, not diagnoses. Verify measurements and obtain qualified clinical review when appropriate."
        return f"Record {pid} has no supplied abnormal alert/fall flag identified by this prototype. This does not establish that the person is healthy; interpret results with source definitions and a qualified professional."

class Orchestrator:
    """Coordinates the dataset-aligned agents for a cohort and an optional selected record."""
    def run(self, df: pd.DataFrame, patient_number: Any = None, use_ollama: bool = False) -> dict[str, Any]:
        ingestion = DataIngestionAgent().run(df)
        monitoring = MonitoringAgent()
        monitoring_summary = monitoring.run(df)
        trends = TrendAgent().run(df)
        selected = df
        if patient_number is not None and "Patient Number" in df.columns:
            selected = df[pd.to_numeric(df["Patient Number"], errors="coerce") == float(patient_number)]
        if selected.empty:
            row: dict[str, Any] = {}
            findings = [Finding("info", "No matching patient record", f"No record matched Patient Number {patient_number}.", "Check the selected patient number and dataset filters.")]
        else:
            row = selected.iloc[0].to_dict()
            findings = monitoring.patient_findings(row)
        recs = ClinicalDecisionSupportAgent().run(findings)
        explanation = ExplanationAgent().run(findings, row, use_ollama=use_ollama)
        return {"ingestion_summary": ingestion, "monitoring_summary": monitoring_summary,
                "trend_summary": trends, "selected_patient": row,
                "findings": [asdict(f) for f in findings], "recommendations": recs,
                "explanation": explanation}

def load_dataset(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Preserve source columns while converting known numeric fields safely.
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df
