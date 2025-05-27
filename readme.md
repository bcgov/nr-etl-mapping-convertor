# Permitting Data ETL Mapping Tool

This repository provides two Python scripts that convert human-readable CSV mapping rules into structured, machine-readable JSON used by an ETL engine for permitting data. The output JSON is designed to integrate with downstream data pipelines such as those conforming to NR-PIES specifications.

---

## Overview

### Scripts

* **`csv2json_rules.py`**: Converts rule definitions into structured logical conditions.
* **`lifecycle_map_converter.py`**: Converts a CSV file that defines lifecycle term mappings into a standardized JSON format.

---

## Features

### `csv2json_rules.py`

* Parses conditional rules (AND, OR, =, IS NULL, comparisons).
* Handles optional start and end date fields.
* Supports nested logic for rule evaluation.
* Produces output JSON usable for programmatic decision workflows.

### `lifecycle_map_converter.py`

* Converts status term mappings into structured JSON.
* Enforces specific order for status keys.
* Separates metadata fields from code set mappings.

---

## Input Format

### Rules CSV (`csv2json_rules.py`)

| Status          | Rules                               | StartDate   | EndDate    |
| --------------- | ----------------------------------- | ----------- | ---------- |
| Application 123 | applicant\_type = 'Private'         | 2023/01/01  | 2024/01/01 |

### Lifecycle Map CSV (`lifecycle_map_converter.py`)

| terms        | STATUS   | status\_code | status\_description |  PHASE | STAGE | STATE |
| ------------ | -------- | ------------ | ------------------- |  ----- | ----- | ----- |
| application1 | Approved | STATE\_1     | Approved Phase      |  ...   | ...   | ...   |

---

## Usage

### Convert Rules to JSON

```bash
python csv2json_rules.py rules.csv rules.json
```

### Convert Lifecycle Mapping to JSON

```bash
python lifecycle_map_converter.py
```

---

## Output Example

### rules.json

```json
{
  "application_approved": {
    "start_date": { "attr": "created_at", "op": "not_null" },
    "end_date": { "attr": "closed_at", "op": "not_null" },
    "logic": {
      "and": [
        { "attr": "applicant_type", "op": "=", "value": "Private" },
        { "or": [
          { "attr": "amount", "op": ">", "value": "10000" },
          { "attr": "priority", "op": "=", "value": "High" }
        ]}
      ]
    }
  }
}
```

### lifecycle\_map.json

```json
{
  "application1": {
    "status": {
      "STATUS": "Approved",
      "status_code": "STATE_1",
      "status_description": "Approved Phase"
    },
    "code_set": {
      "PHASE": "Submission",
      "STAGE": "Review",
      "STATE": "STATE_1"
    }
  }
}
```

---

## Contact

For questions or contributions, please open an issue or contact the maintainers.
