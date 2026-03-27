# dicom-tag-validator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-pytest-brightgreen.svg)](tests/)

> Validates DICOM tags against the PS3.6 standard. Supports VR format checking, semantic validation, and HL7 v2.x PID mapping.

## Features

- **DICOM PS3.6 Registry** — Validates 35+ standard tags with VR/VM conformance
- **VR Validation** — Conformance checking for DA, TM, UI, DS, IS, and CS values
- **Semantic Rules** — Domain logic for modality codes, patient sex, and UID completeness
- **HL7 v2.x Mapper** — Converts PID segments to DICOM patient module tags
- **CLI Workspace** — `validate`, `demo`, and `list-tags` subcommands with JSON output

## Tech Stack

- **Core**: Python 3.9+
- **Testing**: pytest (100% coverage)
- **Standard**: DICOM PS3.6 (2024 Edition)

## Project Structure

```
dicom-tag-validator/
├── src/
│   └── main.py          # Validator logic and HL7 mapper
├── tests/
│   └── test_validator.py # pytest suite
├── examples/
│   └── sample_tags.json  # Example input
└── README.md
```

## Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/DinhLucent/dicom-tag-validator.git
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run validation:
   ```bash
   python src/main.py validate examples/sample_tags.json
   ```

## Demo

Run the built-in demo to see error detection in action:
```bash
python src/main.py demo
```

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---
Built by [DinhLucent](https://github.com/DinhLucent)

