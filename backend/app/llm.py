# backend/app/llm.py
import os
import requests
from typing import Dict, Any

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
MODEL_NAME = os.getenv("OLLAMA_MODEL", "exaone3.5:2.4b")


def explain_case(detail: Dict[str, Any]) -> str:
    """
    사고가 확정된 뒤(MySQL 정본 기준),
    LLM으로 '설명'만 생성한다.
    판단/확정/추론 금지.
    """
    prompt = f"""
너는 교통사고 과실비율 시스템의 '설명 전용' 모듈이다.
절대 새로운 과실비율을 추론하거나 확정하지 마라.
아래 DB 정본 텍스트를 읽고, 사용자에게 이해하기 쉬운 요약/정리만 해라.

[사고유형]
case_code: {detail.get("case_code")}
title: {detail.get("title")}

[사고 상황]
{detail.get("accident_text")}

[기본 과실 설명(문서)]
{detail.get("base_fault_explanation")}

[가감요소 설명(문서)]
{detail.get("modifier_explanation")}

[관련 법규(문서)]
{detail.get("related_law")}

[참고 판례(문서)]
{detail.get("precedent")}

[출력 형식]
- Markdown으로 출력
- 섹션: 사고 요약 / 핵심 사실 / 기본 과실비율 근거 / 가감요소 / 관련 법규·판례 / 한줄 요약
"""

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
    }

    resp = requests.post(OLLAMA_URL, json=payload, timeout=180)
    resp.raise_for_status()
    return (resp.json().get("response") or "").strip()
