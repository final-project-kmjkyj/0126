"""
backend/app/services/step2_graph_service.py

[역할]
- Step2(Leaf 확정 이후) 근거 확장 처리
  - Neo4j에서 seed_case_id 기준:
    - 가감요소(Modifier) 후보
    - 관련 근거(Evidence/Precedent/RelatedLaw) 조회
  - (선택) 사용자가 체크한 modifier만 필터링

[입력]
- Step2GraphRequest (seed_case_id 필수)

[출력]
- Step2GraphResponse (근거/가감요소 목록)

[주의]
- hop은 1~2 단계로 제한(과도한 확장 금지)
- Step2는 과실비율 계산/판단을 하지 않음(설명 확장만)
"""



from typing import List, Optional

from app.schemas.step2_graph import Step2GraphRequest, Step2GraphResponse
from app.schemas.common import Evidence, Modifier, RunContext, MetaInfo


# =========================================================
# Step2 Graph 확장 서비스
# =========================================================
def process_step2_graph(
    request: Step2GraphRequest,
    *,
    graph_repo,
    max_hop: int = 2,
) -> Step2GraphResponse:
    """
    Step2(Graph 확장) 처리 로직

    역할:
    - Step1에서 확정된 seed_case_id 기준으로
      관련 근거(Evidence)와 가감요소(Modifier)를 확장 조회
    - 판단/계산은 수행하지 않음 (설명 전용)

    Parameters
    ----------
    request : Step2GraphRequest
        seed_case_id가 반드시 포함되어야 함

    graph_repo :
        Neo4j 접근 레포지토리
        (get_evidences, get_modifiers 메서드 제공 가정)

    max_hop : int
        그래프 확장 최대 hop 수 (기본 2)
    """

    # -----------------------------------------------------
    # 0. 입력 검증 (방어적)
    # -----------------------------------------------------
    if not request.seed_case_id:
        return Step2GraphResponse(
            context=RunContext(
                run_id=request.run_id,
                seed_case_id=None,
            ),
            evidences=None,
            modifiers=None,
            meta=MetaInfo(
                message="확정된 사고유형이 없어 근거 확장을 수행할 수 없습니다.",
                blocked=True,
            ),
        )

    # hop 상한 강제
    hop = min(max_hop, 2)

    # -----------------------------------------------------
    # 1. 그래프에서 근거 조회
    # -----------------------------------------------------
    evidences: List[Evidence] = graph_repo.get_evidences(
        seed_case_id=request.seed_case_id,
        hop=hop,
    )

    # -----------------------------------------------------
    # 2. 그래프에서 가감요소 조회
    # -----------------------------------------------------
    modifiers: List[Modifier] = graph_repo.get_modifiers(
        seed_case_id=request.seed_case_id,
        hop=hop,
    )

    # -----------------------------------------------------
    # 3. 사용자가 선택한 가감요소가 있으면 필터링
    # -----------------------------------------------------
    if request.checked_modifiers:
        modifiers = [
            m for m in modifiers
            if m.modifier_code in request.checked_modifiers
        ]

    # -----------------------------------------------------
    # 4. 결과 조립 (설명용)
    # -----------------------------------------------------
    return Step2GraphResponse(
        context=RunContext(
            run_id=request.run_id,
            seed_case_id=request.seed_case_id,
        ),
        evidences=evidences or None,
        modifiers=modifiers or None,
        meta=MetaInfo(
            message="확정된 사고유형 기준으로 관련 근거와 가감요소를 확장했습니다.",
        ),
    )