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


def require_env(keys: List[str]) -> None:
    missing = [k for k in keys if not os.environ.get(k)]
    if missing:
        raise KeyError(f"Missing env vars: {missing}")


def choose_from_list(options: List[Any], title: str) -> Optional[Any]:
    """
    options: 문자열 리스트 또는 (case_code,title) 객체 리스트 등
    - q 입력: 종료
    - b 입력: 뒤로가기
    - ? 입력: 모르겠어요(나중에 벡터검색 붙일 자리)
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


def main():
    require_env(["MYSQL_HOST", "MYSQL_PORT", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DB"])

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
    # 실제론 UI에서 1단계 클릭이지만, CLI에서는 고정 옵션으로 제공
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
                print("※ HELP: (나중에 Neo4j 벡터추천 붙일 자리)")
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
                print("※ HELP: (나중에 Neo4j 벡터추천 붙일 자리)")
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
                print("※ HELP: (나중에 Neo4j 벡터추천 붙일 자리)")
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
                print("※ HELP: title 단계에서는 보통 help 안 씀(필요하면 설계 가능)")
                continue

            print("\n✅ 최종 확정!")
            print("case_code:", chosen.case_code)
            print("title    :", chosen.title)
            return

        print("❌ 예상치 못한 next_level:", next_level)
        return


if __name__ == "__main__":
    main()
