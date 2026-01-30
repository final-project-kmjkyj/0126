"""
[역할] neo4j 접근 레이어 (인프라/검색)
- step1(help) : clean_text 임베딩 기반 topk 추천
- step2(추후) : seed_case_code 기반 graph 확장 (가감요소 /법규 판례 등)

[현재 구현 범위]
help 벡터검색 topk (route 버킷 필터 포함)

[전제]
- neo4j : case 노드에 embeddin(1024d, bge-m3, normalized) 저장 완료
- vector index 생성 완료:
name = 'case_embedding_index" , label "case", prop="embedding"

[env 필요]
NEO4J_BOLT_URL=bolt://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
NEO4J_VECTOR_INDEX=case_embedding_index
TOPK=5 (선택)

[주의]
- 임베딩 대상은 query_text(=route_context+user_note) 이고,
clean_Text 자체는 이미 c.embedding으로 저장되어 있다고 가정
"""

from __future__ import annotations # 타입 선언을 편하게 해줌 list[str] , optional[x]
from dataclasses import dataclass # 클래스에 @dataclass 붙이면 __init__, __repr__, __Eq__ 자동생성
#
from typing import Any, Dict, List, Optional # optional은 null이 들어올수도 있게끔 허용  any = 아무타입

import os
from neo4j import GraphDatabase

from sentence_transformers import SentenceTransformer

@dataclass
class RouteState:
    domain_l1: str
    route_l2: Optional[str] = None
    route_l3: Optional[str] = None
    route_l4: Optional[str] = None

class Neo4jRepository: # 모르겠어요 누르면 route 버킷 범위 내에서 vector topK추천

    def __init__(self):
        self.bolt_url = os.environ["NEO4J_BOLT_URL"]
        self.user = os.environ["NEO4J_USER"]
        self.password = os.environ["NEO4J_PASSWORD"]
        self.vector_index = os.environ.get("NEO4J_VECTOR_INDEX", "case_embedding_index")

        self.model = SentenceTransformer("BAAI/bge-m3")

        self.driver = GraphDatabase.driver(
            self.bolt_url,
            auth=(self.user, self.password)
        )

    def close(self):
        if self.driver:
            self.driver.close()
    
    @staticmethod #순수로직
    def build_route_context(state : RouteState): # route 맥락을 "그대로 문자열"로 만든다
        def v(x : Optional[str]):
            return x if x is not None else "NULL"
        
        return (
            f"[ROUTE_CONTEXT]\n" # 지금까지 클릭한 분기 상태에 대한 태그 임베딩모델에게 구조화된 상태정보 알려줌
            f"domain_l1={state.domain_l1}\n"
            f"route_l2={v(state.route_l2)}\n"
            f"route_l3={v(state.route_l3)}\n"
            f"route_l4={v(state.route_l4)}\n"
        )
    
    def build_query_text(self, state: RouteState, user_note:str): # 쿼리텍스트 = 루트텍스트 + 유저입력 원문
        user_note = (user_note or "").strip()
        return self.build_route_context(state) + "\n[USER_NOTE]\n" + user_note # 자연어라는걸 알려줌 태그로
    
    def vector_topk_within_bucket(self, state: RouteState, user_note:str, topk: int=3, candidate_pool: int = 30,):
        query_text = self.build_query_text(state, user_note)

        qvec = self.model.encode( # 쿼리 텍스트 임베딩
            [query_text],
            normalize_embeddings=True,)[0].tolist() # 
        
        # 백터검색 + 버킷필터 (선택된것 까지만 equality)
        where_clauses = ["c.domain_l1 = $domain_l1"] # 일단 1차로 대분류함
        params : Dict[str,Any] = {
            "index" : self.vector_index,
            "k" : int(candidate_pool),
            "vector" : qvec,
            "domain_l1" : state.domain_l1,
        }

        if state.route_l2 is not None:
            where_clauses.append("c.route_l2 = $route_l2") # 값이 있으면 2차분류 쭊쭊쭊 (필터링)
            params["route_l2"] = state.route_l2
        if state.route_l3 is not None:
            where_clauses.append("c.route_l3 = $route_l3")
            params["route_l3"] = state.route_l3
        if state.route_l4 is not None:
            where_clauses.append("c.route_l4 = $route_l4")
            params["route_l4"] = state.route_l4

        where_sql = " AND ".join(where_clauses) # c.domain_l1 = $domain_l1 AND c.route_l2 = $route_l2 AND c.route_l3 = $route_l3

        cypher =f"""
        CALL db.index.vector.queryNodes($index, $k, $vector)
        YIELD node, score
        WITH node AS c, score
        WHERE {where_sql}
        RETURN
          c.case_code AS case_code,
          c.title AS title,
          c.url AS url,
          c.route_l2 AS route_l2,
          c.route_l3 AS route_l3,
          c.route_l4 AS route_l4,
          score AS score
        ORDER BY score DESC
        LIMIT $topk
        """

        params["topk"] = int(topk)

        with self.driver.session() as session:
            rows = session.run(cypher, params).data()

        return rows 

    def graph_expand(self, seed_case_code: str, hop: int = 2) -> Dict[str, Any]:
        """
        (추후) Law/Precedent/Modifier 노드화 했을 때 1~2 hop 확장.
        지금 MVP에서는 MySQL 정본 조회로 충분하므로 TODO.
        """
        return {"seed_case_code": seed_case_code, "hop": hop, "nodes": [], "rels": []}       


