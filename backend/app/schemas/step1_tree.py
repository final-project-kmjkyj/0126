"""
backend/app/schemas/step1_tree.py

[역할]
- Step1 트리 진행 API의 Request/Response 스키마 정의
- 프론트(챗봇 UI)와 백엔드가 합의한 입력/출력 계약(API Contract)

[핵심 필드 예시]
- domain_l1: CAR_CR / CAR_PED / CAR_BIKE
- route_l2~l4: 사용자가 클릭한 분기값(영문 코드)
- user_note: "모르겠어요" 시 추가 자연어 설명(선택)

[주의]
- 여기는 데이터 구조만 정의(로직 금지)
"""