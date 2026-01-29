"""
backend/app/repositories/neo4j_repo.py

[역할]
- Neo4j 접근 레이어
  1) 벡터 검색(TopK) : clean_text 임베딩 기반
  2) 후보군 제한(필요 시): domain/route 조건을 WHERE로 제한
  3) Graph 확장 조회: seed_case_id -> Modifier/Evidence 1~2 hop

[입력/출력]
- vector_search(...) -> 후보 목록(List[dict])
- graph_expand(...) -> modifier/evidence 목록

[주의]
- Step1에서 임베딩 검색은 "추천" 전용 (정답 확정 금지)
- Step2는 seed 확정 이후에만 graph_expand 허용
"""

# backend/app/repositories/neo4j_repo.py

from typing import List
from app.schemas.common import Evidence, Modifier


class Neo4jRepository:
    """
    mock Neo4j repository

    - Step2 Graph 확장 흐름 검증용
    - 실제 Neo4j 연결 전까지 사용
    """

    def get_evidences(self, seed_case_id: str, hop: int = 2) -> List[Evidence]:
        # mock 근거
        return [
            Evidence(
                evidence_id="EVIDENCE_001",
                title="mock 관련 법규",
                description="실제 Neo4j 연결 전 mock 근거입니다.",
                source="mock",
            )
        ]

    def get_modifiers(self, seed_case_id: str, hop: int = 2) -> List[Modifier]:
        # mock 가감요소
        return [
            Modifier(
                modifier_code="MOD_001",
                name="mock 가감요소",
                description="실제 Neo4j 연결 전 mock 가감요소입니다.",
                direction="increase",
            )
        ]

