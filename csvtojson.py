import csv, json, re, sys, pathlib

# ------------ helpers ------------------------------------------------------
def parse_condition(txt: str):
    txt = txt.strip().rstrip(',')
    # 1) >=, <=, >, <  (column-to-column)
    m = re.match(r"(\w+)\s*(>=|<=|>|<)\s*(\w+)", txt, re.I)
    if m:
        col, op, other = m.groups()
        return {"attr": col, "op": op, "other_attr": other}

    # 2) IS NOT NULL / IS NULL
    m = re.match(r"(\w+)\s+IS\s+(NOT\s+)?NULL", txt, re.I)
    if m:
        col, notnull = m.groups()
        return {"attr": col, "op": "not_null" if notnull else "null"}

    # 3) equality with quoted value
    m = re.match(r"(\w+)\s*=\s*'([^']+)'", txt)
    if m:
        col, val = m.groups()
        return {"attr": col, "op": "=", "value": val}

    # 4) equality without quotes
    m = re.match(r"(\w+)\s*=\s*(\S+)", txt)
    if m:
        col, val = m.groups()
        return {"attr": col, "op": "=", "value": val}

    # fallback → regex
    return {"attr": txt, "op": "regex", "value": ".*"}


def parse_rule_cell(cell: str):
    """
    Returns a dict:  { "logic": {...} }
    If a line contains " OR ", split into OR conditions; else AND.
    """
    # split on real newlines first
    lines = [l for l in cell.splitlines() if l.strip()]
    and_nodes = []
    for line in lines:
        if " OR " in line.upper():
            or_parts = [p.strip() for p in re.split(r"\s+OR\s+", line, flags=re.I)]
            or_nodes = [parse_condition(p) for p in or_parts if p]
            and_nodes.append({"or": or_nodes})
        else:
            and_nodes.append(parse_condition(line))
    return {"logic": {"and": and_nodes}}

# ------------ main ---------------------------------------------------------
def convert(csv_path: str, json_path: str):
    out: dict[str, dict] = {}
    with open(csv_path, newline='', encoding='utf-8') as fh:
        rdr = csv.DictReader(fh)
        # Expect header: Status, Rules, StartDate, EndDate
        status_col, rules_col = rdr.fieldnames[0], rdr.fieldnames[1]
        date_cols = rdr.fieldnames[2:]
        for row in rdr:
            status_key = row[status_col].strip()
            rules_cell = row[rules_col] or ''
            # read optional date columns
            start_col = row.get(rdr.fieldnames[2], '').strip()
            end_col = row.get(rdr.fieldnames[3], '').strip()

            # normalize key
            # out_key = status_key.lower().replace(" ", "_")
            # out_key = out_key.replace("(", "").replace(")", "")
            out_key = status_key.strip()  # preserve original formatting


            # build entry
            entry: dict[str, object] = {}
            if start_col:
                entry['start_date'] = {"attr": start_col, "op": "not_null"}
            if end_col:
                entry['end_date'] = {"attr": end_col, "op": "not_null"}

            # parse logic rules
            logic = parse_rule_cell(rules_cell).get('logic', {})
            entry['logic'] = logic

            out[out_key] = entry

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"[csv2json]  wrote  {json_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: csv2json_rules.py <rules.csv> <rules.json>")
    convert(sys.argv[1], sys.argv[2])
    # convert(pathlib.Path(__file__).parent / "rules.csv", "rules.json")