from fastapi import APIRouter
from app.services.tree_service import TreeService
from app.llm import explain_case

router = APIRouter(prefix="/cases", tags=["cases"])
svc = TreeService()

# 간단 메모리 캐시 (PoC용)
_REPORT_CACHE = {}

@router.get("/{case_code}")
def case_detail(case_code: str):
    detail = svc.case_detail(case_code)

    # 안전장치
    if not detail or not detail.get("case_code"):
        return detail

    code = detail["case_code"]

    # 캐시 있으면 바로 반환
    if code in _REPORT_CACHE:
        detail["final_report_md"] = _REPORT_CACHE[code]
        return detail

    # LLM 생성 (항상)
    report = explain_case(detail)
    _REPORT_CACHE[code] = report
    detail["final_report_md"] = report
    return detail
