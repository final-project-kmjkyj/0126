# backend/scripts/cli_mysql_tree.py
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any

from dotenv import load_dotenv

# ==========================================
# 1) import 경로 세팅: backend를 PYTHONPATH에 추가
# ==========================================
BACKEND_DIR = Path(__file__).resolve().parents[1]  # .../backend
sys.path.insert(0, str(BACKEND_DIR))

# ==========================================
# 2) .env 로드 (backend/.env -> 루트/.env 순으로 탐색)
# ==========================================
candidates = [BACKEND_DIR / ".env", BACKEND_DIR.parent / ".env"]
env_path = next((p for p in candidates if p.exists()), None)
if env_path is None:
    raise FileNotFoundError(f".env not found. tried: {candidates}")
load_dotenv(env_path)
print(f"[ENV] loaded from: {env_path}")

# ==========================================
# 3) Repo import
# ==========================================
from app.repositories.mysql_repo import MySQLCasesRepo  # noqa: E402

# [CHANGED] HELP(Neo4j Top3 추천) 연결
from app.repositories.neo4j_repo import Neo4jRepository, RouteState  # noqa: E402


def require_env(keys: List[str]) -> None:
    missing = [k for k in keys if not os.environ.get(k)]
    if missing:
        raise KeyError(f"Missing env vars: {missing}")


def choose_from_list(options: List[Any], title: str) -> Optional[Any]:
    """
    options: 문자열 리스트 또는 (case_code,title) 객체 리스트 등
    - q 입력: 종료
    - b 입력: 뒤로가기
    - ? 입력: 모르겠어요(HELP)
    """
    if not options:
        print("  (옵션 없음)")
        return None

    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

    for i, opt in enumerate(options, 1):
        if hasattr(opt, "case_code") and hasattr(opt, "title"):
            print(f"{i}. {opt.title}  [{opt.case_code}]")
        else:
            print(f"{i}. {opt}")

    while True:
        s = input("\n번호 입력 (b=뒤로, q=종료, ?=모르겠어요): ").strip().lower()
        if s == "q":
            return "QUIT"
        if s == "b":
            return "BACK"
        if s == "?":
            return "HELP"
        if s.isdigit():
            idx = int(s)
            if 1 <= idx <= len(options):
                return options[idx - 1]
        print("❌ 잘못된 입력. 다시 입력해줘.")


# =========================================================
# [CHANGED] HELP 처리 함수 추가
# =========================================================
def print_case_detail(detail: Dict[str, Any]) -> None:
    """MySQL 정본 상세 출력(가독성용)."""
    print("\n" + "#" * 70)
    print("✅ 최종 확정 결과 (MySQL 정본)")
    print("#" * 70)
    print("case_code :", detail.get("case_code"))
    print("title     :", detail.get("title"))
    print("domain_l1 :", detail.get("domain_l1"))
    print("route     :", detail.get("route_l2"), detail.get("route_l3"), detail.get("route_l4"))
    print("url       :", detail.get("url"))

    def show(label: str, key: str) -> None:
        v = detail.get(key)
        if v is None or (isinstance(v, str) and not v.strip()):
            print(f"\n[{label}] (EMPTY)")
        else:
            print(f"\n[{label}]\n{v}")

    show("PARTICIPANTS", "participants_text")
    show("BASE_FAULT", "base_fault_text")
    show("BASE_FAULT_RATIO_JSON", "base_fault_ratio_json")
    show("ADJUSTMENT", "adjustment_text")
    show("ACCIDENT", "accident_text")
    show("BASE_EXPL", "base_fault_explanation")
    show("MODIFIER_EXPL", "modifier_explanation")
    show("RELATED_LAW", "related_law")
    show("PRECEDENT", "precedent")


