"""
backend/app/services/step2_graph_service.py

[역할]
- Step2(Leaf 확정 이후) 근거 확장 처리
  - Neo4j에서 seed_case_id 기준:
    - 가감요소(Modifier) 후보
    - 관련 근거(Evidence/Precedent/RelatedLaw) 조회
  - (선택) 사용자가 체크한 modifier만 필터링

[입력]
- Step2GraphRequest (seed_case_id 필수)

[출력]
- Step2GraphResponse (근거/가감요소 목록)

[주의]
- hop은 1~2 단계로 제한(과도한 확장 금지)
- Step2는 과실비율 계산/판단을 하지 않음(설명 확장만)
"""