# 요청 json(stage)을 받아서 서비스 흐름을 실행하고
# 응답 json(next_level/options/count)을 반환한다.

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Any, Dict, List

from app.services.tree_service import TreeService, TreeState

router = APIRouter(prefix="/tree", tags=["tree"])
svc = TreeService()

class NextReq(BaseModel):
    domain_l1: str
    route_l2: Optional[str] = None
    route_l3: Optional[str] = None
    route_l4: Optional[str] = None

@router.post("/next")
def next_options(req: NextReq) -> Dict[str, Any]:
    state = TreeState(
        domain_l1=req.domain_l1,
        route_l2=req.route_l2,
        route_l3=req.route_l3,
        route_l4=req.route_l4,
    )
    return svc.next_options(state)