def handle_help(repo: MySQLCasesRepo, state: Dict[str, Optional[str]]) -> Optional[str]:
    """
    HELP(모르겠어요) 처리:
    1) MySQL에서 현재 버킷 question 목록 출력 (없으면 fallback 문구)
    2) user_note 입력
    3) Neo4j 벡터검색 Top3 추천 (현재 route 버킷 필터 포함)
    4) 사용자가 1개 선택 -> case_code 반환
    """
    print("\n" + "#" * 70)
    print("[HELP] 현재 버킷 question 표시 → user_note 입력 → Neo4j Top3 추천")
    print("#" * 70)

    # 1) 버킷 내 question 목록(MySQL)
    # - question은 201 중 82만 존재하므로, 0개일 수도 있음
    # [중요] mysql_repo.py에 list_help_questions(...)가 있어야 함
    qrows = repo.list_help_questions(
        state["domain_l1"],
        state["route_l2"],
        state["route_l3"],
        state["route_l4"],
    )

    if not qrows:
        print("⚠️ 이 버킷에는 question이 저장된 케이스가 없습니다.")
        print("➡️ 아래 정보로 사고 상황을 한 줄로 적어주세요:")
        print("   - 충돌 장소(교차로/횡단보도/차로변경 등)")
        print("   - 각 차량 진행방향/신호")
        print("   - 충돌 지점(좌/우측면, 후미 등)")
    else:
        # question 중복제거(같은 질문이 여러 케이스에 붙을 수 있음)
        seen = set()
        uniq = []
        for r in qrows:
            q = (r.get("question") or "").strip()
            if q and q not in seen:
                seen.add(q)
                uniq.append(q)

        print(f"question 후보 {len(uniq)}개(중복 제거) / row {len(qrows)}개")
        for i, q in enumerate(uniq, 1):
            print(f"{i}. {q}")

    # 2) user_note 입력
    user_note = input("\n사용자 메모(user_note)를 입력하세요: ").strip()
    if not user_note:
        print("❌ 입력이 비었습니다. HELP 종료.")
        return None

    # 3) Neo4j Top3 추천
    neo = Neo4jRepository()
    try:
        rs = RouteState(
            domain_l1=state["domain_l1"],
            route_l2=state["route_l2"],
            route_l3=state["route_l3"],
            route_l4=state["route_l4"],
        )
        top3 = neo.vector_topk_within_bucket(rs, user_note=user_note, topk=3)
    finally:
        neo.close()

    if not top3:
        print("❌ 추천 결과가 없습니다. (버킷 필터가 너무 강하거나 데이터 문제)")
        return None

    print("\n" + "=" * 60)
    print("[Neo4j 추천 Top3] (case_code / title / score)")
    print("=" * 60)
    for i, r in enumerate(top3, 1):
        score = r.get("score")
        score_s = f"{score:.4f}" if isinstance(score, (float, int)) else str(score)
        print(f"{i}. {r.get('case_code')} | {r.get('title')} | score={score_s}")

    # 4) 사용자 선택
    while True:
        s = input("\n선택 번호 입력(1~3, b=취소): ").strip().lower()
        if s == "b":
            return None
        if s.isdigit():
            idx = int(s)
            if 1 <= idx <= len(top3):
                return top3[idx - 1]["case_code"]
        print("❌ 잘못된 입력. 다시 입력해줘.")


