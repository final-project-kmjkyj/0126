import requests
from typing import Dict, Any

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "exaone3.5:2.4b"


def explain_case(detail: Dict[str, Any]) -> str:
    """
    사고가 확정된 뒤(MySQL 정본 기준),
    LLM으로 '설명'만 생성한다.
    판단/확정/추론 금지.
    """

    prompt = f"""
너는 교통사고 과실비율 판단 시스템의 설명 전용 모듈이다.
과실비율을 판단하거나 확정하지 말고,
아래 정보를 바탕으로 사고 내용을 구조적으로 설명만 하라.

[사고유형]
case_code: {detail.get("case_code")}
title: {detail.get("title")}

[사고 상황]
{detail.get("accident_text")}

[기본 과실 설명]
{detail.get("base_fault_explanation")}

[가감요소 설명]
{detail.get("modifier_explanation")}

[관련 법규]
{detail.get("related_law")}

[참고 판례]
{detail.get("precedent")}
"""

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
    }

    resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
    resp.raise_for_status()

    return resp.json().get("response", "").strip()
