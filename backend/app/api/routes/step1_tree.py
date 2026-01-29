"""
backend/app/api/routes/step1_tree.py

[역할]
- Step1(룰 기반 트리 진행) API 엔드포인트
- 사용자의 현재 선택(route_state) + (선택)자연어(user_note)를 받아
  1) 다음 질문/선택지 제공 또는
  2) Leaf(최종 사고유형) 확정 또는
  3) 막힘("모르겠어요") 시 Neo4j 임베딩 Top3 추천

[입력]
- Step1TreeRequest (schemas/step1_tree.py)

[출력]
- Step1TreeResponse (schemas/step1_tree.py)

[주의]
- 라우터는 "검증 -> 서비스 호출 -> 응답 반환"만
- 판단 로직/DB 접근을 라우터에서 직접 하지 않음
"""


from fastapi import APIRouter, Depends, HTTPException
from app.schemas.step1_tree import Step1TreeRequest, Step1TreeResponse
from app.services.step1_tree_service import process_step1_tree

# 실제 프로젝트에서는 DI/컨테이너로 교체
from app.data.rule_table import RULE_TABLE
from app.data.route_labels import ROUTE_LABELS
from app.services.embedding_service import embedding_search

router = APIRouter(
    prefix="/step1",
    tags=["Step1 - Rule Tree"],
)


@router.post(
    "/tree",
    response_model=Step1TreeResponse,
    summary="Step1 룰 기반 사고유형 트리 진행",
)
def step1_tree_endpoint(
    request: Step1TreeRequest,
):
    """
    Step1 API 엔드포인트

    역할:
    - 요청 스키마 검증
    - Step1 서비스 호출
    - 결과 그대로 반환

    주의:
    - 판단 로직 없음
    - DB/Neo4j 직접 접근 없음
    """

    try:
        response = process_step1_tree(
            request=request,
            rule_table=RULE_TABLE,
            route_labels=ROUTE_LABELS,
            embedding_search_fn=embedding_search,
        )
        return response

    except Exception as e:
        # 시스템 오류만 여기서 처리
        # 정책/판단 실패는 서비스에서 정상 응답으로 반환해야 함
        raise HTTPException(
            status_code=500,
            detail="Step1 처리 중 서버 오류가 발생했습니다."
        ) from e
