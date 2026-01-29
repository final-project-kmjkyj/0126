
"""
backend/scripts/import_cases_to_neo4j.py

[역할]
- CSV를 읽어서 Neo4j Case 노드로 적재
- 필수 프로퍼티: case_code, clean_text, (선택) route_l2~l4, domain_l1 등

[주의]
- 임베딩 생성은 이 스크립트에서 하지 않고 embed_cases.py에서 별도 수행
"""


from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # => /.../backend

import os
import argparse
from typing import Any, Dict, List

import pymysql
from neo4j import GraphDatabase

from app.core.env import load_env


MYSQL_SELECT_SQL = """
SELECT
  case_code,
  domain_l1,
  route_l2, route_l3, route_l4,
  title,
  clean_text,
  question,
  url
FROM cases
WHERE case_code IS NOT NULL
ORDER BY case_code
"""


def fetch_rows_from_mysql() -> List[Dict[str, Any]]:
    conn = pymysql.connect(
        host=os.environ["MYSQL_HOST"],
        port=int(os.environ["MYSQL_PORT"]),
        user=os.environ["MYSQL_USER"],
        password=os.environ["MYSQL_PASSWORD"],
        db=os.environ["MYSQL_DB"],
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )

    try:
        with conn.cursor() as cur:
            cur.execute(MYSQL_SELECT_SQL)
            rows = cur.fetchall()

        # 빈 문자열 정리
        for r in rows:
            for k in ["domain_l1", "route_l2", "route_l3", "route_l4", "title", "clean_text", "question", "url"]:
                if k in r and isinstance(r[k], str):
                    v = r[k].strip()
                    r[k] = v if v else None

        return rows
    finally:
        conn.close()


def chunked(lst: List[Dict[str, Any]], size: int):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


def main():
    load_env()  # ✅ 루트 .env 로드 (너희 프로젝트 방식)

    parser = argparse.ArgumentParser()
    parser.add_argument("--wipe", action="store_true", help="Neo4j :Case 전체 삭제 후 재적재")
    parser.add_argument("--batch-size", type=int, default=200)
    args = parser.parse_args()

    # env (Neo4j)
    bolt_url = os.environ["NEO4J_BOLT_URL"]
    user = os.environ["NEO4J_USER"]
    password = os.environ["NEO4J_PASSWORD"]

    label = os.environ.get("NEO4J_CASE_LABEL", "Case")
    id_prop = os.environ.get("NEO4J_CASE_ID_PROP", "case_code")

    # 1) MySQL -> rows
    rows = fetch_rows_from_mysql()
    if not rows:
        raise RuntimeError("MySQL cases rows=0. DB/테이블/권한을 확인하세요.")

    # 2) Neo4j connect
    driver = GraphDatabase.driver(bolt_url, auth=(user, password))
    try:
        with driver.session() as session:
            # 2-1) UNIQUE constraint
            session.run(f"""
            CREATE CONSTRAINT case_code_unique IF NOT EXISTS
            FOR (c:{label})
            REQUIRE c.{id_prop} IS UNIQUE
            """)

            # 2-2) wipe
            if args.wipe:
                session.run(f"MATCH (c:{label}) DETACH DELETE c")

        # 3) upsert
            cypher_upsert = f"""
            UNWIND $rows AS row
            MERGE (c:{label} {{{id_prop}: row.case_code}})
            ON CREATE SET
            c.created_at = datetime()
            SET
            c.domain_l1  = row.domain_l1,
            c.route_l2   = row.route_l2,
            c.route_l3   = row.route_l3,
            c.route_l4   = row.route_l4,
            c.title      = row.title,
            c.clean_text = row.clean_text,
            c.question   = row.question,
            c.url        = row.url,
            c.updated_at = datetime()
            """


        total = 0
        for batch in chunked(rows, args.batch_size):
            with driver.session() as session:
                session.run(cypher_upsert, rows=batch)
            total += len(batch)
            print(f"[Neo4j] upserted {total}/{len(rows)}")

        # 4) verify
        with driver.session() as session:
            cnt = session.run(f"MATCH (c:{label}) RETURN count(c) AS cnt").single()["cnt"]
            null_clean = session.run(f"MATCH (c:{label}) WHERE c.clean_text IS NULL RETURN count(c) AS cnt").single()["cnt"]

        print(f"✅ Done. Neo4j :{label} count = {cnt}, clean_text NULL = {null_clean}")

    finally:
        driver.close()


if __name__ == "__main__":
    main()
