import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LABELS_PATH = BASE_DIR / "route_labels_ko.json"

with open(LABELS_PATH, encoding="utf-8") as f:
    ROUTE_LABELS = json.load(f)
