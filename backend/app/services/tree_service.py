# backend/app/services/tree_service.py
from __future__ import annotations
from app.repositories.neo4j_repo import Neo4jRepository
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from app.repositories.mysql_repo import MySQLCasesRepo, CaseTitle
from app.repositories.neo4j_repo import Neo4jRepository, RouteState

class TreeService:
    def __init__(self):
        self.neo4j = Neo4jRepository()
        ...
    
    def case_detail(self, case_code: str):
        detail = self.mysql_repo.get_case_detail(case_code)

        # 🔽 여기 추가
        modifiers = self.neo4j.get_common_modifiers(case_code)
        detail["common_modifiers"] = modifiers

        return detail
    
@dataclass
class TreeState:
    domain_l1: str
    route_l2: Optional[str] = None
    route_l3: Optional[str] = None
    route_l4: Optional[str] = None


class TreeService:
    """
    [역할] (서비스/도메인 계층)
    - CLI에서 검증한 흐름을 "함수"로 분리한 계층
    - Repo(MySQL/Neo4j) 호출은 여기서만 한다
    - FastAPI/CLI는 TreeService만 호출한다

    [주의]
    - 사고유형(case_code) 확정은 룰 기반(사용자 선택)으로만.
    - Neo4j 벡터검색은 HELP에서 Top3 '추천'만.
    """

    def __init__(
        self,
        mysql_repo: Optional[MySQLCasesRepo] = None,
        neo4j_repo: Optional[Neo4jRepository] = None,
    ):
        self.mysql = mysql_repo or MySQLCasesRepo()
        # Neo4j는 요청마다 열었다 닫아도 되고(안전), 재사용해도 됨.
        # 여기서는 "요청마다" 만드는 방식으로 구현(간단/안전).
        self.neo4j = neo4j_repo  # optional

    # ----------------------------
    # 1) 트리 다음 옵션
    # ----------------------------
    def next_options(self, state: TreeState) -> Dict[str, Any]:
        """
        입력 state 기준으로 다음 단계(next_level)와 options 반환.
        - candidate_count도 같이 반환(디버깅/UX)
        """
        cnt = self.mysql.count_candidates(
            state.domain_l1, state.route_l2, state.route_l3, state.route_l4
        )

        nxt = self.mysql.infer_next_options(
            state.domain_l1, state.route_l2, state.route_l3, state.route_l4
        )
        next_level = nxt["next_level"]

        # infer_next_options에서 route_l2는 options 비워두므로 여기서 채움
        if next_level == "route_l2":
            options = self.mysql.list_distinct("route_l2", state.domain_l1)
            return {"next_level": "route_l2", "options": options, "candidate_count": cnt}

        if next_level in ("route_l3", "route_l4"):
            return {"next_level": next_level, "options": nxt["options"], "candidate_count": cnt}

        if next_level == "title":
            # options는 CaseTitle list
            titles: List[CaseTitle] = self.mysql.list_titles(
                state.domain_l1, route_l2=state.route_l2, route_l3=state.route_l3, route_l4=state.route_l4
            )
            # API 친화적으로 dict로 변환
            options = [{"case_code": t.case_code, "title": t.title} for t in titles]
            return {"next_level": "title", "options": options, "candidate_count": cnt}

        # 방어
        return {"next_level": next_level, "options": [], "candidate_count": cnt}

    # ----------------------------
    # 2) HELP: 질문 리스트
    # ----------------------------
    def help_questions(self, state: TreeState) -> Dict[str, Any]:
        """
        현재 버킷에서 question 목록 반환.
        - question은 일부 케이스만 존재하므로 0개면 fallback 문구 1개 반환
        - 중복 제거해서 돌려줌
        """
        rows = self.mysql.list_help_questions(
            state.domain_l1, state.route_l2, state.route_l3, state.route_l4
        )

        seen = set()
        questions: List[str] = []
        for r in rows:
            q = (r.get("question") or "").strip()
            if q and q not in seen:
                seen.add(q)
                questions.append(q)

        if not questions:
            # 공통 fallback 질문(UNKNOWN용)
            fallback = (
                "사고 상황을 한 줄로 적어주세요. (장소/진행방향/신호/충돌지점)\n"
                "예) 교차로에서 A는 직진(녹색), B는 좌회전(황색) 중 측면 충돌"
            )
            return {"questions": [fallback], "fallback_used": True}

        return {"questions": questions, "fallback_used": False}

    # ----------------------------
    # 3) HELP: Neo4j Top3 추천
    # ----------------------------
    def help_recommend(self, state: TreeState, user_note: str, topk: int = 3) -> Dict[str, Any]:
        """
        route 버킷 필터 내에서 user_note로 벡터검색 TopK 추천.
        """
        if not user_note or not user_note.strip():
            return {"topk": [], "error": "user_note is empty"}

        rs = RouteState(
            domain_l1=state.domain_l1,
            route_l2=state.route_l2,
            route_l3=state.route_l3,
            route_l4=state.route_l4,
        )

        neo = self.neo4j or Neo4jRepository()
        try:
            top = neo.vector_topk_within_bucket(rs, user_note=user_note, topk=topk)
        finally:
            # neo4j_repo가 close 제공한다는 전제(네 CLI 기준)
            try:
                neo.close()
            except Exception:
                pass

        return {"topk": top}

    # ----------------------------
    # 4) case_code 확정 후 상세 조회
    # ----------------------------
    def case_detail(self, case_code: str) -> Dict[str, Any]:
        """
        MySQL 정본 상세 반환
        """
        return self.mysql.get_case_detail(case_code)