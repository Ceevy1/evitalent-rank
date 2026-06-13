from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from evitalent.settings import PROJECT_ROOT


DEFAULT_PRIVATE_ROOT = PROJECT_ROOT / "data"
DEFAULT_INPUT_ROOT = PROJECT_ROOT / "data" / "raw" / "resumes"


@dataclass(frozen=True)
class OfficialSampleSettings:
    version: str
    domains: list[str]
    allowed_extensions: list[str]
    private_data_root: Path
    resume_input_root: Path
    require_manual_redaction_review: bool
    allow_llm_before_review: bool
    extraction_mode: str
    allow_mock_fallback: bool
    allow_cached_response: bool
    continue_on_single_document_failure: bool
    checkpoint_enabled: bool
    scoring_only_if_eligible: bool

    @property
    def redacted_pilot_dir(self) -> Path:
        return self.private_data_root / "redacted" / "resumes" / "pilot"

    @property
    def redacted_batch_dir(self) -> Path:
        return self.private_data_root / "redacted" / "resumes" / "batch"

    @property
    def extracted_pilot_dir(self) -> Path:
        return self.private_data_root / "extracted" / "resumes" / "pilot"

    @property
    def extracted_batch_dir(self) -> Path:
        return self.private_data_root / "extracted" / "resumes" / "batch"

    @property
    def official_output_root(self) -> Path:
        return self.private_data_root / "outputs" / "official_samples_v1"

    @property
    def manifests_dir(self) -> Path:
        return self.official_output_root / "manifests"

    @property
    def pilot_output_dir(self) -> Path:
        return self.official_output_root / "pilot"

    @property
    def batch_output_dir(self) -> Path:
        return self.official_output_root / "batch"

    @property
    def rankings_dir(self) -> Path:
        return self.official_output_root / "rankings"

    @property
    def reports_dir(self) -> Path:
        return self.official_output_root / "reports"

    @property
    def raw_manifest_path(self) -> Path:
        return self.manifests_dir / "raw_manifest_private.json"

    @property
    def inventory_safe_summary_path(self) -> Path:
        return self.manifests_dir / "inventory_safe_summary.json"

    @property
    def redaction_pilot_private_path(self) -> Path:
        return self.pilot_output_dir / "redaction_pilot_private.json"

    @property
    def redaction_pilot_safe_summary_path(self) -> Path:
        return self.pilot_output_dir / "redaction_pilot_safe_summary.json"

    @property
    def review_gate_path(self) -> Path:
        return self.pilot_output_dir / "redaction_review_gate.json"

    @property
    def llm_pilot_private_path(self) -> Path:
        return self.pilot_output_dir / "llm_pilot_private.json"

    @property
    def llm_pilot_safe_summary_path(self) -> Path:
        return self.pilot_output_dir / "llm_pilot_safe_summary.json"

    @property
    def batch_state_path(self) -> Path:
        return self.batch_output_dir / "batch_run_state.json"

    @property
    def manual_review_path(self) -> Path:
        return self.batch_output_dir / "manual_review_records.json"

    @property
    def risk_issue_review_path(self) -> Path:
        return self.batch_output_dir / "risk_issue_review_records.json"

    def ensure_private_dirs(self) -> None:
        for path in [
            self.resume_input_root,
            self.redacted_pilot_dir,
            self.redacted_batch_dir,
            self.extracted_pilot_dir,
            self.extracted_batch_dir,
            self.manifests_dir,
            self.pilot_output_dir,
            self.batch_output_dir,
            self.batch_output_dir / "extraction_results_private",
            self.rankings_dir,
            self.reports_dir,
        ]:
            path.mkdir(parents=True, exist_ok=True)
        for domain in self.domains:
            (self.resume_input_root / domain).mkdir(parents=True, exist_ok=True)
            (self.redacted_pilot_dir / domain).mkdir(parents=True, exist_ok=True)
            (self.redacted_batch_dir / domain).mkdir(parents=True, exist_ok=True)
            (self.extracted_pilot_dir / domain).mkdir(parents=True, exist_ok=True)
            (self.extracted_batch_dir / domain).mkdir(parents=True, exist_ok=True)


def _read_config(config_path: Path | None = None) -> dict[str, Any]:
    path = config_path or PROJECT_ROOT / "config" / "official_samples_settings.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_official_sample_settings(config_path: Path | None = None, create_dirs: bool = True) -> OfficialSampleSettings:
    cfg = _read_config(config_path)
    input_cfg = cfg.get("input", {})
    processing_cfg = cfg.get("processing", {})
    pilot_cfg = cfg.get("pilot", {})
    private_root = Path(os.getenv(input_cfg.get("private_data_root_env", "EVITALENT_PRIVATE_DATA_ROOT"), str(DEFAULT_PRIVATE_ROOT)))
    input_root = Path(os.getenv(input_cfg.get("resume_input_root_env", "RESUME_INPUT_ROOT"), str(private_root / "raw" / "resumes")))
    settings = OfficialSampleSettings(
        version=str(cfg.get("version", "1.0.0")),
        domains=list(cfg["domains"]),
        allowed_extensions=[ext.lower() for ext in input_cfg.get("allowed_extensions", [".docx"])],
        private_data_root=private_root,
        resume_input_root=input_root,
        require_manual_redaction_review=bool(pilot_cfg.get("require_manual_redaction_review", True)),
        allow_llm_before_review=bool(pilot_cfg.get("allow_llm_before_review", False)),
        extraction_mode=str(processing_cfg.get("extraction_mode", "local_ollama")),
        allow_mock_fallback=bool(processing_cfg.get("allow_mock_fallback", False)),
        allow_cached_response=bool(processing_cfg.get("allow_cached_response", False)),
        continue_on_single_document_failure=bool(processing_cfg.get("continue_on_single_document_failure", True)),
        checkpoint_enabled=bool(processing_cfg.get("checkpoint_enabled", True)),
        scoring_only_if_eligible=bool(processing_cfg.get("scoring_only_if_eligible", True)),
    )
    if create_dirs:
        settings.ensure_private_dirs()
    return settings
