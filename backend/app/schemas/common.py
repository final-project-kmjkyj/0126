"""
backend/app/schemas/common.py

[역할]
- 공통 타입/모델 정의 (예: Candidate, Evidence, Modifier 등)
- step1/step2 응답에서 반복되는 구조를 재사용 가능하게 함

[주의]
- 프론트(types/api.ts)와 형태를 최대한 맞춰 API 계약 안정화
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


# =========================================================
# 공통 Candidate (Step1 추천 / Step2 확장 공용)
# Step1(임베딩 추천), Step2(Graph 후보)
# =========================================================
class Candidate(BaseModel):
    """
    사고유형 후보 또는 추천 결과
    - Step1: 임베딩 기반 Top-N 추천 (확정 아님)
    - Step2: 그래프 확장 시 참고 후보
    """
    case_id: str = Field(..., description="사고유형 코드 (case_code)")
    title: Optional[str] = Field(None, description="사고유형 제목(한글)")
    score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="유사도 점수(추천용, 판단용 아님)"
    )
    source: Optional[Literal["rule", "embedding", "graph"]] = Field(
        None,
        description="후보 생성 출처"
    )


# =========================================================
# 근거(Evidence) 공통 모델 (step2_graph 확장 전용)
# =========================================================
class Evidence(BaseModel):
    """
    Step2 Graph 확장 결과 중 '근거' 단위
    """
    evidence_type: Literal["LAW", "PRECEDENT", "GUIDELINE"] = Field(
        ..., description="근거 유형"
    )
    title: str = Field(..., description="근거 제목")
    content: str = Field(..., description="근거 본문 요약 또는 전문")
    reference: Optional[str] = Field(
        None, description="조문 번호, 판례 번호 등"
    )


# =========================================================
# 가감요소(Modifier) 공통 모델 (step2_graph 확장 전용)
# =========================================================
class Modifier(BaseModel):
    """
    과실 가감요소 정의
    - Step2에서 후보로 제시
    - 사용자가 선택할 수 있음
    """
    modifier_code: str = Field(..., description="가감요소 코드")
    description: str = Field(..., description="가감요소 설명")
    direction: Literal["PLUS", "MINUS"] = Field(
        ..., description="과실 가산/감산 방향"
    )
    max_adjustment: Optional[int] = Field(
        None, description="최대 가감 가능 비율(있을 경우)"
    )


# =========================================================
# 공통 실행 컨텍스트 (Step1 ↔ Step2 연결용)
# Step1 결과를 Step2로 안전하게 넘기는 계약
# =========================================================
class RunContext(BaseModel):
    """
    Step1에서 발급 → Step2로 전달되는 실행 단위 컨텍스트
    """
    run_id: str = Field(..., description="실행 식별자(UUID 등)")
    domain_l1: Optional[str] = None
    route_l2: Optional[str] = None
    route_l3: Optional[str] = None
    route_l4: Optional[str] = None
    seed_case_id: Optional[str] = Field(
        None, description="Step1에서 확정된 사고유형 코드"
    )


# =========================================================
# 공통 메타 정보 (디버깅 / Audit / 재현성)
# =========================================================
class MetaInfo(BaseModel):
    """
    응답 메타 정보 (판단 아님)
    """
    message: Optional[str] = None
    warnings: Optional[List[str]] = None
    blocked: bool = Field(
        False, description="정책상 판단/확장이 차단되었는지 여부"
    )

