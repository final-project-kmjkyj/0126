"""
backend/app/repositories/mysql_repo.py

MySQL(cases) 에서

다음 route 후보(distinct)

후보 count

title(가상 route_l5) 목록

을 뽑아주는 DB 조회 모듈(Infra 레이어)

👉 다른 파일들이 이걸 “불러다 쓰는” 구조야.
[역할]
- MySQL 접근 레이어(선택)
  - run 저장(run_id, route_state, seed_case_id, debug, timestamps)
  - CSV 룰 테이블을 DB로 적재했다면:
    - route 조건 기반 후보군 조회(WHERE 필터)

[주의]
- MVP에서는 CSV를 pandas로 필터링해도 됨
- 운영/상용화를 생각하면 룰 테이블 + run 로그는 MySQL이 안정적
"""

# app/repositories/mysql_repo.py

import os
import pymysql
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class CaseTitle:
    case_code: str
    title: str


class MySQLCasesRepo:
    """
    Infra / Data Access
    - state 기반 AND 조건 조회
    - 다음 route 옵션 / title 목록 제공
    """

    def __init__(self):
        self.conn_args = dict(
            host=os.environ["MYSQL_HOST"],
            port=int(os.environ["MYSQL_PORT"]),
            user=os.environ["MYSQL_USER"],
            password=os.environ["MYSQL_PASSWORD"],
            db=os.environ["MYSQL_DB"],
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
        )
    def infer_next_options(self, domain_l1, route_l2, route_l3, route_l4):
        """
        다음 단계 후보를 '팩트'로 산출만 함(판단 X)

        규칙:
        - route_l2가 None이면: 다음은 route_l2
        - route_l3가 None이면: 다음은 route_l3 distinct
        - route_l4가 None이면:
            - route_l4 distinct가 있으면: 다음은 route_l4
            - 없으면: 다음은 title(=가상 route_l5)
        - route_l4가 있으면: 다음은 title
        """
        if route_l2 is None:
            return {"next_level": "route_l2", "options": []}

        if route_l3 is None:
            opts = self.list_distinct(
                "route_l3", domain_l1, route_l2=route_l2
            )
            return {"next_level": "route_l3", "options": opts}

        if route_l4 is None:
            l4_opts = self.list_distinct(
                "route_l4", domain_l1, route_l2=route_l2, route_l3=route_l3
            )
            if l4_opts:
                return {"next_level": "route_l4", "options": l4_opts}

            # route_l4가 전부 NULL이면 title 선택(가상 route_l5)
            titles = self.list_titles(
                domain_l1, route_l2=route_l2, route_l3=route_l3, route_l4=None
            )
            return {"next_level": "title", "options": titles}

        # route_l4까지 선택됐으면 title 선택
        titles = self.list_titles(
            domain_l1, route_l2=route_l2, route_l3=route_l3, route_l4=route_l4
        )
        return {"next_level": "title", "options": titles}
    
    def _conn(self):
        return pymysql.connect(**self.conn_args)

    def _where(self, domain_l1, route_l2=None, route_l3=None, route_l4=None):
        clauses = ["domain_l1=%s"]
        params = [domain_l1]

        if route_l2:
            clauses.append("route_l2=%s")
            params.append(route_l2)
        if route_l3:
            clauses.append("route_l3=%s")
            params.append(route_l3)
        if route_l4:
            clauses.append("route_l4=%s")
            params.append(route_l4)

        return " AND ".join(clauses), params

    def list_distinct(self, col, domain_l1, route_l2=None, route_l3=None, route_l4=None):
        where, params = self._where(domain_l1, route_l2, route_l3, route_l4)
        sql = f"""
        SELECT DISTINCT {col} AS v
        FROM cases
        WHERE {where}
          AND {col} IS NOT NULL
          AND {col} <> ''
        ORDER BY v
        """
        with self._conn() as c:
            with c.cursor() as cur:
                cur.execute(sql, params)
                return [r["v"] for r in cur.fetchall()]

    def count_candidates(self, domain_l1, route_l2=None, route_l3=None, route_l4=None):
        where, params = self._where(domain_l1, route_l2, route_l3, route_l4)
        sql = f"SELECT COUNT(*) cnt FROM cases WHERE {where}"
        with self._conn() as c:
            with c.cursor() as cur:
                cur.execute(sql, params)
                return cur.fetchone()["cnt"]

    def list_titles(self, domain_l1, route_l2, route_l3=None, route_l4=None):
        where, params = self._where(domain_l1, route_l2, route_l3, route_l4)
        sql = f"""
        SELECT case_code, title
        FROM cases
        WHERE {where}
        ORDER BY case_code
        """
        with self._conn() as c:
            with c.cursor() as cur:
                cur.execute(sql, params)
                return [CaseTitle(**r) for r in cur.fetchall()]
            
    def list_help_questions(self, domain_l1, route_l2=None, route_l3=None, route_l4=None):
        """
        현재 버킷(route 조건) 안에서 question이 존재하는 row만 가져온다.
        - question은 201건 중 82건만 존재하므로, 버킷에 따라 0개 나올 수 있음.
        """
        where, params = self._where(domain_l1, route_l2, route_l3, route_l4)
        sql = f"""
        SELECT case_code, title, question, url
        FROM cases
        WHERE {where}
          AND question IS NOT NULL
          AND question <> ''
        ORDER BY case_code
        """
        with self._conn() as c:
            with c.cursor() as cur:
                cur.execute(sql, params)
                return cur.fetchall()

    def get_case_detail(self, case_code: str) -> Dict[str, Any]:
        """
        case_code로 정본(Full text) 상세를 가져온다.
        - 최종 확정 후 출력용 (과실비율/해설/사고상황/법규/판례 등)
        """
        sql = """
        SELECT
          domain_l1, case_code, route_l2, route_l3, route_l4, title,
          participants_text, base_fault_text, base_fault_ratio_json,
          adjustment_text, accident_text,
          base_fault_explanation, modifier_explanation,
          related_law, precedent,
          url, question
        FROM cases
        WHERE case_code = %s
        LIMIT 1
        """
        with self._conn() as c:
            with c.cursor() as cur:
                cur.execute(sql, (case_code,))
                row = cur.fetchone()
                return row or {}

            
        
