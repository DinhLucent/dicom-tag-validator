"""
dicom-tag-validator — Python CLI tool for validating DICOM tags against
the DICOM standard (PS3.6) with detailed error reporting and HL7 integration support.

Author: DinhLucent
License: MIT
"""
from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# DICOM Standard Tag Registry (subset of PS3.6 Data Dictionary)
# Format: (group, element): (keyword, VR, VM, description)
# ---------------------------------------------------------------------------
DICOM_TAG_REGISTRY: Dict[Tuple[int, int], Dict[str, str]] = {
    (0x0008, 0x0016): {"keyword": "SOPClassUID",            "vr": "UI", "vm": "1",   "desc": "SOP Class UID"},
    (0x0008, 0x0018): {"keyword": "SOPInstanceUID",         "vr": "UI", "vm": "1",   "desc": "SOP Instance UID"},
    (0x0008, 0x0020): {"keyword": "StudyDate",              "vr": "DA", "vm": "1",   "desc": "Study Date"},
    (0x0008, 0x0021): {"keyword": "SeriesDate",             "vr": "DA", "vm": "1",   "desc": "Series Date"},
    (0x0008, 0x0022): {"keyword": "AcquisitionDate",        "vr": "DA", "vm": "1",   "desc": "Acquisition Date"},
    (0x0008, 0x0023): {"keyword": "ContentDate",            "vr": "DA", "vm": "1",   "desc": "Content Date"},
    (0x0008, 0x0030): {"keyword": "StudyTime",              "vr": "TM", "vm": "1",   "desc": "Study Time"},
    (0x0008, 0x0031): {"keyword": "SeriesTime",             "vr": "TM", "vm": "1",   "desc": "Series Time"},
    (0x0008, 0x0050): {"keyword": "AccessionNumber",        "vr": "SH", "vm": "1",   "desc": "Accession Number"},
    (0x0008, 0x0060): {"keyword": "Modality",               "vr": "CS", "vm": "1",   "desc": "Modality"},
    (0x0008, 0x0070): {"keyword": "Manufacturer",           "vr": "LO", "vm": "1",   "desc": "Manufacturer"},
    (0x0008, 0x0080): {"keyword": "InstitutionName",        "vr": "LO", "vm": "1",   "desc": "Institution Name"},
    (0x0008, 0x0090): {"keyword": "ReferringPhysicianName", "vr": "PN", "vm": "1",   "desc": "Referring Physician's Name"},
    (0x0008, 0x1030): {"keyword": "StudyDescription",       "vr": "LO", "vm": "1",   "desc": "Study Description"},
    (0x0008, 0x103E): {"keyword": "SeriesDescription",      "vr": "LO", "vm": "1",   "desc": "Series Description"},
    (0x0010, 0x0010): {"keyword": "PatientName",            "vr": "PN", "vm": "1",   "desc": "Patient's Name"},
    (0x0010, 0x0020): {"keyword": "PatientID",              "vr": "LO", "vm": "1",   "desc": "Patient ID"},
    (0x0010, 0x0030): {"keyword": "PatientBirthDate",       "vr": "DA", "vm": "1",   "desc": "Patient's Birth Date"},
    (0x0010, 0x0040): {"keyword": "PatientSex",             "vr": "CS", "vm": "1",   "desc": "Patient's Sex"},
    (0x0010, 0x1030): {"keyword": "PatientWeight",          "vr": "DS", "vm": "1",   "desc": "Patient's Weight"},
    (0x0018, 0x0015): {"keyword": "BodyPartExamined",       "vr": "CS", "vm": "1",   "desc": "Body Part Examined"},
    (0x0018, 0x0050): {"keyword": "SliceThickness",         "vr": "DS", "vm": "1",   "desc": "Slice Thickness"},
    (0x0018, 0x0081): {"keyword": "EchoTime",               "vr": "DS", "vm": "1",   "desc": "Echo Time"},
    (0x0020, 0x000D): {"keyword": "StudyInstanceUID",       "vr": "UI", "vm": "1",   "desc": "Study Instance UID"},
    (0x0020, 0x000E): {"keyword": "SeriesInstanceUID",      "vr": "UI", "vm": "1",   "desc": "Series Instance UID"},
    (0x0020, 0x0010): {"keyword": "StudyID",                "vr": "SH", "vm": "1",   "desc": "Study ID"},
    (0x0020, 0x0011): {"keyword": "SeriesNumber",           "vr": "IS", "vm": "1",   "desc": "Series Number"},
    (0x0020, 0x0013): {"keyword": "InstanceNumber",         "vr": "IS", "vm": "1",   "desc": "Instance Number"},
    (0x0028, 0x0002): {"keyword": "SamplesPerPixel",        "vr": "US", "vm": "1",   "desc": "Samples per Pixel"},
    (0x0028, 0x0004): {"keyword": "PhotometricInterpretation", "vr": "CS", "vm": "1", "desc": "Photometric Interpretation"},
    (0x0028, 0x0010): {"keyword": "Rows",                   "vr": "US", "vm": "1",   "desc": "Rows"},
    (0x0028, 0x0011): {"keyword": "Columns",                "vr": "US", "vm": "1",   "desc": "Columns"},
    (0x0028, 0x0100): {"keyword": "BitsAllocated",          "vr": "US", "vm": "1",   "desc": "Bits Allocated"},
    (0x0028, 0x0101): {"keyword": "BitsStored",             "vr": "US", "vm": "1",   "desc": "Bits Stored"},
    (0x0028, 0x0102): {"keyword": "HighBit",                "vr": "US", "vm": "1",   "desc": "High Bit"},
    (0x0028, 0x0103): {"keyword": "PixelRepresentation",    "vr": "US", "vm": "1",   "desc": "Pixel Representation"},
}

