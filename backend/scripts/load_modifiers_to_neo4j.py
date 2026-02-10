# backend/scripts/load_modifiers_to_neo4j.py
import json
import os
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv

# 프로젝트 루트의 .env 로드
ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

def main():
    bolt = os.environ["NEO4J_BOLT_URL"]     # 예: bolt://127.0.0.1:7687
    user = os.environ["NEO4J_USER"]         # 예: neo4j
    pw   = os.environ["NEO4J_PASSWORD"]     # 예: password

    # JSON 파일 경로 (원하는 위치로 바꿔도 됨)
    json_path = Path("/home/alpaco/kmjkyj_infra/backend/app/data/modifier_defs.json")
    data = json.loads(json_path.read_text(encoding="utf-8"))

    driver = GraphDatabase.driver(bolt, auth=(user, pw))

    cypher = """
    MERGE (m:Modifier {code: $code})
    SET m.name = $name,
        m.kind = $kind,
        m.range = $range,
        m.apply_rules = $apply_rules,
        m.examples = $examples
    """

    with driver.session() as session:
        for code, obj in data.items():
            session.run(
                cypher,
                code=code,
                name=obj.get("name"),
                kind=obj.get("kind"),
                range=obj.get("range"),
                apply_rules=obj.get("apply_rules", []),
                examples=obj.get("examples", []),
            )

    driver.close()
    print("[OK] Modifiers loaded:", len(data))

if __name__ == "__main__":
    main()
