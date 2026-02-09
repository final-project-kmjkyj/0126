from fastapi import APIRouter
import os
import pymysql
from neo4j import GraphDatabase

router = APIRouter(prefix="/infra", tags=["infra"])

@router.get("/mysql/count")
def mysql_count():
    conn = pymysql.connect(
        host=os.environ["MYSQL_HOST"],
        port=int(os.environ["MYSQL_PORT"]),
        user=os.environ["MYSQL_USER"],
        password=os.environ["MYSQL_PASSWORD"],
        db=os.environ["MYSQL_DB"],
        charset="utf8mb4",
        autocommit=True,
    )
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM cases")
            (cnt,) = cur.fetchone()
        return {"cases": cnt}
    finally:
        conn.close()


@router.get("/neo4j/count")
def neo4j_count():
    driver = GraphDatabase.driver(
        os.environ["NEO4J_BOLT_URL"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
    )
    try:
        with driver.session() as session:
            rec = session.run("MATCH (c:Case) RETURN count(c) AS cnt").single()
            return {"cases": rec["cnt"]}
    finally:
        driver.close()
