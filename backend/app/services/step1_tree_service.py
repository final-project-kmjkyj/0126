"""
backend/app/services/step1_tree_service.py

[역할]
- Step1 전체 흐름(룰 기반) 처리
  1) CSV(룰 테이블)에서 현재 route_state로 후보군 필터링
  2) 후보군이 1개면 Leaf 확정(case_code 반환)
  3) 후보군이 여러 개면 다음 질문/선택지 구성
  4) 사용자가 "모르겠어요"면:
     - 현재 route 맥락 + user_note를 query_builder로 합쳐 query_text 생성
     - 임베딩 생성 후 Neo4j에서 (현재 후보군 범위 내) Top3 추천

[입력]
- Step1TreeRequest

[출력]
- Step1TreeResponse

[주의]
- "정답(Leaf)"은 룰 필터 결과로만 확정(임베딩으로 확정 금지)
- 임베딩은 막힘 해결(추천) 보조 수단
"""