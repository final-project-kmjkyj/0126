"""
backend/scripts/embed_cases.py

[역할]
- Neo4j에 적재된 Case 노드들의 clean_text를 읽고
- OpenAI Embedding 생성 후 embedding 프로퍼티에 업데이트
- (선택) 벡터 인덱스가 없다면 생성/확인

[주의]
- OPENAI_API_KEY 필수(환경변수)
- 비용/속도 때문에 배치 처리(예: 50~200개 단위) 권장
"""