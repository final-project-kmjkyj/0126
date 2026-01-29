import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "CAR_accident_final_v3.CSV"


def load_rule_table():
    rules = []

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rules.append(row)

    return rules


# Step1에서 import해서 쓰는 전역 룰 테이블
RULE_TABLE = load_rule_table()