# Type-2 mandatory tags that must be present (may be empty)
TYPE2_REQUIRED = {
    (0x0008, 0x0020), (0x0008, 0x0030), (0x0008, 0x0050),
    (0x0008, 0x0060), (0x0010, 0x0010), (0x0010, 0x0020),
    (0x0010, 0x0030), (0x0010, 0x0040), (0x0020, 0x000D),
    (0x0020, 0x000E), (0x0020, 0x0010), (0x0020, 0x0011),
    (0x0020, 0x0013),
}

# Allowed VR values for validation
VR_TYPES = {
    "AE", "AS", "AT", "CS", "DA", "DS", "DT", "FL", "FD",
    "IS", "LO", "LT", "OB", "OD", "OF", "OL", "OW", "PN",
    "SH", "SL", "SQ", "SS", "ST", "SV", "TM", "UC", "UI",
    "UL", "UN", "UR", "US", "UT", "UV",
}

# Modality codes from DICOM PS3.3
VALID_MODALITIES = {
    "CR", "CT", "MR", "NM", "US", "OT", "BI", "DG", "ES",
    "LS", "PT", "RG", "ST", "TG", "XA", "RF", "RTIMAGE",
    "RTDOSE", "RTSTRUCT", "RTPLAN", "RTRECORD", "HC", "DX",
    "MG", "IO", "PX", "GM", "SM", "XC", "PR", "AU", "ECG",
    "EPS", "HD", "SR", "IVUS", "OP", "SMR", "AR", "RESP",
    "KO", "SEG", "REG", "FID", "RWV", "DOC", "OAM", "OCT",
    "IVOCT", "OPT", "OPTBSV", "OPTENF", "OPV", "OSS", "POS",
    "BDUS", "EEG", "EMG", "EOG", "DIC", "PLAN", "HLVS",
}

PATIENT_SEX_VALUES = {"M", "F", "O", ""}


