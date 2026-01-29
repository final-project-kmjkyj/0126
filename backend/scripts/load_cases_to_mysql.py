from dotenv import load_dotenv
load_dotenv()

"""
CSV -> MySQL 적재 스크립트 (MVP 최소 버전)

- 전제:
  - CSV는 이미 정제됨 (노이즈 컬럼 제거됨)
  - base_fault_ratio_json은 TEXT로 그대로 저장
  - .env에 MYSQL_* 환경변수 세팅되어 있음
"""

import os
import pandas as pd
import pymysql


def to_none(x):
    if pd.isna(x):
        return None
    return x


def main():
    # 환경변수에서만 읽는다 (코드에 기본값 안 둠)
    csv_path = os.environ["CASES_CSV_PATH"]

    conn = pymysql.connect(
        host=os.environ["MYSQL_HOST"],
        port=int(os.environ["MYSQL_PORT"]),
        user=os.environ["MYSQL_USER"],
        password=os.environ["MYSQL_PASSWORD"],
        db=os.environ["MYSQL_DB"],
        charset="utf8mb4",
        autocommit=False,
    )

    df = pd.read_csv(csv_path)

    insert_sql = """
    INSERT INTO cases (
      domain_l1, case_code, route_l2, route_l3, route_l4,
      title, participants_text, base_fault_text, base_fault_ratio_json,
      adjustment_text, accident_text,
      base_fault_explanation, modifier_explanation, related_law, precedent,
      clean_text, url, question
    )
    VALUES (
      %s,%s,%s,%s,%s,
      %s,%s,%s,%s,
      %s,%s,
      %s,%s,%s,%s,
      %s,%s,%s
    )
    ON DUPLICATE KEY UPDATE
      domain_l1=VALUES(domain_l1),
      route_l2=VALUES(route_l2),
      route_l3=VALUES(route_l3),
      route_l4=VALUES(route_l4),
      title=VALUES(title),
      participants_text=VALUES(participants_text),
      base_fault_text=VALUES(base_fault_text),
      base_fault_ratio_json=VALUES(base_fault_ratio_json),
      adjustment_text=VALUES(adjustment_text),
      accident_text=VALUES(accident_text),
      base_fault_explanation=VALUES(base_fault_explanation),
      modifier_explanation=VALUES(modifier_explanation),
      related_law=VALUES(related_law),
      precedent=VALUES(precedent),
      clean_text=VALUES(clean_text),
      url=VALUES(url),
      question=VALUES(question);
    """

    try:
        with conn.cursor() as cur:
            for _, r in df.iterrows():
                cur.execute(
                    insert_sql,
                    (
                        to_none(r["domain_l1"]),
                        to_none(r["case_code"]),
                        to_none(r["route_l2"]),
                        to_none(r["route_l3"]),
                        to_none(r["route_l4"]),
                        to_none(r["title"]),
                        to_none(r["participants_text"]),
                        to_none(r["base_fault_text"]),
                        to_none(r["base_fault_ratio_json"]),  # 그냥 TEXT
                        to_none(r["adjustment_text"]),
                        to_none(r["accident_text"]),
                        to_none(r["base_fault_explanation"]),
                        to_none(r["modifier_explanation"]),
                        to_none(r["related_law"]),
                        to_none(r["precedent"]),
                        to_none(r["clean_text"]),
                        to_none(r["url"]),
                        to_none(r["question"]),
                    ),
                )

        conn.commit()
        print(f"[OK] {len(df)} rows upserted into cases")

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    main()
