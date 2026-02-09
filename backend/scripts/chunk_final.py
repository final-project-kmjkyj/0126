# extract_fault_cases_to_csv.py
# -*- coding: utf-8 -*-

import argparse
import json
import re
from pathlib import Path

import pandas as pd

# ---------- Optional: PDF fallback (PyMuPDF) ----------
def extract_text_from_pdf(pdf_path: str) -> str:
    try:
        import fitz  # PyMuPDF
    except ImportError as e:
        raise RuntimeError("PDF fallback을 쓰려면 PyMuPDF가 필요합니다: pip install pymupdf") from e

    doc = fitz.open(pdf_path)
    pages = []
    for i in range(len(doc)):
        t = doc[i].get_text("text")
        pages.append(f"\n\n[Page {i+1}]\n{t}")
    return "\n".join(pages)


# ---------- HTML parse ----------
def extract_text_from_html(html_path: str) -> str:
    try:
        from bs4 import BeautifulSoup
    except ImportError as e:
        raise RuntimeError("HTML 파싱을 쓰려면 bs4가 필요합니다: pip install beautifulsoup4 lxml") from e

    html = Path(html_path).read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "lxml")

    # structured.html 이 페이지별로 <h2>Page N</h2> + <p>...</p> 형태라고 가정
    # 전체 텍스트를 줄 단위로 이어붙이기
    lines = []
    for el in soup.find_all(["h1", "h2", "h3", "p", "li"]):
        txt = el.get_text(" ", strip=True)
        if txt:
            lines.append(txt)
    return "\n".join(lines)


# ---------- Normalization ----------
def normalize(text: str) -> str:
    # 줄바꿈/공백 정리
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ---------- Case block split ----------
# 사고유형 코드 패턴 (차1-4, 보17, 거31-2, 회전-1 등 케이스 확장)
CASE_CODE_RE = re.compile(
    r"^(차|보|거|회전)\s*\d+(?:-\d+)?\s*$"
)

def split_into_case_blocks(full_text: str) -> dict:
    """
    full_text를 줄 단위로 훑으며,
    '사고유형 코드' 라인이 나오면 새 블록 시작.
    return: {case_code: block_text}
    """
    lines = full_text.split("\n")
    blocks = {}
    current_code = None
    buff = []

    def flush():
        nonlocal current_code, buff
        if current_code and buff:
            blocks[current_code] = "\n".join(buff).strip()
        buff = []

    for raw in lines:
        line = raw.strip()
        if not line:
            # 빈줄은 블록 내부에서 유지해도 되지만 과도하면 노이즈라 1개만 유지
            buff.append("")
            continue

        m = CASE_CODE_RE.match(line.replace(" ", ""))
        if m:
            # 새 케이스 시작
            flush()
            current_code = line.replace(" ", "")  # 공백 제거해서 정규화
            buff = [current_code]
            continue

        if current_code:
            buff.append(line)

    flush()
    return blocks


# ---------- Field extraction heuristics ----------
def pick_title(block_text: str, case_code: str) -> str:
    """
    보통 PDF/HTML에서 '제목'이 case_code 직전/직후에 위치함.
    여기서는 블록 상단 8줄 중 case_code/잡텍스트 제외한 가장 그럴듯한 한 줄을 제목으로.
    """
    lines = [l.strip() for l in block_text.split("\n") if l.strip()]
    # 첫 줄은 보통 case_code 자체
    head = lines[:10]

    candidates = []
    for l in head:
        if l == case_code:
            continue
        if "기본" in l and "과실" in l:
            continue
        if l.startswith("자동차사고") or l.startswith("과실비율"):
            continue
        # (A) (B) 등 당사자 라인은 제목이 아닐 가능성이 큼
        if re.search(r"\(A\)|\(B\)|A\s*[:：]|B\s*[:：]", l):
            continue
        candidates.append(l)

    return candidates[0] if candidates else ""


def extract_participants(block_text: str) -> str:
    """
    (A) ... (B) ... 혹은 '자동차 A :' 같은 라인을 모아서 한 줄로 정리
    """
    lines = [l.strip() for l in block_text.split("\n") if l.strip()]
    picked = []

    for l in lines[:80]:
        if re.search(r"\(A\)", l) or re.search(r"\(B\)", l):
            picked.append(l)
        elif re.search(r"자동차\s*A\s*[:：]", l) or re.search(r"자동차\s*B\s*[:：]", l):
            picked.append(l)
        elif re.search(r"^A\s*[:：]", l) or re.search(r"^B\s*[:：]", l):
            picked.append(l)

    # 너무 길면 중복 제거
    uniq = []
    seen = set()
    for p in picked:
        if p not in seen:
            uniq.append(p)
            seen.add(p)

    return " / ".join(uniq)


def extract_base_fault(block_text: str):
    """
    '기본 과실비율 A50 B50' 또는 '기본과실 A 70 : B 30' 등에서
    base_fault_text, base_fault_ratio_json 뽑기
    """
    # 여러 표기 변형 대응
    # 예: "기본 과실비율 A50 B50"
    # 예: "기본과실 A 70 : B 30"
    m1 = re.search(r"기본\s*과실비율\s*(?:A\s*)?(\d{1,3})\s*(?:B\s*)?(\d{1,3})", block_text)
    if not m1:
        m1 = re.search(r"기본\s*과실\s*A\s*(\d{1,3})\s*[:：]\s*B\s*(\d{1,3})", block_text)

    if m1:
        a = int(m1.group(1))
        b = int(m1.group(2))
        base_text = f"A{a} B{b}"
        ratio_json = json.dumps({"A": a, "B": b}, ensure_ascii=False)
        return base_text, ratio_json

    return "", ""


