"""
backend/app/schemas/step2_graph.py

[역할]
- Step2 그래프 확장 API의 Request/Response 스키마 정의

[핵심 필드 예시]
- run_id: step1에서 발급받은 실행 ID
- seed_case_id(case_code): 최종 확정된 사고유형 코드
- checked_modifiers: 사용자가 선택한 가감요소(선택)

[주의]
- Step2는 "확장/설명" 단계이며 seed를 다시 고르지 않음

프론트 사용 예시
// Step2는 항상 Leaf 이후
renderEvidence(response.evidences);
renderModifiers(response.modifiers);
"""



from typing import List, Optional
from pydantic import BaseModel, Field
from .common import Evidence, Modifier, RunContext, MetaInfo


# =========================================================
# Step2 요청 스키마
# =========================================================
class Step2GraphRequest(BaseModel):
    """
    Step2(Graph 확장) 요청
    - Step1에서 Leaf 확정 이후에만 호출 가능
    """
    run_id: str = Field(
        ..., description="Step1에서 발급된 실행 식별자"
    )

    seed_case_id: str = Field(
        ..., description="최종 확정된 사고유형 코드(case_code)"
    )

    checked_modifiers: Optional[List[str]] = Field(
        None,
        description="사용자가 선택한 가감요소 코드 목록(선택)"
    )


# =========================================================
# Step2 응답 스키마
# =========================================================
class Step2GraphResponse(BaseModel):
    """
    Step2 처리 결과
    - 사고유형은 이미 확정된 상태
    - 관련 근거 및 가감요소 후보를 확장 제공
    """

    # 실행 컨텍스트 (Step1과 연속성 유지)
    context: RunContext = Field(
        ..., description="현재 실행 컨텍스트"
    )

    # 근거 확장 결과
    evidences: Optional[List[Evidence]] = Field(
        None,
        description="관련 근거 목록 (법규/판례/지침 등)"
    )

    # 가감요소 후보
    modifiers: Optional[List[Modifier]] = Field(
        None,
        description="적용 가능 가감요소 후보 목록"
    )

    # 메타 정보
    meta: Optional[MetaInfo] = Field(
        None, description="메타/경고/차단 정보"
    )