class Severity(Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class ValidationIssue:
    tag: str
    severity: Severity
    code: str
    message: str
    suggestion: str = ""

    def to_dict(self) -> Dict[str, str]:
        return {
            "tag": self.tag,
            "severity": self.severity.value,
            "code": self.code,
            "message": self.message,
            "suggestion": self.suggestion,
        }

    def __repr__(self) -> str:
        return f"ValidationIssue(tag='{self.tag}', severity={self.severity.value}, code='{self.code}')"

    def __str__(self) -> str:
        icon = {"ERROR": "❌", "WARNING": "⚠️ ", "INFO": "ℹ️ "}[self.severity.value]
        lines = [f"  {icon} [{self.severity.value}] {self.tag}: {self.message}"]
        if self.suggestion:
            lines.append(f"     💡 {self.suggestion}")
        return "\n".join(lines)


@dataclass
class ValidationReport:
    total_tags: int = 0
    valid_tags: int = 0
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.ERROR]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.WARNING]

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def summary(self) -> str:
        status = "✅ VALID" if self.is_valid else "❌ INVALID"
        return (
            f"{status} | "
            f"{self.total_tags} tags | "
            f"{self.valid_tags} valid | "
            f"{len(self.errors)} errors | "
            f"{len(self.warnings)} warnings"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.is_valid,
            "total_tags": self.total_tags,
            "valid_tags": self.valid_tags,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "issues": [i.to_dict() for i in self.issues],
        }

    def __repr__(self) -> str:
        return f"ValidationReport(total={self.total_tags}, issues={len(self.issues)}, valid={self.is_valid})"


def _parse_tag_str(tag_str: str) -> Optional[Tuple[int, int]]:
    """Parse tag string like '(0008,0016)' or '0008,0016' or '00080016'.

    Returns (group, element) tuple or None if invalid.
    """
    tag_str = tag_str.strip().replace("(", "").replace(")", "").replace(" ", "")
    if "," in tag_str:
        parts = tag_str.split(",")
        if len(parts) == 2:
            try:
                return (int(parts[0], 16), int(parts[1], 16))
            except ValueError:
                return None
    elif len(tag_str) == 8:
        try:
            return (int(tag_str[:4], 16), int(tag_str[4:], 16))
        except ValueError:
            return None
    return None


def _format_tag(group: int, element: int) -> str:
    return f"({group:04X},{element:04X})"


# ---------------------------------------------------------------------------
# Value Representation validators
# ---------------------------------------------------------------------------

def _validate_vr_da(value: str) -> bool:
    """YYYYMMDD format."""
    value = value.strip()
    if not value:
        return True
    if len(value) != 8:
        return False
    try:
        y, m, d = int(value[:4]), int(value[4:6]), int(value[6:])
        return 1 <= m <= 12 and 1 <= d <= 31 and y >= 1900
    except ValueError:
        return False


def _validate_vr_tm(value: str) -> bool:
    """HHMMSS.FFFFFF format."""
    value = value.strip()
    if not value:
        return True
    value = value.split(".")[0]
    if not value.isdigit():
        return False
    if len(value) not in {2, 4, 6}:
        return False
    hh = int(value[:2])
    mm = int(value[2:4]) if len(value) >= 4 else 0
    ss = int(value[4:6]) if len(value) >= 6 else 0
    return 0 <= hh <= 23 and 0 <= mm <= 59 and 0 <= ss <= 59


def _validate_vr_ui(value: str) -> bool:
    """UID: digits and dots, max 64 chars, no leading zeros in components."""
    if not value:
        return True
    value = value.strip().rstrip("\x00")
    if len(value) > 64:
        return False
    components = value.split(".")
    for c in components:
        if not c:
            return False
        if not c.isdigit():
            return False
        if len(c) > 1 and c[0] == "0":
            return False
    return True


def _validate_vr_ds(value: str) -> bool:
    """Decimal string."""
    if not value:
        return True
    try:
        float(value.strip())
        return True
    except ValueError:
        return False


def _validate_vr_is(value: str) -> bool:
    """Integer string."""
    if not value:
        return True
    try:
        int(value.strip())
        return True
    except ValueError:
        return False


def _validate_vr_cs(value: str) -> bool:
    """Code string: uppercase letters, digits, spaces, underscores."""
    if not value:
        return True
    return all(c.isupper() or c.isdigit() or c in (" ", "_") for c in value.strip())


VR_VALIDATORS = {
    "DA": _validate_vr_da,
    "TM": _validate_vr_tm,
    "UI": _validate_vr_ui,
    "DS": _validate_vr_ds,
    "IS": _validate_vr_is,
    "CS": _validate_vr_cs,
}


# ---------------------------------------------------------------------------
# Main validator
# ---------------------------------------------------------------------------

