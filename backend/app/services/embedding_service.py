"""
backend/app/services/embedding_service.py

[역할]
- OpenAI Embedding API 호출 래퍼
- 텍스트(query_text 또는 clean_text)에 대한 벡터(embedding) 생성

[입력]
- text: str

[출력]
- vector: List[float]

[주의]
- OPENAI_API_KEY는 환경변수로만 주입
- 임베딩 모델명은 config(settings.OPENAI_EMBED_MODEL)에서 관리
"""

# backend/app/services/embedding_service.py

from typing import List
from app.schemas.common import Candidate


def embedding_search(
    query_text: str,
    candidate_case_ids: List[str],
    top_k: int = 3,
) -> List[Candidate]:
    """
    mock 임베딩 검색 함수

    - 실제 임베딩/Neo4j 연결 전 테스트용
    - '모르겠어요' 경로 검증 목적
    """

    if not candidate_case_ids:
        return []

    results = []
    for case_id in candidate_case_ids[:top_k]:
        results.append(
            Candidate(
                case_code=case_id,
                score=0.0,
                reason="mock embedding 추천",
            )
        )

    return results