def extract_accident_text(block_text: str) -> str:
    """
    '사고 상황' 섹션을 찾아 그 다음 내용을 일정 구간 뽑기
    """
    # 섹션 시작점 후보
    patterns = [
        r"사고\s*상황",
        r"\[사고상황\]",
        r"사고상황",
    ]
    start = None
    for pat in patterns:
        m = re.search(pat, block_text)
        if m:
            start = m.end()
            break
    if start is None:
        return ""

    tail = block_text[start:]
    # 다음 섹션(도표해설/관련법규/참고판례/수정요소) 전까지만
    stop = re.search(r"\[도표해설\]|\[관련법규\]|\[참고판례\]|수정요소|기본\s*과실", tail)
    chunk = tail[:stop.start()] if stop else tail
    chunk = chunk.strip()

    # 너무 길면 적당히 컷(필요 시 조정)
    return chunk[:2000].strip()


def extract_explanation(block_text: str) -> str:
    """
    [도표해설]부터 다음 대괄호 섹션 전까지를 explanation_text로.
    """
    m = re.search(r"\[도표해설\]", block_text)
    if not m:
        return ""

    tail = block_text[m.end():]
    stop = re.search(r"\[관련법규\]|\[참고판례\]|\[심의결정사례\]", tail)
    chunk = tail[:stop.start()] if stop else tail
    return chunk.strip()[:4000]


def make_clean_text(row: dict) -> str:
    parts = []
    parts.append(f"[사고유형] {row.get('case_code','')}")
    parts.append(f"[제목] {row.get('title','')}".strip())
    if row.get("participants_text"):
        parts.append(f"\n[당사자]\n{row['participants_text']}")
    if row.get("accident_text"):
        parts.append(f"\n[사고상황]\n{row['accident_text']}")
    if row.get("base_fault_text") or row.get("base_fault_ratio_json"):
        parts.append(f"\n[기본과실]\n{row.get('base_fault_text','')}\n{row.get('base_fault_ratio_json','')}")
    if row.get("explanation_text"):
        parts.append(f"\n[도표해설]\n{row['explanation_text']}")
    return "\n".join([p for p in parts if p and p.strip()])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--template_csv", required=True, help="샘플 CSV(구조/케이스코드 기준)")
    ap.add_argument("--out_csv", required=True, help="결과 CSV 저장 경로")
    ap.add_argument("--html", default="", help="structured.html 경로(있으면 우선 사용)")
    ap.add_argument("--pdf", default="", help="PDF 경로(HTML이 없거나 실패하면 사용)")
    ap.add_argument("--case_codes", default="", help="추출할 case_code를 콤마로 지정(미지정 시 template_csv의 case_code 사용)")
    args = ap.parse_args()

    template = pd.read_csv(args.template_csv)
    if "case_code" not in template.columns:
        raise ValueError("template_csv에 case_code 컬럼이 없습니다.")

    # 추출 대상 case_code 목록
    if args.case_codes.strip():
        target_codes = [c.strip() for c in args.case_codes.split(",") if c.strip()]
    else:
        target_codes = template["case_code"].astype(str).tolist()

    # 소스 텍스트 만들기
    source_text = ""
    if args.html:
        source_text = extract_text_from_html(args.html)
    if (not source_text.strip()) and args.pdf:
        source_text = extract_text_from_pdf(args.pdf)
    if not source_text.strip():
        raise ValueError("입력 소스가 비었습니다. --html 또는 --pdf를 제공하세요.")

    source_text = normalize(source_text)

    # 사고유형 단위 블록 분할
    blocks = split_into_case_blocks(source_text)

    # template 구조 그대로 결과 프레임 생성
    out = template.copy()

    # 각 케이스 채우기
    for i, code in enumerate(out["case_code"].astype(str).tolist()):
        if code not in target_codes:
            continue

        block = blocks.get(code, "")
        if not block:
            # 못 찾으면 빈 값 유지
            continue

        title = pick_title(block, code)
        participants = extract_participants(block)
        base_text, ratio_json = extract_base_fault(block)
        accident_text = extract_accident_text(block)
        explanation = extract_explanation(block)

        # 컬럼이 존재할 때만 채우기(샘플 CSV 구조 준수)
        if "title" in out.columns: out.at[i, "title"] = title
        if "participants_text" in out.columns: out.at[i, "participants_text"] = participants
        if "accident_text" in out.columns: out.at[i, "accident_text"] = accident_text
        if "base_fault_text" in out.columns: out.at[i, "base_fault_text"] = base_text
        if "base_fault_ratio_json" in out.columns: out.at[i, "base_fault_ratio_json"] = ratio_json
        if "explanation_text" in out.columns: out.at[i, "explanation_text"] = explanation

        # clean_text는 위 필드 조합으로 생성
        if "clean_text" in out.columns:
            row_dict = {
                "case_code": code,
                "title": title,
                "participants_text": participants,
                "accident_text": accident_text,
                "base_fault_text": base_text,
                "base_fault_ratio_json": ratio_json,
                "explanation_text": explanation,
            }
            out.at[i, "clean_text"] = make_clean_text(row_dict)

    Path(args.out_csv).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out_csv, index=False, encoding="utf-8-sig")
    print(f"[OK] saved -> {args.out_csv}")


if __name__ == "__main__":
    main()
