"""
backend/app/services/step1_tree_service.py

[역할]
- Step1 전체 흐름(룰 기반) 처리
  1) CSV(룰 테이블)에서 현재 route_state로 후보군 필터링
  2) 후보군이 1개면 Leaf 확정(case_code 반환)
  3) 후보군이 여러 개면 다음 질문/선택지 구성
  4) 사용자가 "모르겠어요"면:
     - 현재 route 맥락 + user_note를 query_builder로 합쳐 query_text 생성
     - 임베딩 생성 후 Neo4j에서 (현재 후보군 범위 내) Top3 추천

[입력]
- Step1TreeRequest

[출력]
- Step1TreeResponse

[주의]
- "정답(Leaf)"은 룰 필터 결과로만 확정(임베딩으로 확정 금지)
- 임베딩은 막힘 해결(추천) 보조 수단
"""



from typing import List, Dict, Optional
import uuid

from app.schemas.step1_tree import Step1TreeRequest, Step1TreeResponse
from app.schemas.common import Candidate, RunContext, MetaInfo
from app.services.query_builder import build_query_text


# =========================================================
# 내부 유틸 (실제 구현 시 CSV 룰 테이블로 교체)
# =========================================================
def filter_candidates_by_route(
    rule_table: List[Dict[str, str]],
    route_state: Dict[str, Optional[str]],
) -> List[Dict[str, str]]:
    """
    CSV 룰 테이블에서 현재 route_state에 맞는 사고유형 후보 필터링
    - route_state에 값이 있는 필드만 조건으로 사용
    """
    results = []

    for row in rule_table:
        matched = True
        for key, value in route_state.items():
            if value is None:
                continue
            if row.get(key) != value:
                matched = False
                break
        if matched:
            results.append(row)

    return results


# =========================================================
# Step1 메인 서비스
# =========================================================
def process_step1_tree(
    request: Step1TreeRequest,
    rule_table: List[Dict[str, str]],
    route_labels: Dict[str, str],
    embedding_search_fn,   # (query_text, candidate_case_ids) -> List[Candidate]
) -> Step1TreeResponse:
    """
    Step1(룰 기반 트리) 전체 처리 로직

    원칙:
    - Leaf 확정은 룰 필터 결과로만 수행
    - 임베딩은 '막힘 해결 추천' 보조 수단
    - 판단/계산 없음
    """

    # -----------------------------------------------------
    # 0. run_id 준비
    # -----------------------------------------------------
    run_id = request.run_id or str(uuid.uuid4())

    # -----------------------------------------------------
    # 1. 현재 route_state 구성
    # -----------------------------------------------------
    route_state = {
        "domain_l1": request.domain_l1,
        "route_l2": request.route_l2,
        "route_l3": request.route_l3,
        "route_l4": request.route_l4,
    }

    # -----------------------------------------------------
    # 2. 룰 기반 후보 필터링
    # -----------------------------------------------------
    filtered = filter_candidates_by_route(
        rule_table=rule_table,
        route_state=route_state,
    )

    # -----------------------------------------------------
    # 3. 후보 0개 → 상위 단계로 rollback
    # -----------------------------------------------------
    if len(filtered) == 0:
        return Step1TreeResponse(
            context=RunContext(
                run_id=run_id,
                **route_state,
            ),
            is_leaf=False,
            need_help=True,
            next_routes=None,
            candidates=None,
            meta=MetaInfo(
                message="조건에 맞는 사고유형이 없습니다. 이전 단계로 돌아가 다시 선택해주세요.",
                blocked=True,
            ),
        )

    # -----------------------------------------------------
    # 4. 후보 1개 → Leaf 확정 (룰 기반)
    # -----------------------------------------------------
    if len(filtered) == 1:
        case = filtered[0]
        return Step1TreeResponse(
            context=RunContext(
                run_id=run_id,
                **route_state,
                seed_case_id=case["case_code"],
            ),
            is_leaf=True,
            need_help=False,
            next_routes=None,
            candidates=None,
            meta=MetaInfo(
                message="사고유형이 확정되었습니다.",
            ),
        )

    # -----------------------------------------------------
    # 5. 후보 다수 → 다음 질문 or '모르겠어요' 대응
    # -----------------------------------------------------

    # 5-1. 사용자가 자연어를 입력하지 않은 경우
    if not request.user_note:
        # 다음 분기(route_l?) 계산
        # (실제 구현 시: rule_table에서 남은 분기값 집계)
        next_routes = []  # placeholder

        return Step1TreeResponse(
            context=RunContext(
                run_id=run_id,
                **route_state,
            ),
            is_leaf=False,
            need_help=True,
            next_routes=next_routes,
            candidates=None,
            meta=MetaInfo(
                message="추가 정보를 선택해주세요.",
            ),
        )

    # -----------------------------------------------------
    # 5-2. '모르겠어요' + 자연어 입력 → 임베딩 추천
    # -----------------------------------------------------
    query_text = build_query_text(
        route_state=route_state,
        user_note=request.user_note,
        route_labels=route_labels,
    )

    # 후보군 case_code 범위 제한
    candidate_case_ids = [row["case_code"] for row in filtered]

    # 임베딩 기반 추천 (Top-N)
    embedding_candidates: List[Candidate] = embedding_search_fn(
        query_text=query_text,
        candidate_case_ids=candidate_case_ids,
    )

    # 추천 실패 처리
    if not embedding_candidates:
        return Step1TreeResponse(
            context=RunContext(
                run_id=run_id,
                **route_state,
            ),
            is_leaf=False,
            need_help=True,
            next_routes=None,
            candidates=None,
            meta=MetaInfo(
                message="설명만으로 사고유형을 추천하기 어렵습니다. 다시 선택해주세요.",
                blocked=True,
            ),
        )

    # -----------------------------------------------------
    # 6. 추천 결과 반환 (확정 아님)
    # -----------------------------------------------------
    return Step1TreeResponse(
        context=RunContext(
            run_id=run_id,
            **route_state,
        ),
        is_leaf=False,
        need_help=True,
        next_routes=None,
        candidates=embedding_candidates,
        meta=MetaInfo(
            message="입력하신 설명과 유사한 사고유형 후보입니다. 가장 가까운 것을 선택해주세요.",
        ),
    )