class DicomTagValidator:
    """Validate a dictionary of DICOM tags against the DICOM PS3.6 standard."""

    def __init__(self, strict: bool = False):
        self.strict = strict

    def validate(self, tags: Dict[str, Any]) -> ValidationReport:
        """Validate a dict of {tag_str: value} pairs.

        Args:
            tags: Dictionary mapping tag strings to values,
                  e.g. {"(0008,0016)": "1.2.840.10008.5.1.4.1.1.2", ...}

        Returns:
            ValidationReport with all detected issues.
        """
        report = ValidationReport(total_tags=len(tags))
        parsed: Dict[Tuple[int, int], Any] = {}
        issues = report.issues

        # Parse and validate each tag
        for tag_str, value in tags.items():
            parsed_tag = _parse_tag_str(str(tag_str))
            if parsed_tag is None:
                issues.append(ValidationIssue(
                    tag=str(tag_str),
                    severity=Severity.ERROR,
                    code="INVALID_TAG_FORMAT",
                    message=f"Cannot parse tag '{tag_str}'",
                    suggestion="Use format (GGGG,EEEE) e.g. (0008,0016)",
                ))
                continue

            parsed[parsed_tag] = value
            tag_label = _format_tag(*parsed_tag)
            registry_entry = DICOM_TAG_REGISTRY.get(parsed_tag)

            # Check if tag is in registry
            if registry_entry is None:
                if self.strict:
                    issues.append(ValidationIssue(
                        tag=tag_label,
                        severity=Severity.WARNING,
                        code="UNKNOWN_TAG",
                        message="Tag not found in DICOM PS3.6 registry",
                        suggestion="Verify this is a valid private or standard DICOM tag",
                    ))
                report.valid_tags += 1
                continue

            vr = registry_entry["vr"]
            str_value = str(value) if value is not None else ""

            # VR format validation
            validator_fn = VR_VALIDATORS.get(vr)
            if validator_fn and not validator_fn(str_value):
                issues.append(ValidationIssue(
                    tag=tag_label,
                    severity=Severity.ERROR,
                    code="INVALID_VR_FORMAT",
                    message=f"Value '{str_value}' does not conform to VR={vr} ({registry_entry['keyword']})",
                    suggestion=self._vr_hint(vr),
                ))
                continue

            # Semantic validations
            semantic_issues = self._semantic_validate(parsed_tag, str_value, registry_entry)
            issues.extend(semantic_issues)

            if not any(i.severity == Severity.ERROR and i.tag == tag_label for i in semantic_issues):
                report.valid_tags += 1

        # Type-2 tag presence checks
        for required_tag in TYPE2_REQUIRED:
            tag_label = _format_tag(*required_tag)
            if required_tag not in parsed:
                entry = DICOM_TAG_REGISTRY.get(required_tag, {})
                issues.append(ValidationIssue(
                    tag=tag_label,
                    severity=Severity.WARNING,
                    code="MISSING_TYPE2_TAG",
                    message=f"Type-2 tag missing: {entry.get('keyword', 'Unknown')} — {entry.get('desc', '')}",
                    suggestion="Add this tag (value may be empty) for DICOM compliance",
                ))

        return report

    def _semantic_validate(
        self,
        tag: Tuple[int, int],
        value: str,
        entry: Dict[str, str],
    ) -> List[ValidationIssue]:
        """Domain-level semantic validation rules."""
        issues: List[ValidationIssue] = []
        tag_label = _format_tag(*tag)

        if tag == (0x0008, 0x0060):  # Modality
            upper = value.upper().strip()
            if upper and upper not in VALID_MODALITIES:
                issues.append(ValidationIssue(
                    tag=tag_label,
                    severity=Severity.WARNING,
                    code="UNKNOWN_MODALITY",
                    message=f"Modality '{value}' is not a recognised DICOM modality code",
                    suggestion=f"Common values: CT, MR, US, CR. See PS3.3 C.7.3.1.1.1",
                ))

        elif tag == (0x0010, 0x0040):  # PatientSex
            if value.upper() not in PATIENT_SEX_VALUES:
                issues.append(ValidationIssue(
                    tag=tag_label,
                    severity=Severity.ERROR,
                    code="INVALID_PATIENT_SEX",
                    message=f"PatientSex must be 'M', 'F', 'O', or empty — got '{value}'",
                    suggestion="Use M (male), F (female), O (other), or leave empty",
                ))

        elif tag in {(0x0008, 0x0016), (0x0008, 0x0018), (0x0020, 0x000D), (0x0020, 0x000E)}:
            # UID completeness
            stripped = value.strip().rstrip("\x00")
            if not stripped:
                issues.append(ValidationIssue(
                    tag=tag_label,
                    severity=Severity.ERROR,
                    code="EMPTY_REQUIRED_UID",
                    message=f"'{entry['keyword']}' UID cannot be empty",
                    suggestion="Generate a valid DICOM UID using pydicom.uid.generate_uid()",
                ))

        return issues

    @staticmethod
    def _vr_hint(vr: str) -> str:
        hints = {
            "DA": "Use YYYYMMDD format (e.g. 20240101)",
            "TM": "Use HHMMSS or HHMM or HH format (e.g. 143023)",
            "UI": "UID must be digits and dots, max 64 chars",
            "DS": "Decimal string (e.g. '3.14' or '-1.5e-3')",
            "IS": "Integer string (e.g. '42' or '-7')",
            "CS": "Code string: uppercase letters, digits, spaces, underscores only",
        }
        return hints.get(vr, f"See DICOM PS3.5 for VR={vr} format rules")


