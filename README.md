# 🏥 dicom-tag-validator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-pytest-brightgreen.svg)](tests/)
[![DICOM PS3.6](https://img.shields.io/badge/DICOM-PS3.6-blue.svg)](https://dicom.nema.org)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

> A Python CLI tool for validating DICOM tags against the DICOM standard (PS3.6) with detailed error reporting, VR format checking, semantic validation, and HL7 v2.x integration support.

---

## ✨ Features

- ✅ **DICOM PS3.6 Registry** — validates 35+ standard tags with VR, VM, and descriptions
- ✅ **VR Format Validation** — DA, TM, UI, DS, IS, CS value conformance checking
- ✅ **Semantic Rules** — modality codes, patient sex, UID completeness, Type-2 presence
- ✅ **HL7 v2.x Mapper** — converts PID segment fields to DICOM patient module tags
- ✅ **Rich CLI** — `validate`, `demo`, `list-tags` subcommands with JSON output option
- ✅ **Exit Code Support** — CI/CD integration via `--exit-code` flag
- ✅ **40+ Unit Tests** — pytest suite with 100% coverage of core logic

---

## 📦 Installation

```bash
git clone https://github.com/DinhLucent/dicom-tag-validator.git
cd dicom-tag-validator
pip install -r requirements.txt
```

---

## 🚀 Quick Start

### Validate a JSON file of DICOM tags

```bash
python src/main.py validate examples/sample_tags.json
```

### Run the built-in demo (shows error detection)

```bash
python src/main.py demo
```

### List all tags in the registry

```bash
python src/main.py list-tags --filter Patient
```

### JSON output for CI/CD integration

```bash
python src/main.py validate tags.json --json --exit-code
```

---

## 📋 Input Format

Create a JSON file with DICOM tags in standard `(GGGG,EEEE)` format:

```json
{
  "(0008,0016)": "1.2.840.10008.5.1.4.1.1.2",
  "(0008,0020)": "20240101",
  "(0008,0060)": "CT",
  "(0010,0010)": "Doe^John",
  "(0010,0020)": "PID-12345",
  "(0010,0040)": "M",
  "(0020,000D)": "1.2.840.99999.1.0"
}
```

---

## 📊 Sample Output

```
============================================================
  DICOM Tag Validation Report
============================================================
  ❌ INVALID | 15 tags | 13 valid | 2 errors | 1 warnings
============================================================

  ERRORS (2):
  ──────────────────────────────────────────────────────────
  ❌ [ERROR] (0008,0021): Value '20241399' does not conform to VR=DA (SeriesDate)
     💡 Use YYYYMMDD format (e.g. 20240101)
  ❌ [ERROR] (0010,0040): PatientSex must be 'M', 'F', 'O', or empty — got 'X'
     💡 Use M (male), F (female), O (other), or leave empty

  WARNINGS (1):
  ──────────────────────────────────────────────────────────
  ⚠️  [WARNING] (0008,0021): Type-2 tag missing ...
============================================================
```

---

## 🔗 HL7 Integration

Convert HL7 v2.x PID segment fields to DICOM tags:

```python
from src.main import HL7DicomMapper, DicomTagValidator

mapper = HL7DicomMapper()
pid_segment = {
    "PID.3": "PAT-001",
    "PID.5": "Doe^Jane",
    "PID.7": "19900101",
    "PID.8": "F",
}

dicom_tags = mapper.from_hl7_pid(pid_segment)
validator = DicomTagValidator()
report = validator.validate(dicom_tags)
print(report.summary())
```

---

## 🏗️ Project Structure

```
dicom-tag-validator/
├── src/
│   └── main.py          # Core validator, HL7 mapper, CLI
├── tests/
│   └── test_validator.py # 40+ pytest test cases
├── examples/
│   └── sample_tags.json  # Example input file
├── docs/                 # Extended documentation
├── requirements.txt
├── setup.py
└── README.md
```

---

## 🧪 Running Tests

```bash
pip install pytest
pytest tests/ -v
```

---

## 🤝 Contributing

Contributions are welcome! Areas of improvement:

- Adding more DICOM tags from PS3.6 Data Dictionary
- Supporting DICOM file (`.dcm`) direct parsing via `pydicom`
- Adding new VR validators (PN, LO, SH format constraints)
- Extending HL7 message type support (OBR, OBX segments)

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<div align="center">Built by <a href="https://github.com/DinhLucent">DinhLucent</a> · Healthcare & Biomedical Tools</div>
