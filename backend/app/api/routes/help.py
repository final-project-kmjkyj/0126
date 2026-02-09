# help/questions : mysql에서 질문 목록
# help/recommend : neo4j top3 추천

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Any, Dict

from app.services.tree_service import TreeService, TreeState

router = APIRouter(prefix="/help", tags=["help"])
svc = TreeService()

class HelpQReq(BaseModel):
    domain_l1: str
    route_l2: Optional[str] = None
    route_l3: Optional[str] = None
    route_l4: Optional[str] = None

class HelpRecReq(HelpQReq):
    user_note: str
    topk: int = 3

@router.post("/questions")
def help_questions(req: HelpQReq) -> Dict[str, Any]:
    state = TreeState(req.domain_l1, req.route_l2, req.route_l3, req.route_l4)
    return svc.help_questions(state)

@router.post("/recommend")
def help_recommend(req: HelpRecReq) -> Dict[str, Any]:
    state = TreeState(req.domain_l1, req.route_l2, req.route_l3, req.route_l4)
    return svc.help_recommend(state, user_note=req.user_note, topk=req.topk)
