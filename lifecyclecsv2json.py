import csv
import json

# Now a list, in the exact order you want
STATUS_FIELDS = ["STATUS", "status_code", "status_description"]

def csv_to_json(input_csv: str, output_json: str):
    mapping = {}
    with open(input_csv, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize header whitespace
            norm = {k.strip(): v for k, v in row.items()}
            term = norm['terms']

            # Build status in the exact order: STATUS, status_code, status_description
            status_group = {}
            for field in STATUS_FIELDS:
                status_group[field] = norm.get(field, '')

            # Everything else goes into code_set
            code_set = {
                k: v
                for k, v in norm.items()
                if k not in STATUS_FIELDS and k != 'terms'
            }

            mapping[term] = {
                "status": status_group,
                "code_set": code_set
            }

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    csv_to_json('lifecycle_map.csv', 'lifecycle_map.json')
    print("Wrote lifecycle_map.json")
