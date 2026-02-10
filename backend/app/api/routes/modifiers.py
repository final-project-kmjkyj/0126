from fastapi import APIRouter, HTTPException
from app.repositories.neo4j_repo import Neo4jRepository

router = APIRouter(prefix="/modifiers", tags=["modifiers"])

@router.get("/{code}")
def get_modifier(code: str):
    neo = Neo4jRepository()  # ✅ 요청 시점 생성 (env load 이후)
    data = neo.get_modifier(code)
    if not data:
        raise HTTPException(status_code=404, detail="Modifier not found")
    return data
