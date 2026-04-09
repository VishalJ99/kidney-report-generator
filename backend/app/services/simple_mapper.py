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
from typing import Any, Dict, List, Optional, Tuple


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
    def _normalize_classification(value: Optional[str]) -> Optional[str]:
        """Normalize shorthand-entry classification values."""
        if value is None:
            return None

        cleaned = str(value).strip().lower()
        if cleaned in {"diagnosis", "pattern", "attribute"}:
            return cleaned

        return None

    @staticmethod
    def _normalize_medium(value: Optional[str], classification: Optional[str]) -> Optional[str]:
        """Normalize medium values for canonical coding groups."""
        if classification is None:
            return None
        if classification in {"diagnosis", "attribute"}:
            return "PATIENT"

        cleaned = str(value).strip().upper() if value is not None else ""
        if cleaned in {"LM", "EM", "IHC"}:
            return cleaned
        return "LM"

    @staticmethod
    def _is_resolved_code(value: Optional[str]) -> bool:
        """Return True when a code value is usable."""
        if value is None:
            return False
        cleaned = str(value).strip()
        return bool(cleaned) and cleaned.upper() != "VALUE"

    @classmethod
    def _normalize_codes(
        cls,
        value: Any,
        *,
        allow_placeholders: bool = False,
        preserve_nulls: bool = False,
    ) -> Dict[str, Optional[str]]:
        """Normalize a code-system mapping."""
        codes = {}
        if not isinstance(value, dict):
            return codes

        for code_key, code_value in value.items():
            if not code_key:
                continue
            cleaned_key = str(code_key).strip()
            if code_value is None:
                if preserve_nulls:
                    codes[cleaned_key] = None
                continue
            cleaned_value = cls._clean_text(code_value)
            if not cleaned_value:
                continue
            if not allow_placeholders and not cls._is_resolved_code(cleaned_value):
                continue
            codes[cleaned_key] = cleaned_value

        return codes

    def _normalize_coding_group(self, value: Any) -> Optional[Dict[str, Any]]:
        """Normalize a single canonical coding group."""
        if not isinstance(value, dict):
            return None

        classification = self._normalize_classification(value.get("classification"))
        medium = self._normalize_medium(value.get("medium"), classification)
        codes = self._normalize_codes(value.get("codes"), preserve_nulls=True)
        resolved_codes = {code_key: code_value for code_key, code_value in codes.items() if code_value is not None}
        if classification is None or medium is None or not resolved_codes:
            return None

        return {
            "classification": classification,
            "medium": medium,
            "codes": codes,
        }

    def _legacy_to_coding(self, entry: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert legacy top-level code metadata into one canonical coding group where possible."""
        classification = self._normalize_classification(entry.get("classification"))
        if classification is None:
            return []

        pattern_metadata = entry.get("pattern_metadata") if isinstance(entry.get("pattern_metadata"), dict) else {}
        medium = self._normalize_medium(pattern_metadata.get("medium"), classification)
        codes = self._normalize_codes(entry.get("codes"), preserve_nulls=True)
        resolved_codes = {code_key: code_value for code_key, code_value in codes.items() if code_value is not None}
        if medium is None or not resolved_codes:
            return []

        return [
            {
                "classification": classification,
                "medium": medium,
                "codes": codes,
            }
        ]

    def _normalize_coding(self, entry: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return canonical coding groups for an entry."""
        raw_coding = entry.get("coding")
        if isinstance(raw_coding, list) and raw_coding:
            coding = []
            for raw_group in raw_coding:
                normalized_group = self._normalize_coding_group(raw_group)
                if normalized_group:
                    coding.append(normalized_group)
            if coding:
                return coding

        return self._legacy_to_coding(entry)

    @staticmethod
    def _compatibility_fields_from_coding(
        coding: List[Dict[str, Any]],
    ) -> Tuple[Optional[str], Optional[Dict[str, str]], Dict[str, str]]:
        """Derive legacy compatibility fields from canonical coding groups."""
        if not coding:
            return None, None, {}

        classifications = {group["classification"] for group in coding}
        classification = next(iter(classifications)) if len(classifications) == 1 else None

        pattern_metadata = None
        if classification == "pattern":
            mediums = {group["medium"] for group in coding}
            if len(mediums) == 1:
                pattern_metadata = {"medium": next(iter(mediums))}

        flattened_codes: Dict[str, List[str]] = {}
        for group in coding:
            for code_key, code_value in group["codes"].items():
                if code_value is None:
                    continue
                flattened_codes.setdefault(code_key, [])
                if code_value not in flattened_codes[code_key]:
                    flattened_codes[code_key].append(code_value)

        return (
            classification,
            pattern_metadata,
            {code_key: ", ".join(values) for code_key, values in flattened_codes.items()},
        )

    @staticmethod
    def _pending_code_types(entry: Dict[str, Any]) -> List[str]:
        """Return unresolved placeholder code families from canonical coding or legacy top-level codes."""
        pending = []
        seen = set()

        for coding_group in entry.get("coding", []) or []:
            if not isinstance(coding_group, dict):
                continue
            for code_key, code_value in (coding_group.get("codes") or {}).items():
                if code_value is None:
                    cleaned_key = str(code_key).strip()
                    if cleaned_key and cleaned_key not in seen:
                        pending.append(cleaned_key)
                        seen.add(cleaned_key)

        for code_key, code_value in (entry.get("codes") or {}).items():
            if str(code_value).strip().upper() == "VALUE":
                cleaned_key = str(code_key).strip()
                if cleaned_key and cleaned_key not in seen:
                    pending.append(cleaned_key)
                    seen.add(cleaned_key)
        return pending

    def _build_storage_entry(self, payload: Dict[str, Any], existing_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Build the persisted entry shape, preferring canonical coding groups."""
        stored_entry = {
            "main_body": self._clean_text(payload.get("main_body")),
            "conclusion": self._clean_text(payload.get("conclusion")),
            "comments": self._clean_text(payload.get("comments")),
        }

        existing_coding = self._normalize_coding(existing_entry)
        incoming_coding = []

        raw_payload_coding = payload.get("coding")
        if isinstance(raw_payload_coding, list) and raw_payload_coding:
            for raw_group in raw_payload_coding:
                normalized_group = self._normalize_coding_group(raw_group)
                if normalized_group:
                    incoming_coding.append(normalized_group)
        elif existing_coding:
            incoming_coding = existing_coding
        else:
            incoming_coding = self._legacy_to_coding(payload)

        stored_entry["coding"] = incoming_coding

        if incoming_coding:
            pending_legacy_codes = {
                code_key: code_value
                for code_key, code_value in self._normalize_codes(existing_entry.get("codes"), allow_placeholders=True).items()
                if not self._is_resolved_code(code_value)
            }
            if pending_legacy_codes:
                stored_entry["codes"] = pending_legacy_codes
            return stored_entry

        legacy_codes = self._normalize_codes(payload.get("codes"), allow_placeholders=True)
        if not legacy_codes:
            legacy_codes = self._normalize_codes(existing_entry.get("codes"), allow_placeholders=True)
        if legacy_codes:
            stored_entry["codes"] = legacy_codes

        classification = self._normalize_classification(payload.get("classification"))
        if classification is None:
            classification = self._normalize_classification(existing_entry.get("classification"))
        if classification:
            stored_entry["classification"] = classification

        if classification == "pattern":
            payload_pattern_metadata = payload.get("pattern_metadata") if isinstance(payload.get("pattern_metadata"), dict) else {}
            existing_pattern_metadata = (
                existing_entry.get("pattern_metadata") if isinstance(existing_entry.get("pattern_metadata"), dict) else {}
            )
            medium_source = payload_pattern_metadata.get("medium") or existing_pattern_metadata.get("medium")
            stored_entry["pattern_metadata"] = {"medium": self._normalize_medium(medium_source, classification)}

        return stored_entry

    def _normalize_entry(self, key: str, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a stored entry for API responses."""
        coding = self._normalize_coding(entry)
        classification, pattern_metadata, codes = self._compatibility_fields_from_coding(coding)
        if not coding:
            classification = self._normalize_classification(entry.get("classification"))
            pattern_metadata = None
            if classification == "pattern":
                raw_pattern_metadata = entry.get("pattern_metadata") if isinstance(entry.get("pattern_metadata"), dict) else {}
                pattern_metadata = {"medium": self._normalize_medium(raw_pattern_metadata.get("medium"), classification)}
            codes = self._normalize_codes(entry.get("codes"), allow_placeholders=True)

        return {
            "key": self._normalize_key(key),
            "main_body": self._clean_text(entry.get("main_body")),
            "conclusion": self._clean_text(entry.get("conclusion")),
            "comments": self._clean_text(entry.get("comments")),
            "coding": coding,
            "classification": classification,
            "pattern_metadata": pattern_metadata,
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
            existing_entry = self.mappings.get(normalized_key, {})
            self.mappings[normalized_key] = self._build_storage_entry(payload, existing_entry)
            self._save_mappings()

        return self._normalize_entry(normalized_key, self.mappings[normalized_key])

    def delete_phrase_entry(self, key: str) -> Dict[str, Any]:
        """Delete a structured phrase entry and persist the updated dictionary."""
        normalized_key = self._normalize_key(key)
        if not normalized_key:
            raise ValueError("Phrase key is required.")

        with self._lock:
            if normalized_key not in self.mappings:
                raise ValueError(f"Phrase entry not found: {normalized_key}")

            deleted_entry = self._normalize_entry(normalized_key, self.mappings.pop(normalized_key))
            self._save_mappings()

        return deleted_entry

    def get_case_code(self, key: str, section: str) -> Optional[Dict[str, Any]]:
        """Return structured case-code metadata for a shorthand key."""
        key_lower = self._normalize_key(key)
        entry = self.mappings.get(key_lower)
        if not entry:
            return None

        coding = self._normalize_coding(entry)
        classification, pattern_metadata, codes = self._compatibility_fields_from_coding(coding)
        pending_code_types = self._pending_code_types(entry)

        if not coding:
            codes = self._normalize_codes(entry.get("codes"))
            classification = self._normalize_classification(entry.get("classification"))
            pattern_metadata = None
            if classification == "pattern":
                raw_pattern_metadata = entry.get("pattern_metadata") if isinstance(entry.get("pattern_metadata"), dict) else {}
                pattern_metadata = {"medium": self._normalize_medium(raw_pattern_metadata.get("medium"), classification)}

        if not coding and not codes and not pending_code_types:
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
            "coding": coding,
            "classification": classification,
            "pattern_metadata": pattern_metadata,
            "codes": codes,
            "pending_code_types": pending_code_types,
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

    def get_conclusion_codes(self, key: str, report_type: str = "transplant") -> List[str]:
        """Get report-type-appropriate conclusion codes for a key."""
        key_lower = self._normalize_key(key)

        if key_lower not in self.mappings:
            return []

        alias_priority = ["transplant"] if report_type == "transplant" else ["native1", "kbc", "native2"]
        extracted_codes = []
        seen_codes = set()

        coding = self._normalize_coding(self.mappings[key_lower])
        if coding:
            for coding_group in coding:
                for alias in alias_priority:
                    code_value = coding_group["codes"].get(alias)
                    if code_value and code_value not in seen_codes:
                        extracted_codes.append(code_value)
                        seen_codes.add(code_value)
                        break
            return extracted_codes

        codes = self.mappings[key_lower].get("codes", {})
        if not codes:
            return []

        if report_type == "transplant":
            code_value = codes.get("transplant")
        else:
            code_value = codes.get("native1") or codes.get("kbc") or codes.get("native2")

        if not self._is_resolved_code(code_value):
            return []

        return [str(code_value).strip()]

    def get_conclusion_code(self, key: str, report_type: str = "transplant") -> Optional[str]:
        """Backward-compatible single-code accessor for older callers."""
        codes = self.get_conclusion_codes(key, report_type)
        return codes[0] if codes else None

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
