from fastapi import APIRouter
from fastapi.responses import JSONResponse
import json
from pathlib import Path

router = APIRouter(prefix="/labels", tags=["labels"])

@router.get("/route")
def route_labels():
    # 프로젝트 루트 data/route_labels_ko.json
    root = Path(__file__).resolve().parents[3]  # .../backend/app/routes -> .../kmjkyj_infra
    path = root / "data" / "route_labels_ko.json"
    return JSONResponse(json.loads(path.read_text(encoding="utf-8")))
