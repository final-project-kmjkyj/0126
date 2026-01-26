"""
backend/app/services/embedding_service.py

[역할]
- OpenAI Embedding API 호출 래퍼
- 텍스트(query_text 또는 clean_text)에 대한 벡터(embedding) 생성

[입력]
- text: str

[출력]
- vector: List[float]

[주의]
- OPENAI_API_KEY는 환경변수로만 주입
- 임베딩 모델명은 config(settings.OPENAI_EMBED_MODEL)에서 관리
"""