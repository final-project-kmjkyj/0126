"""
backend/app/repositories/mysql_repo.py

[역할]
- MySQL 접근 레이어(선택)
  - run 저장(run_id, route_state, seed_case_id, debug, timestamps)
  - CSV 룰 테이블을 DB로 적재했다면:
    - route 조건 기반 후보군 조회(WHERE 필터)

[주의]
- MVP에서는 CSV를 pandas로 필터링해도 됨
- 운영/상용화를 생각하면 룰 테이블 + run 로그는 MySQL이 안정적
"""