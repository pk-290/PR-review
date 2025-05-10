import re
from typing import List, Dict

HUNK_REGEX = re.compile(
    r"^diff --git a/(.+?) b/(.+?)$(?:.*?)(?=^diff --git|\Z)", re.M|re.S
)

def split_diff_by_file(diff_text: str) -> List[Dict]:
    parts = []
    for m in HUNK_REGEX.finditer(diff_text):
        parts.append({
            "filename": m.group(2),
            "hunk": m.group(0)
        })
    return parts