# ---------------------------------------------------------------------------
# HL7 Integration Helper
# ---------------------------------------------------------------------------

class HL7DicomMapper:
    """Map HL7 v2.x PID segment fields to DICOM patient module tags."""

    FIELD_MAP = {
        "PID.3":  (0x0010, 0x0020),  # PatientID        <- PID-3 Patient ID
        "PID.5":  (0x0010, 0x0010),  # PatientName      <- PID-5 Patient Name
        "PID.7":  (0x0010, 0x0030),  # PatientBirthDate <- PID-7 Date of Birth
        "PID.8":  (0x0010, 0x0040),  # PatientSex       <- PID-8 Administrative Sex
        "PID.10": (0x0010, 0x2160),  # EthnicGroup      <- PID-10 Ethnic Group
        "PID.11": (0x0010, 0x0040),  # (also sex)
        "PID.13": (0x0010, 0x1040),  # PatientAddress   <- PID-13 Phone Number (Home) - approximate map
        "PID.19": (0x0010, 0x0020),  # SSN Number       <- PID-19 SSN (map to PatientID)
    }

    SEX_MAP = {"M": "M", "F": "F", "U": "O", "O": "O", "A": "O", "N": "O", "C": "O"}

    def from_hl7_pid(self, pid_segment: Dict[str, str]) -> Dict[str, str]:
        """Convert HL7 PID segment dict to DICOM tag dict.

        Args:
            pid_segment: Dict like {"PID.3": "12345", "PID.5": "Doe^John", ...}

        Returns:
            DICOM tag dict ready to pass into DicomTagValidator.validate()
        """
        dicom: Dict[str, str] = {}
        for field_name, value in pid_segment.items():
            tag = self.FIELD_MAP.get(field_name)
            if tag is None:
                continue
            tag_str = _format_tag(*tag)
            if field_name in {"PID.8", "PID.11"}:
                value = self.SEX_MAP.get(value.upper(), "O")
            dicom[tag_str] = value
        return dicom


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_checklist(report: ValidationReport) -> None:
    print("\n" + "─" * 40)
    print("  DICOM VALIDATION CHECKLIST")
    print("─" * 40)
    
    # Required categories
    checks = [
        ("Structure", report.is_valid),
        ("Group 0008 (Study)", not any(i.tag.startswith("(0008") for i in report.errors)),
        ("Group 0010 (Patient)", not any(i.tag.startswith("(0010") for i in report.errors)),
        ("Group 0020 (Instance)", not any(i.tag.startswith("(0020") for i in report.errors)),
        ("VR Compliance", not any(i.code == "INVALID_VR_FORMAT" for i in report.errors)),
    ]
    
    for label, passed in checks:
        icon = "✅" if passed else "❌"
        print(f"  {icon} {label:<25}")
        
    print("─" * 40)
    print(f"  Result: {'PASS' if report.is_valid else 'FAIL'}")
    print("─" * 40 + "\n")


