"""
backend/app/core/config.py

[역할]
- .env / 환경변수 로드
- Neo4j / MySQL / OpenAI 설정을 Settings 객체로 제공

[입력]
- 환경변수(.env 포함)

[출력]
- settings (전역 설정 객체)

[주의]
- Python 3.9이면 Optional[str] 형태로 타입 작성 (str | None 금지)
- OPENAI_API_KEY는 환경변수로만 관리(코드/CSV에 저장 금지)
"""

from pathlib import Path
from dotenv import load_dotenv

def load_env():
    root = Path(__file__).resolve().parents[3]
    env_path = root / ".env"
    load_dotenv(env_path)

    return env_path