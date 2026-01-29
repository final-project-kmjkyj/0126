"""
backend/app/api/routes/step2_graph.py

[역할]
- Step2(Leaf 확정 이후) Graph 확장 API
- seed_case_id(=case_code) 기준으로
  가감요소/관련법규/판례/what-if 후보를 그래프에서 확장해 제공

[입력]
- Step2GraphRequest (schemas/step2_graph.py)

[출력]
- Step2GraphResponse (schemas/step2_graph.py)

[주의]
- Graph는 반드시 Leaf 확정 이후에만 사용
- Step2에서 seed 확정(판단)하지 않음 (이미 확정된 case_code만 받음)
"""


# backend/app/api/routes/step2_graph.py

from fastapi import APIRouter, HTTPException
from app.schemas.step2_graph import Step2GraphRequest, Step2GraphResponse
from app.services.step2_graph_service import process_step2_graph

# 실제 프로젝트에서는 DI/컨테이너로 교체
from app.repositories.neo4j_repo import Neo4jRepository


router = APIRouter(
    prefix="/step2",
    tags=["Step2 - Graph Expansion"],
)


@router.post(
    "/graph",
    response_model=Step2GraphResponse,
    summary="Step2 확정 사고유형 기준 Graph 근거 확장",
)
def step2_graph_endpoint(
    request: Step2GraphRequest,
):
    """
    Step2 API 엔드포인트

    역할:
    - 요청 스키마 검증
    - Step2 서비스 호출
    - 결과 그대로 반환

    주의:
    - seed_case_id 재선정/판단 금지
    - 과실비율 계산 금지
    """

    try:
        graph_repo = Neo4jRepository()

        response = process_step2_graph(
            request=request,
            graph_repo=graph_repo,
        )
        return response

    except Exception as e:
        # 시스템/인프라 오류만 HTTP 예외로 처리
        # 정책/판단 실패는 서비스에서 정상 응답으로 반환해야 함
        raise HTTPException(
            status_code=500,
            detail="Step2 그래프 확장 처리 중 서버 오류가 발생했습니다."
        ) from e
