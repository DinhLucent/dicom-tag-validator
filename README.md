# dicom-tag-validator

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![Tests](https://img.shields.io/badge/Tests-64_passing-brightgreen)
![License](https://img.shields.io/badge/License-MIT-green)

A specialized Python CLI tool and library for validating DICOM metadata against the PS3.6 standard. It ensures clinical data integrity by performing deep Value Representation (VR) validation and structural checks.

## What is DICOM?

DICOM (Digital Imaging and Communications in Medicine) is the global standard for medical imaging and related information. Medical devices (CT, MRI, X-ray) produce DICOM files containing both the image and critical metadata (Patient ID, Study Date, Modality). 

Incorrect tags can lead to clinical errors or system integration failures. This tool validates those tags before they enter your database or VNA (Vendor Neutral Archive).

## Quick Start

### Validate a JSON file

Create a `tags.json` file:
```json
{
  "(0008,0060)": "CT",
  "(0010,0010)": "Doe^John",
  "(0010,0040)": "X"
}
```

Run validation:
```bash
python -m src.main validate tags.json
```

Output:
```
  ❌ [ERROR] (0010,0040): PatientSex must be 'M', 'F', 'O', or empty — got 'X'
     💡 Use M (male), F (female), O (other), or leave empty
```

### Get a concise checklist

```bash
python -m src.main demo --checklist
```

## Features

- **Standard Compliance**: Validates against DICOM PS3.6 Data Dictionary.
- **VR Validation**: Strict format checking for DA (Date), TM (Time), UI (UID), DS (Decimal), etc.
- **HL7 Integration**: Built-in mapper for clinical workflows (PID segment to DICOM tags).
- **Flexible CLI**: Detailed reports, concise checklists, or machine-readable JSON output.
- **Type-2 Checks**: Identifies missing mandatory tags that are allowed to be empty.

## How it works — module by module

### `src/main.py` — Core & CLI

The engine of the tool. It contains the data dictionary, VR validators, and the main validation logic.

#### Programmatic Usage

```python
from src.main import DicomTagValidator

validator = DicomTagValidator(strict=True)

tags = {
    "(0008,0016)": "1.2.840.10008.5.1.4.1.1.2",
    "(0010,0040)": "M"
}

report = validator.validate(tags)

if report.is_valid:
    print(f"Passed: {report.valid_tags} tags valid")
else:
    for error in report.errors:
        print(f"Error in {error.tag}: {error.message}")
```

#### HL7 to DICOM Mapping

Clinical systems often need to populate DICOM metadata from HL7 messages.

```python
from src.main import HL7DicomMapper

mapper = HL7DicomMapper()
pid_segment = {
    "PID.3": "PAT-123",
    "PID.5": "Smith^Jane",
    "PID.8": "F"
}

dicom_tags = mapper.from_hl7_pid(pid_segment)
# Result: {'(0010,0020)': 'PAT-123', '(0010,0010)': 'Smith^Jane', ...}
```

## Project Structure

```
dicom-tag-validator/
├── src/
│   ├── __init__.py
│   └── main.py             # Core validator, registry, and CLI
├── tests/
│   ├── test_validator.py   # 64 tests covering VRs, Mapper, and CLI
│   └── test_placeholder.py
├── examples/
│   └── sample_tags.json
├── requirements.txt
├── LICENSE
└── README.md
```

## Installation

```bash
git clone https://github.com/DinhLucent/dicom-tag-validator.git
cd dicom-tag-validator
pip install -r requirements.txt
```

No external dependencies — runs on vanilla Python 3.9+.

## Running Tests

```bash
# Run all 64 tests
python -m pytest tests/ -v

# Quick summary
python -m pytest tests/ -q
```

## Configuration

The validator uses a built-in subset of the PS3.6 registry. You can filter the tags it knows about via the CLI:

```bash
python -m src.main list-tags --filter Patient
```

## License

MIT License — see [LICENSE](LICENSE)

---
Built by [DinhLucent](https://github.com/DinhLucent)
