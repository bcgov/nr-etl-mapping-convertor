from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple



def canon(col: str) -> str:
    return col.strip()

# ─────────────────────────── regex patterns ────────────────────────────
_COL = r"(?!IS\b|NOT\b)([A-Z][A-Z0-9_]{2,})"

CMP_PAT       = re.compile(rf"^{_COL}\s*(>=|<=|>|<)\s*{_COL}\b", re.I)
NULL_PAT      = re.compile(rf"^{_COL}\s+IS\s+(NOT\s+)?NULL\b", re.I)
STR_EQ_PAT    = re.compile(rf"^{_COL}\s*=\s*'([^']+)'", re.I)
BARE_EQ_PAT   = re.compile(rf"^{_COL}\s*=\s*([A-Z0-9]+)", re.I)

PATTERNS: List[Tuple[re.Pattern, callable]] = [
    (CMP_PAT,     lambda m: {"attr": canon(m.group(1)),
                             "op":   m.group(2),
                             "other_attr": canon(m.group(3))}),
    (NULL_PAT,    lambda m: {"attr": canon(m.group(1)),
                             "op":   "not_null" if m.group(2) else "null"}),
    (STR_EQ_PAT,  lambda m: {"attr": canon(m.group(1)),
                             "op":   "=",
                             "value": m.group(2)}),
    (BARE_EQ_PAT, lambda m: {"attr": canon(m.group(1)),
                             "op":   "=",
                             "value": m.group(2)}),
]

# whitespace that *starts* a new clause
SPLIT_WS = re.compile(rf"\s+(?={_COL}\s*(?:IS\b|>=|<=|>|<|=))", re.I)

# ───────────────────────── helper functions ────────────────────────────
def _normalise(txt: str) -> str:
    """Tidy a raw rule fragment."""
    txt = txt.strip()
    txt = re.sub(r"[,\s]+$", "", txt) 
    txt = re.sub(r"<\s*=", "<=", txt)
    txt = re.sub(r">\s*=", ">=", txt)
    txt = re.sub(r"\bIS\s+NOT\s+NUL\b", "IS NOT NULL", txt, flags=re.I)
    return re.sub(r"\b(?:AND|OR)\b\s*$", "", txt, flags=re.I).strip()

def tokenise(fragment: str) -> List[Dict]:
    """Return a list of parsed mini-clauses for one raw fragment."""
    out: List[Dict] = []
    queue = [_normalise(fragment)]

    while queue:
        frag = queue.pop(0)
        if not frag:
            continue

        for pat, build in PATTERNS:
            m = pat.match(frag)
            if m:
                out.append(build(m))
                remainder = _normalise(frag[m.end():])
                if remainder:
                    queue.insert(0, remainder)
                break
        else:                                                   # no match
            parts = [p.strip() for p in SPLIT_WS.split(frag) if p.strip()]
            if len(parts) == 1:                                 # give up → regex
                out.append({"attr": canon(frag), "op": "regex", "value": ".*"})
            else:
                queue = parts + queue
    return out

def parse_rule_cell(cell: str) -> Dict:
    """Convert multi-line Rules cell → nested AND/OR JSON structure."""
    and_nodes: List[Dict] = []

    for raw in (ln for ln in cell.splitlines() if ln.strip()):
        upper = raw.upper()
        if " OR " in upper:
            parts = re.split(r"\s+OR\s+", raw, flags=re.I)
            or_list = [n for p in parts for n in tokenise(p)]
            and_nodes.append({"or": or_list})
        else:
            and_nodes.extend(tokenise(raw))
    return {"logic": {"and": and_nodes}} if and_nodes else {"logic": {"and": []}}

def make_status_key(raw: str) -> str:
    key = re.sub(r"['\"]", "", raw.strip())  # strip quotes/apostrophes
    key = re.sub(r"\s+", "_", key)           # any whitespace → _
    key = re.sub(r"_+", "_", key)            # collapse dup underscores
    return key

# ─────────────────────── CSV ➜ JSON converter ──────────────────────────
def convert(csv_path: Path, json_path: Path) -> None:
    out: Dict[str, Dict] = {}

    with csv_path.open(newline="", encoding="utf-8") as fh:
        rdr = csv.DictReader(fh)
        if not rdr.fieldnames or len(rdr.fieldnames) < 3:
            sys.exit("CSV needs at least 3 columns: Status, Rules, StartDate…")

        status_col = rdr.fieldnames[0]
        rules_col  = rdr.fieldnames[1]
        start_col  = rdr.fieldnames[2]
        end_col    = rdr.fieldnames[3] if len(rdr.fieldnames) > 3 else None

        for row in rdr:
            base_key = make_status_key(row[status_col])
            rule_text = row.get(rules_col, "") or ""

            entry: Dict[str, object] = {}

            if s := row.get(start_col, "").strip():
                entry["start_date"] = {"attr": canon(s), "op": "not_null"}
            if end_col and (e := row.get(end_col, "").strip()):
                entry["end_date"] = {"attr": canon(e), "op": "not_null"}

            entry.update(parse_rule_cell(rule_text))

            key = base_key
            suffix = 1
            while key in out:
                suffix += 1
                key = f"{base_key}_{suffix}"
            out[key] = entry

    json_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[csv2json] wrote {json_path}  ({len(out)} status blocks)")

# ───────────────────────────── CLI ──────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: csv2json_rules.py <rules.csv> <rules.json>")
    convert(Path(sys.argv[1]), Path(sys.argv[2]))
