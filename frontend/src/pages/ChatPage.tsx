/**
frontend/src/pages/ChatPage.tsx

[역할]
- 챗봇 메인 화면(질문/선택/입력/결과 흐름 전체 관리)
- step1_tree API 호출로 트리를 내려가며 Leaf 확정
- Leaf 확정 후 step2_graph 호출로 근거 확장 결과 표시

[상태 예시]
- routeState: domain_l1, route_l2~l4
- messages: 채팅 로그
- options: 현재 선택지 버튼 목록
- blocked: "모르겠어요" 입력 모드 여부

[주의]
- 최종 사고유형 확정은 step1 응답(seed_case_id) 기준
 */