"""
Build native and transplant XLSX exports from shorthand-derived coding data.
"""

from io import BytesIO
from typing import Any, Dict, Iterable, List, Optional

from openpyxl import Workbook


PATIENT_FIELD_PREFIXES = {
    "Name": "name",
    "NHS": "nhs_number",
    "HN": "hospital_number",
    "NS": "path_number",
    "Coder": "coder",
    "Date": "date",
    "Consent": "consent",
}

NATIVE_HEADERS = [
    "Name",
    "CODER",
    "Date",
    "NHS number",
    "Hosp number",
    "Path number",
    "CONSENT PIS v 6. (Y N U)",
    "Diagnosis KBC",
    "Diagnosis native1",
    "Diagnosis native2",
    "Pattern KBC",
    "Pattern native1",
    "Pattern native2",
]

TRANSPLANT_HEADERS = [
    "Path no",
    "NHS Number",
    "IF Sample",
    "RNA Sample",
    "EM Sample",
    "EM US done",
    "Coder",
    "Consent",
    "Date of Bx",
    "Type Bx",
    "Diagnosis codes",
    "Comments histology",
    "Banff Scores from",
    "C4d",
    "SV40",
    "IFTA nearest 10%",
    "CT",
    "CI",
    "I",
    "iIFTA",
    "TI",
    "T",
    "Arteries Number",
    "CV",
    "Leuco Scl Int",
    "V",
    "AH",
    "G (nr)",
    "Obs G (nr)",
    "Segm G (nr)",
    "Segm G type",
    "CG",
    "Glomerulitis",
    "PTC",
    "MVI",
    "EDD",
    "Glom FPE",
    "Glom ES",
    "Glom SER",
    "Glom new GBM",
    "Glom TRI",
    "PTCBMML2",
    "PTCBMML3",
    "PTCBMML5",
    "PTCBMML7",
    "IF (FROZEN/PARA)",
    "IGG",
    "IGA",
    "IGM",
    "C3",
    "C1Q",
    "KAPPA",
    "LAMBDA",
]

BANFF_COLUMN_MAP = {
    "C4D": "C4d",
    "CT": "CT",
    "CI": "CI",
    "I": "I",
    "IIFTA": "iIFTA",
    "TI": "TI",
    "T": "T",
    "CV": "CV",
    "V": "V",
    "AH": "AH",
    "CG": "CG",
    "G": "Glomerulitis",
    "PTC": "PTC",
}


class ExportConflictError(ValueError):
    """Raised when export data contains conflicting user-entered values."""


def _blank_row(headers: Iterable[str]) -> Dict[str, Any]:
    return {header: "" for header in headers}


def _dedupe(values: Iterable[str]) -> List[str]:
    seen = set()
    result = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _list_cell(values: Iterable[str]) -> str:
    return "; ".join(_dedupe(values))


def _extract_patient_fields(shorthand_text: str) -> Dict[str, str]:
    fields = {field: "" for field in PATIENT_FIELD_PREFIXES.values()}
    for raw_line in shorthand_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("!"):
            continue
        for prefix, field in PATIENT_FIELD_PREFIXES.items():
            if line.lower().startswith(prefix.lower() + " "):
                fields[field] = line[len(prefix) + 1 :].strip()
    return fields


def _append_code(
    buckets: Dict[str, List[str]],
    column_prefix: str,
    codes: Dict[str, Optional[str]],
) -> None:
    for code_family in ("kbc", "native1", "native2"):
        code_value = codes.get(code_family)
        if code_value:
            buckets[f"{column_prefix} {code_family.upper() if code_family == 'kbc' else code_family}"].append(code_value)


def _parse_banff_code(code_value: str) -> Optional[tuple[str, str]]:
    if "_" not in code_value:
        return None
    raw_column, value = code_value.rsplit("_", 1)
    column = BANFF_COLUMN_MAP.get(raw_column.upper())
    if not column or not value:
        return None
    return column, value


def _write_workbook(headers: List[str], row: Dict[str, Any]) -> bytes:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Export"
    worksheet.append(headers)
    worksheet.append([row.get(header, "") for header in headers])

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def build_native_export(shorthand_text: str, case_codes: List[Dict[str, Any]]) -> bytes:
    """Build the native XLSX export."""
    fields = _extract_patient_fields(shorthand_text)
    row = _blank_row(NATIVE_HEADERS)
    row["Name"] = fields["name"]
    row["CODER"] = fields["coder"]
    row["Date"] = fields["date"]
    row["NHS number"] = fields["nhs_number"]
    row["Hosp number"] = fields["hospital_number"]
    row["Path number"] = fields["path_number"]
    row["CONSENT PIS v 6. (Y N U)"] = fields["consent"]

    buckets = {
        "Diagnosis KBC": [],
        "Diagnosis native1": [],
        "Diagnosis native2": [],
        "Pattern KBC": [],
        "Pattern native1": [],
        "Pattern native2": [],
    }

    for entry in case_codes:
        for coding_group in entry.get("coding", []) or []:
            classification = coding_group.get("classification")
            codes = coding_group.get("codes") or {}
            if classification == "diagnosis":
                _append_code(buckets, "Diagnosis", codes)
            elif classification == "pattern":
                _append_code(buckets, "Pattern", codes)

    for column, values in buckets.items():
        row[column] = _list_cell(values)

    return _write_workbook(NATIVE_HEADERS, row)


def build_transplant_export(shorthand_text: str, case_codes: List[Dict[str, Any]]) -> bytes:
    """Build the transplant XLSX export."""
    fields = _extract_patient_fields(shorthand_text)
    row = _blank_row(TRANSPLANT_HEADERS)
    row["Path no"] = fields["path_number"]
    row["NHS Number"] = fields["nhs_number"]
    row["Coder"] = fields["coder"]
    row["Consent"] = fields["consent"]
    row["Date of Bx"] = fields["date"]
    row["Type Bx"] = "Transplant"

    diagnosis_codes = []
    banff_sources: Dict[str, tuple[str, str]] = {}
    for entry in case_codes:
        for coding_group in entry.get("coding", []) or []:
            classification = coding_group.get("classification")
            codes = coding_group.get("codes") or {}

            transplant_code = codes.get("transplant")
            if classification == "pattern" and transplant_code:
                parsed_banff = _parse_banff_code(transplant_code)
                if parsed_banff:
                    column, value = parsed_banff
                    previous = banff_sources.get(column)
                    if previous and previous[0] != value:
                        previous_value, previous_key = previous
                        raise ExportConflictError(
                            "Conflicting Banff scores entered for "
                            f"{column}: {previous_key} gives {previous_value}, "
                            f"{entry.get('key')} gives {value}. Please remove the incorrect shorthand before exporting."
                        )
                    row[column] = value
                    banff_sources[column] = (value, entry.get("key", "unknown shorthand"))
                    continue

            if classification == "diagnosis":
                if transplant_code:
                    diagnosis_codes.append(transplant_code)
                elif codes.get("kbc"):
                    diagnosis_codes.append(codes["kbc"])

    row["Diagnosis codes"] = _list_cell(diagnosis_codes)
    return _write_workbook(TRANSPLANT_HEADERS, row)


def build_export_workbook(
    shorthand_text: str,
    report_type: str,
    case_codes: List[Dict[str, Any]],
) -> bytes:
    """Build the report-type-specific XLSX export."""
    if report_type == "native":
        return build_native_export(shorthand_text, case_codes)
    return build_transplant_export(shorthand_text, case_codes)
