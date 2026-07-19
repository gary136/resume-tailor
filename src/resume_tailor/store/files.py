"""File-backed stores: fact inventory, resumes, preference record.

Layout under the data dir (default ./data, override with RESUME_TAILOR_DATA):
    facts.yaml          fact inventory (truth record)
    preferences.yaml    preference record
    resumes/*.md        master + variants
    resume_tailor.db    SQLite (jobs + application log)
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml

from resume_tailor.contracts import FactInventory, PreferenceRecord


def data_dir() -> Path:
    return Path(os.environ.get("RESUME_TAILOR_DATA", "data"))


def db_path() -> Path:
    return data_dir() / "resume_tailor.db"


def resumes_dir() -> Path:
    return data_dir() / "resumes"


def load_fact_inventory(path: Path | None = None) -> FactInventory:
    path = path or data_dir() / "facts.yaml"
    return FactInventory.model_validate(yaml.safe_load(path.read_text()))


def save_fact_inventory(inventory: FactInventory, path: Path | None = None) -> Path:
    path = path or data_dir() / "facts.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(inventory.model_dump(), sort_keys=False, allow_unicode=True))
    return path


def load_preferences(path: Path | None = None) -> PreferenceRecord:
    path = path or data_dir() / "preferences.yaml"
    if not path.exists():
        return PreferenceRecord()
    return PreferenceRecord.model_validate(yaml.safe_load(path.read_text()))


def save_preferences(preferences: PreferenceRecord, path: Path | None = None) -> Path:
    path = path or data_dir() / "preferences.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(preferences.model_dump(), sort_keys=False, allow_unicode=True))
    return path
