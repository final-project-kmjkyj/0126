"""
backend/app/main.py

[역할]
- FastAPI 앱 엔트리포인트
- 라우터(step1_tree, step2_graph) 등록
- 헬스체크 제공

[입력]
- HTTP 요청

[출력]
- JSON 응답

[주의]
- 비즈니스 로직(판단/검색)은 절대 여기서 하지 않음
"""


# backend/app/main.py

from fastapi import FastAPI

from app.api.routes.step1_tree import router as step1_router
from app.api.routes.step2_graph import router as step2_router


# =========================================================
# FastAPI App 생성
# =========================================================
app = FastAPI(
    title="Accident Liability Decision API",
    description="근거 기반 교통사고 과실비율 판단 보조 시스템",
    version="0.1.0",
)


# =========================================================
# Router 등록
# =========================================================
app.include_router(step1_router)
app.include_router(step2_router)


# =========================================================
# Health Check
# =========================================================
@app.get(
    "/health",
    summary="헬스 체크",
)
def health_check():
    """
    서버 상태 확인용 엔드포인트
    - 로직/DB/Neo4j 접근 없음
    """
    return {
        "status": "ok",
        "service": "accident-liability-api",
    }

