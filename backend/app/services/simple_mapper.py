"""
Simple mapper for converting shorthand codes to full medical phrases.
Supports section-specific values and code extraction.
"""

import json
import os
import re
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import Lock
from typing import Any, Dict, List, Optional


class SimpleMapper:
    """Maps shorthand codes to full medical phrases using sectioned JSON lookup."""

    def __init__(self, json_path: Optional[str] = None):
        """Initialize mapper with phrases from sectioned JSON file."""
        default_json_path = Path(__file__).parent.parent / "data" / "phrases_sectioned.json"
        configured_path = json_path or os.getenv("PHRASES_JSON_PATH")
        self.json_path = Path(configured_path) if configured_path else default_json_path
        self.default_json_path = default_json_path
        self._lock = Lock()
        self._ensure_json_exists()
        self._load_mappings()

    def _ensure_json_exists(self) -> None:
        """Seed a configured phrases file from the bundled default if needed."""
        if self.json_path.exists():
            return

        self.json_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(self.default_json_path, self.json_path)

    def _load_mappings(self) -> None:
        """Load mappings from disk."""
        with open(self.json_path, "r", encoding="utf-8") as file_handle:
            self.mappings = json.load(file_handle)

    def _save_mappings(self) -> None:
        """Persist mappings atomically to disk."""
        self.json_path.parent.mkdir(parents=True, exist_ok=True)

        with NamedTemporaryFile("w", dir=self.json_path.parent, delete=False, encoding="utf-8") as file_handle:
            json.dump(self.mappings, file_handle, indent=2)
            file_handle.write("\n")
            temp_path = Path(file_handle.name)

        temp_path.replace(self.json_path)

    @staticmethod
    def _normalize_key(key: str) -> str:
        """Normalize a shorthand key."""
        return key.strip().lower()

    @staticmethod
    def _clean_text(value: Optional[str]) -> str:
        """Normalize free-text fields to strings."""
        if value is None:
            return ""
        return str(value).strip()

    @staticmethod
    def _is_resolved_code(value: Optional[str]) -> bool:
        """Return True when a code value is usable."""
        if value is None:
            return False
        cleaned = str(value).strip()
        return bool(cleaned) and cleaned.upper() != "VALUE"

    def _normalize_entry(self, key: str, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a stored entry without dropping unknown code fields."""
        codes = {}
        for code_key, code_value in (entry.get("codes") or {}).items():
            if not code_key:
                continue
            codes[str(code_key).strip()] = self._clean_text(code_value)

        return {
            "key": self._normalize_key(key),
            "main_body": self._clean_text(entry.get("main_body")),
            "conclusion": self._clean_text(entry.get("conclusion")),
            "comments": self._clean_text(entry.get("comments")),
            "codes": codes,
        }

    def get_phrase_entries(self) -> List[Dict[str, Any]]:
        """Return structured phrase entries for the frontend phrase manager."""
        entries = [self._normalize_entry(key, entry) for key, entry in self.mappings.items()]
        return sorted(entries, key=lambda entry: entry["key"])

    def upsert_phrase_entry(self, key: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update a structured phrase entry and persist it."""
        normalized_key = self._normalize_key(key)
        if not normalized_key:
            raise ValueError("Phrase key is required.")

        with self._lock:
            existing_entry = self._normalize_entry(normalized_key, self.mappings.get(normalized_key, {}))
            merged_codes = dict(existing_entry.get("codes", {}))

            for code_key, code_value in (payload.get("codes") or {}).items():
                if not code_key:
                    continue
                merged_codes[str(code_key).strip()] = self._clean_text(code_value)

            self.mappings[normalized_key] = {
                "main_body": self._clean_text(payload.get("main_body")),
                "conclusion": self._clean_text(payload.get("conclusion")),
                "comments": self._clean_text(payload.get("comments")),
                "codes": merged_codes,
            }
            self._save_mappings()

        return self._normalize_entry(normalized_key, self.mappings[normalized_key])

    def get_case_code(self, key: str, section: str) -> Optional[Dict[str, Any]]:
        """Return structured case-code metadata for a shorthand key."""
        key_lower = self._normalize_key(key)
        entry = self.mappings.get(key_lower)
        if not entry:
            return None

        codes = {
            code_key: code_value.strip()
            for code_key, code_value in (entry.get("codes") or {}).items()
            if self._is_resolved_code(code_value)
        }
        if not codes:
            return None

        label = (
            self._clean_text(entry.get("conclusion"))
            or self._clean_text(entry.get(section))
            or self._clean_text(entry.get("main_body"))
            or self._clean_text(entry.get("comments"))
            or key_lower
        )

        return {
            "key": key_lower,
            "section": section,
            "label": label,
            "codes": codes,
        }

    def map_code(self, code: str, section: str = "main_body") -> Optional[str]:
        """Map a single shorthand code to its full phrase for a given section."""
        code_lower = self._normalize_key(code)

        if code_lower in self.mappings:
            entry = self.mappings[code_lower]
            value = entry.get(section, "")
            return value if value else None

        for key, entry in self.mappings.items():
            if key.startswith("~"):
                pattern = key[1:]
                match = re.match(pattern, code_lower, re.IGNORECASE)
                if match:
                    template = entry.get(section, "")
                    if not template:
                        return None

                    result = template
                    for i, group in enumerate(match.groups(), 1):
                        result = result.replace(f"{{{i}}}", group)
                    return result

        return None

    def get_conclusion_code(self, key: str, report_type: str = "transplant") -> Optional[str]:
        """Get database code for a conclusion key."""
        key_lower = self._normalize_key(key)

        if key_lower not in self.mappings:
            return None

        codes = self.mappings[key_lower].get("codes", {})
        if not codes:
            return None

        if report_type == "transplant":
            code_value = codes.get("transplant")
        else:
            code_value = codes.get("native1") or codes.get("kbc") or codes.get("native2")

        if not self._is_resolved_code(code_value):
            return None

        return str(code_value).strip()

    def get_all_mappings(self) -> Dict[str, str]:
        """Return all mappings for the reference popup."""
        result = {}
        section_labels = {
            "main_body": "MAIN BODY",
            "conclusion": "CONCLUSION",
            "comments": "COMMENTS",
        }

        for key, entry in self.mappings.items():
            display_key = key[1:] + " (pattern)" if key.startswith("~") else key

            for section, label in section_labels.items():
                value = entry.get(section, "")
                if value:
                    result[f"{display_key} [{label}]"] = value

        return result

    def is_header(self, code: str) -> bool:
        """Check if a code represents a section header."""
        return self._normalize_key(code).startswith("!")
