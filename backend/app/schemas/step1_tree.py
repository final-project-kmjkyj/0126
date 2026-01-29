"""
backend/app/schemas/step1_tree.py

[역할]
- Step1 트리 진행 API의 Request/Response 스키마 정의
- 프론트(챗봇 UI)와 백엔드가 합의한 입력/출력 계약(API Contract)

[핵심 필드 예시]
- domain_l1: CAR_CR / CAR_PED / CAR_BIKE
- route_l2~l4: 사용자가 클릭한 분기값(영문 코드)
- user_note: "모르겠어요" 시 추가 자연어 설명(선택)

[주의]
- 여기는 데이터 구조만 정의(로직 금지)

프론트 사용 예시
if (response.is_leaf) {
  // Step2로 이동
} else if (response.need_help) {
  // 다음 질문 or 후보 선택 UI
} """


from typing import List, Optional
from pydantic import BaseModel, Field
from .common import Candidate, RunContext, MetaInfo


# =========================================================
# Step1 요청 스키마
# =========================================================
class Step1TreeRequest(BaseModel):
    """
    Step1(룰 기반 트리) 진행 요청
    - 프론트에서 사용자의 현재 선택 상태를 전달
    """
    run_id: Optional[str] = Field(
        None,
        description="기존 실행 식별자 (없으면 신규 생성)"
    )

    # Route 상태
    domain_l1: Optional[str] = Field(
        None, description="사고 주체 대분류 (CAR_PED, CAR_CAR, CAR_BIKE 등)"
    )
    route_l2: Optional[str] = Field(
        None, description="사고 공간/상황 분기"
    )
    route_l3: Optional[str] = Field(
        None, description="사고 맥락/조건 분기"
    )
    route_l4: Optional[str] = Field(
        None, description="충돌 형태 분기"
    )

    # 막힘 처리용 자연어 (선택)
    user_note: Optional[str] = Field(
        None,
        description="사용자가 '모르겠어요' 선택 시 입력한 자연어 설명"
    )

# =========================================================
# Step1 응답 스키마
# =========================================================
class Step1TreeResponse(BaseModel):
    """
    Step1 처리 결과
    - 다음 질문을 던지거나
    - Leaf 확정하거나
    - 추천 후보를 제공
    """

    # 실행 컨텍스트 (Step2로 전달 가능)
    context: RunContext = Field(
        ..., description="현재 실행 컨텍스트"
    )

    # 현재 상태 플래그
    is_leaf: bool = Field(
        False, description="사고유형이 확정(Leaf)되었는지 여부"
    )
    need_help: bool = Field(
        False, description="추가 입력(질문/선택)이 필요한지 여부"
    )

    # 다음 분기 선택지 (룰 기반)
    next_routes: Optional[List[str]] = Field(
        None,
        description="다음 단계에서 선택 가능한 route 코드 목록"
    )

    # 임베딩 기반 추천 후보 (막힘 해결용)
    candidates: Optional[List[Candidate]] = Field(
        None,
        description="유사 사고유형 추천 목록 (확정 아님)"
    )

    # 메타 정보
    meta: Optional[MetaInfo] = Field(
        None, description="메타/경고/차단 정보"
    )