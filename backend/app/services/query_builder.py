"""
backend/app/services/query_builder.py

[역할]
- "현재까지의 route 맥락" + "사용자 자연어(user_note)"를 합쳐
  Neo4j 임베딩 검색용 query_text를 생성

[입력]
- route_state: domain_l1, route_l2~l4, (선택)한글 라벨
- user_note: 사용자가 입력한 자연어

[출력]
- query_text: 짧은 한글/코드 혼합 문자열(검색용)

[주의]
- LLM으로 요약/정리하지 않고 원문 자연어를 그대로 포함(정책)
- query_text는 “막힘 해결 추천” 용도이며 정답 확정에 쓰지 않음
"""