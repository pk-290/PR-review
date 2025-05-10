import re
from typing import List, Dict

def run_linters(filename: str, hunk: str) -> List[Dict]:
    """
    Pseudo-linter: returns a list of warnings like:
    [{"line": 3, "type": "style", "msg": "Line too long"}, ...]
    """
    warnings = []
    lines = hunk.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("+"):
            clean = line[1:]
            if len(clean) > 100:
                warnings.append({
                    "line": i + 1,
                    "type": "style",
                    "msg": "Line exceeds 100 characters"
                })
            if re.search(r'print\s*\(', clean):
                warnings.append({
                    "line": i + 1,
                    "type": "debug",
                    "msg": "Debug print statement found"
                })
            if re.search(r'except\s*:\s*$', clean):
                warnings.append({
                    "line": i + 1,
                    "type": "bug",
                    "msg": "Bare except block"
                })
    return warnings
