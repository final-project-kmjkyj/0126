from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.env import load_env

load_env()

app = FastAPI()

# CORS (프론트 분리면 일단 전체 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ routes가 app/api/routes 밑에 있으니 여기로 import
from app.api.routes.tree import router as tree_router
from app.api.routes.help import router as help_router
from app.api.routes.cases import router as case_router
from app.api.routes.infra import router as infra_router
# (있으면) from app.api.routes.labels import router as labels_router

app.include_router(tree_router)
app.include_router(help_router)
app.include_router(case_router)
app.include_router(infra_router)
# app.include_router(labels_router)

@app.get("/health")
def health():
    return {"ok": True}
