import csv
import json

# Define the status fields in exact order
STATUS_FIELDS = ["Status", "Status_code", "Status_description"]

def csv_to_json(input_csv: str, output_json: str):
    mapping = {}
    with open(input_csv, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize header and value whitespace
            norm = {k.strip(): v.strip() for k, v in row.items()}
            
            term = norm['Converted_Status']  # Updated key here

            # Build status dictionary
            status_group = {field: norm.get(field, '') for field in STATUS_FIELDS}

            # Everything else goes into code_set
            code_set = {
                k: v
                for k, v in norm.items()
                if k not in STATUS_FIELDS and k != 'Converted_Status'
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
