"""
backend/app/schemas/step2_graph.py

[역할]
- Step2 그래프 확장 API의 Request/Response 스키마 정의

[핵심 필드 예시]
- run_id: step1에서 발급받은 실행 ID
- seed_case_id(case_code): 최종 확정된 사고유형 코드
- checked_modifiers: 사용자가 선택한 가감요소(선택)

[주의]
- Step2는 "확장/설명" 단계이며 seed를 다시 고르지 않음
"""