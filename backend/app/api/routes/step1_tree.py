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