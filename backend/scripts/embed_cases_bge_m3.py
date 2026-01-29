"""
==========================================================
[clean_text 전용 임베딩 스크립트 - BGE-M3]

목적
- Neo4j에 적재된 Case 노드 중
- embedding 이 없는 노드만 골라
- clean_text → BGE-M3 임베딩 생성
- 결과를 c.embedding 에 저장

설계 원칙 (중요)
- 임베딩 대상은 clean_text ONLY
- route / title / 설명 / user_note 절대 섞지 않음
- 임베딩은 "검색 보조" 용도
- 사고유형 판단(Top1)은 룰 기반 트리가 담당

모델
- BAAI/bge-m3
- embedding dimension = 1024
- cosine similarity 사용 (normalize_embeddings=True)

==========================================================
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from neo4j import GraphDatabase
from app.core.env import load_env
from sentence_transformers import SentenceTransformer


def main():
    load_env()

    NEO4J_BOLT_URL=os.environ["NEO4J_BOLT_URL"]
    NEO4J_USER=os.environ["NEO4J_USER"]
    NEO4J_PASSWORD=os.environ["NEO4J_PASSWORD"]

    model = SentenceTransformer("BAAI/bge-m3")

    EMBED_DIM =1024

    driver = GraphDatabase.driver(
        NEO4J_BOLT_URL,
        auth=(NEO4J_USER, NEO4J_PASSWORD)
    )

    fetch_query = """
    MATCH (c:Case)
    WHERE c.embedding IS NULL
        AND c.clean_text IS NOT NULL
    RETURN
        c.case_code AS case_code,
        c.clean_text AS clean_text
    """

    with driver.session() as session:
        rows = session.run(fetch_query).data()

    total = len(rows)
    print(f"embedding needed : {total}")

    if total ==0:
        print("all case nodes already embedded")
        driver.clese()
        return
    
    update_query = """
    UNWIND $rows AS row
    MATCH (c:Case {case_code : row.case_code})
    SET
        c.embedding = row.embedding,
        c.embed_model = 'bge-m3',
        c.embed_dim = size(row.embedding),
        c.embed_updated_at = datetime()
    """

    BATCH_SIZE = 32

    for i in range(0, total, BATCH_SIZE):
        batch = rows[i : i+BATCH_SIZE]

        texts = [r["clean_text"] for r in batch]

        vectors = model.encode(
            texts,
            normalize_embeddings=True,).tolist()

        payload = [
            {"case_code" : batch[j]["case_code"],
             "embedding" : vectors[j],}
             for j in range(len(batch))
        ]

        with driver.session() as session:
            session.run(update_query, rows=payload)

        print(f"임베딩 {min(i+ BATCH_SIZE, total)} / {total}")

    driver.close()
    print("✅ Embedding update completed (BGE-M3 / clean_text only).")


if __name__=="__main__":
    main()