def main():
    # [CHANGED] Neo4j env도 체크
    require_env(
        [
            "MYSQL_HOST",
            "MYSQL_PORT",
            "MYSQL_USER",
            "MYSQL_PASSWORD",
            "MYSQL_DB",
            "NEO4J_BOLT_URL",
            "NEO4J_USER",
            "NEO4J_PASSWORD",
            "NEO4J_VECTOR_INDEX",
        ]
    )

    repo = MySQLCasesRepo()

    # ---------------------------
    # state (사용자 클릭 누적)
    # ---------------------------
    state: Dict[str, Optional[str]] = {
        "domain_l1": None,
        "route_l2": None,
        "route_l3": None,
        "route_l4": None,
    }
    history: List[Dict[str, Optional[str]]] = []

    # ---------------------------
    # 0) domain_l1 선택(간단)
    # ---------------------------
    domain_options = ["CAR_CAR", "CAR_PED", "CAR_BIK"]
    choice = choose_from_list(domain_options, "1단계: domain_l1 선택")
    if choice in ("QUIT", None):
        print("종료")
        return
    state["domain_l1"] = choice

    while True:
        # 스냅샷 저장(뒤로가기용)
        history.append(state.copy())

        # 현재 후보 수
        cnt = repo.count_candidates(
            state["domain_l1"],
            state["route_l2"],
            state["route_l3"],
            state["route_l4"],
        )
        print("\n" + "-" * 60)
        print("[STATE]", state, "| candidates:", cnt)
        print("-" * 60)

        # 다음 단계 후보 산출
        nxt = repo.infer_next_options(
            state["domain_l1"],
            state["route_l2"],
            state["route_l3"],
            state["route_l4"],
        )
        next_level = nxt["next_level"]

        # route_l2는 infer_next_options에서 options 비워둔 상태라 여기서 직접 뽑음
        if next_level == "route_l2":
            opts = repo.list_distinct("route_l2", state["domain_l1"])
            chosen = choose_from_list(opts, "2단계: route_l2 선택")
            if chosen == "QUIT":
                print("종료")
                return
            if chosen == "BACK":
                history.pop()  # 현재 스냅샷 제거
                if len(history) >= 2:
                    history.pop()
                    state = history[-1].copy()
                else:
                    print("더 이상 뒤로갈 수 없음.")
                continue
            if chosen == "HELP":
                # [CHANGED] HELP 연결
                picked = handle_help(repo, state)
                if picked:
                    detail = repo.get_case_detail(picked)
                    print_case_detail(detail)
                    return
                continue

            state["route_l2"] = chosen
            continue

        if next_level == "route_l3":
            opts = nxt["options"]
            chosen = choose_from_list(opts, "3단계: route_l3 선택")
            if chosen == "QUIT":
                print("종료")
                return
            if chosen == "BACK":
                history.pop()
                if len(history) >= 2:
                    history.pop()
                    state = history[-1].copy()
                else:
                    print("더 이상 뒤로갈 수 없음.")
                continue
            if chosen == "HELP":
                # [CHANGED] HELP 연결
                picked = handle_help(repo, state)
                if picked:
                    detail = repo.get_case_detail(picked)
                    print_case_detail(detail)
                    return
                continue

            state["route_l3"] = chosen
            continue

        if next_level == "route_l4":
            opts = nxt["options"]
            chosen = choose_from_list(opts, "4단계: route_l4 선택")
            if chosen == "QUIT":
                print("종료")
                return
            if chosen == "BACK":
                history.pop()
                if len(history) >= 2:
                    history.pop()
                    state = history[-1].copy()
                else:
                    print("더 이상 뒤로갈 수 없음.")
                continue
            if chosen == "HELP":
                # [CHANGED] HELP 연결
                picked = handle_help(repo, state)
                if picked:
                    detail = repo.get_case_detail(picked)
                    print_case_detail(detail)
                    return
                continue

            state["route_l4"] = chosen
            continue

        if next_level == "title":
            # 최종 title 선택 (가상 route_l5)
            titles = repo.list_titles(
                state["domain_l1"],
                route_l2=state["route_l2"],
                route_l3=state["route_l3"],
                route_l4=state["route_l4"],
            )
            chosen = choose_from_list(titles, "최종: title 선택 (case_code 확정)")
            if chosen == "QUIT":
                print("종료")
                return
            if chosen == "BACK":
                history.pop()
                if len(history) >= 2:
                    history.pop()
                    state = history[-1].copy()
                else:
                    print("더 이상 뒤로갈 수 없음.")
                continue
            if chosen == "HELP":
                # title 단계에서도 HELP를 쓸 수는 있지만, UX상 보통 안 씀
                print("※ HELP: title 단계에서는 보통 help 안 씀(필요하면 설계 가능)")
                continue

            # [CHANGED] 최종 확정 후 MySQL 상세 출력까지
            detail = repo.get_case_detail(chosen.case_code)
            print_case_detail(detail)
            return

        print("❌ 예상치 못한 next_level:", next_level)
        return


if __name__ == "__main__":
    main()