def print_report(report: ValidationReport, verbose: bool = True) -> None:
    print("\n" + "=" * 60)
    print("  DICOM Tag Validation Report")
    print("=" * 60)
    print(f"  {report.summary()}")
    print("=" * 60)

    if not report.issues:
        print("  ✅ No issues found!")
    else:
        by_severity = {s: [] for s in Severity}
        for issue in report.issues:
            by_severity[issue.severity].append(issue)

        for severity in [Severity.ERROR, Severity.WARNING, Severity.INFO]:
            group = by_severity[severity]
            if group:
                print(f"\n  {severity.value}S ({len(group)}):")
                print("  " + "-" * 56)
                for issue in group:
                    print(issue)

    print("=" * 60 + "\n")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _load_json_tags(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")
    with p.open(encoding="utf-8") as f:
        return json.load(f)


def main(argv: Optional[List[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="dicom-tag-validator",
        description="Validate DICOM tags against the DICOM PS3.6 standard",
    )
    subparsers = parser.add_subparsers(dest="command", help="Command")

    # validate command
    val = subparsers.add_parser("validate", help="Validate a JSON file of DICOM tags")
    val.add_argument("file", help="JSON file with DICOM tags ({tag: value, ...})")
    val.add_argument("--strict", action="store_true", help="Warn on unknown/private tags")
    val.add_argument("--json", action="store_true", dest="json_output", help="Output results as JSON")
    val.add_argument("--checklist", action="store_true", help="Output results as a concise checklist")
    val.add_argument("--exit-code", action="store_true", help="Return exit code 1 on errors")

    # demo command
    demo = subparsers.add_parser("demo", help="Run a built-in demo with sample tags")
    demo.add_argument("--checklist", action="store_true", help="Output results as a concise checklist")

    # list-tags command
    lt = subparsers.add_parser("list-tags", help="List all tags in the registry")
    lt.add_argument("--filter", default="", help="Filter by keyword substring")

    args = parser.parse_args(argv)

    if args.command == "validate":
        try:
            tags = _load_json_tags(args.file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"❌ {e}", file=sys.stderr)
            return 1

        validator = DicomTagValidator(strict=args.strict)
        report = validator.validate(tags)

        if args.json_output:
            print(json.dumps(report.to_dict(), indent=2))
        elif args.checklist:
            print_checklist(report)
        else:
            print_report(report)

        if args.exit_code and not report.is_valid:
            return 1
        return 0

    elif args.command == "demo":
        print("Running demo validation with sample DICOM tags...")
        sample_tags = {
            "(0008,0016)": "1.2.840.10008.5.1.4.1.1.2",  # CT Image Storage
            "(0008,0018)": "1.2.3.4.5.6789",
            "(0008,0020)": "20240101",
            "(0008,0030)": "143023",
            "(0008,0050)": "ACC001",
            "(0008,0060)": "CT",
            "(0010,0010)": "Doe^John^A",
            "(0010,0020)": "PID-12345",
            "(0010,0030)": "19850315",
            "(0010,0040)": "M",
            "(0020,000D)": "1.2.840.99999.1.2",
            "(0020,000E)": "1.2.840.99999.1.2.1",
            "(0020,0010)": "STU001",
            "(0020,0011)": "1",
            "(0020,0013)": "42",
            # Intentional errors for demo:
            "(0008,0021)": "20241399",       # Bad date (month 13)
            "(0010,0040)": "X",              # Invalid sex code
            "(0008,XXXX)": "invalid-tag",    # Unparseable tag
        }

        validator = DicomTagValidator(strict=True)
        report = validator.validate(sample_tags)
        
        if args.checklist:
            print_checklist(report)
        else:
            print_report(report)
        return 0

    elif args.command == "list-tags":
        print(f"\n{'Tag':^15} {'Keyword':^35} {'VR':^6} {'Description'}")
        print("-" * 80)
        for (g, e), info in sorted(DICOM_TAG_REGISTRY.items()):
            keyword = info["keyword"]
            if args.filter and args.filter.lower() not in keyword.lower():
                continue
            print(f"({g:04X},{e:04X})  {keyword:<35} {info['vr']:^6}  {info['desc']}")
        return 0

    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
