"""
backend/app/services/query_builder.py

[역할]
- "현재까지의 route 맥락" + "사용자 자연어(user_note)"를 합쳐
  Neo4j 임베딩 검색용 query_text를 생성

[입력]
- route_state: domain_l1, route_l2~l4, (선택)한글 라벨
- user_note: 사용자가 입력한 자연어

[출력]
- query_text: 짧은 한글/코드 혼합 문자열(검색용)

[주의]
- LLM으로 요약/정리하지 않고 원문 자연어를 그대로 포함(정책)
- query_text는 “막힘 해결 추천” 용도이며 정답 확정에 쓰지 않음
"""


# backend/app/services/query_builder.py

from typing import Optional, Dict, List


# =========================================================
# Query Builder
# =========================================================
def build_query_text(
    route_state: Dict[str, Optional[str]],
    user_note: Optional[str] = None,
    route_labels: Optional[Dict[str, str]] = None,
) -> str:
    """
    Neo4j 임베딩 검색용 query_text 생성기

    원칙:
    - LLM 사용 금지
    - 자연어 요약/정제 금지
    - user_note는 원문 그대로 포함
    - route 맥락은 키워드 나열 방식으로만 결합
    - '막힘 해결 추천' 용도로만 사용 (정답 확정 금지)

    Parameters
    ----------
    route_state : Dict[str, Optional[str]]
        {
            "domain_l1": "CAR_PED",
            "route_l2": "SIG_IN_CW",
            "route_l3": "CAR_R_AFTER_CW",
            "route_l4": None
        }

    user_note : Optional[str]
        사용자가 입력한 자연어 설명 (원문 유지)

    route_labels : Optional[Dict[str, str]]
        route 코드 → 한글 라벨 매핑 (선택)
        예) { "SIG_IN_CW": "횡단보도 내(신호등 있음)" }

    Returns
    -------
    str
        임베딩 검색용 query_text
    """

    tokens: List[str] = []

    # 1. route 코드 기반 토큰 추가
    for key in ["domain_l1", "route_l2", "route_l3", "route_l4"]:
        value = route_state.get(key)
        if not value:
            continue

        # 코드 자체
        tokens.append(value)

        # 한글 라벨이 있으면 함께 추가
        if route_labels and value in route_labels:
            tokens.append(route_labels[value])

    # 2. 사용자 자연어 원문 그대로 추가
    if user_note:
        tokens.append(user_note.strip())

    # 3. 공백 기준으로 단순 결합
    # (문장 생성/정제 의도 없음)
    query_text = " ".join(tokens)

    return query_text
