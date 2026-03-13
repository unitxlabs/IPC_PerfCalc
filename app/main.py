import csv
import io
from pathlib import Path
from typing import List

from fastapi import FastAPI, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .config import settings
from .db import Base, engine, get_db
from . import models, schemas
from .perf_core.perf_calc import estimate_perf
from .perf_core.perf_schema import PerfEvalInput, PerfEvalResult


# Create tables on startup (simple approach for MVP)
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
ASSETS_DIR = STATIC_DIR / "assets"
INDEX_FILE = STATIC_DIR / "index.html"


@app.get(f"{settings.api_prefix}/options", response_model=schemas.OptionsOut)
def get_options(db: Session = Depends(get_db)):
    """Provide dropdown options for frontend."""
    ipc_models = db.query(models.IPCModel).all()

    # Static enums aligned with ERD; adjust when data grows
    resolutions = [5, 12, 24]
    camera_counts = list(range(1, 9))
    model_counts = [2, 3, 4, 5, 6, 7, 8, 9, 10]
    software_versions = [
        v[0]
        for v in db.query(models.TestRecord.software_version)
        .distinct()
        .order_by(models.TestRecord.software_version)
        .all()
    ]

    return schemas.OptionsOut(
        ipc_models=ipc_models,
        resolutions=resolutions,
        camera_counts=camera_counts,
        model_counts=model_counts,
        software_versions=software_versions,
    )


@app.post(
    f"{settings.api_prefix}/records/search",
    response_model=List[schemas.TestRecordOut],
)
def search_records(payload: schemas.RecordSearchRequest, db: Session = Depends(get_db)):
    """Search historical test records with simple filters."""
    query = db.query(models.TestRecord)

    if payload.ipc_model_ids:
        query = query.filter(models.TestRecord.ipc_model_id.in_(payload.ipc_model_ids))
    if payload.resolution_mp is not None:
        query = query.filter(models.TestRecord.resolution_mp == payload.resolution_mp)
    if payload.camera_count is not None:
        query = query.filter(models.TestRecord.camera_count == payload.camera_count)
    if payload.model_count is not None:
        query = query.filter(models.TestRecord.model_count == payload.model_count)
    if payload.software_versions:
        query = query.filter(
            models.TestRecord.software_version.in_(payload.software_versions)
        )

    results = query.order_by(models.TestRecord.created_at.desc()).all()
    return results


@app.post("/perf/eval", response_model=PerfEvalResult)
def eval_perf(inp: PerfEvalInput):
    return estimate_perf(inp)


def _parse_bool(val: str) -> bool:
    return str(val).strip().lower() in {"1", "true", "yes", "y"}


@app.post(
    f"{settings.api_prefix}/records/import",
    response_model=schemas.ImportResult,
)
def import_records(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Import records from CSV (expects comma delimiter)."""
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="仅支持 CSV 文件")

    content = file.file.read().decode("utf-8-sig")
    reader = csv.reader(io.StringIO(content))

    inserted = 0
    skipped = 0
    errors: List[str] = []
    ipc_cache = {}

    for idx, row in enumerate(reader, start=1):
        if not row or all(not str(c).strip() for c in row):
            continue

        # Skip headers containing keywords
        if any(keyword in row[0] for keyword in ["Camera", "相机", "第 1 列"]):
            continue

        try:
            name = row[0].strip()
            resolution_mp = int(float(row[1]))
            camera_count = int(float(row[2]))
            image_count = int(float(row[3])) if len(row) > 3 and row[3] else None
            save_image = _parse_bool(row[4]) if len(row) > 4 and row[4] else None
            software_version = row[5].strip() if len(row) > 5 else ""
            perf = float(row[6]) if len(row) > 6 and row[6] else None
            ex_perf = float(row[7]) if len(row) > 7 and row[7] else None
        except Exception as exc:  # noqa: BLE001
            skipped += 1
            errors.append(f"行{idx}: 解析错误 ({exc}) -> {row}")
            continue

        if not name or perf is None:
            skipped += 1
            errors.append(f"行{idx}: 缺少必填字段 name/performance -> {row}")
            continue

        ipc = ipc_cache.get(name)
        if not ipc:
            ipc = db.query(models.IPCModel).filter(models.IPCModel.name == name).first()
            if not ipc:
                ipc = models.IPCModel(name=name)
                db.add(ipc)
                db.flush()  # get id
            ipc_cache[name] = ipc

        record = models.TestRecord(
            ipc_model_id=ipc.id,
            software_version=software_version or "unknown",
            resolution_mp=resolution_mp,
            camera_count=camera_count,
            model_count=2,
            segments_count=50,
            image_count=image_count,
            save_image=1 if save_image else 0 if save_image is not None else None,
            measured_perf_mps=perf,
            ex_perf_mps=ex_perf,
        )
        db.add(record)
        inserted += 1

    db.commit()

    return schemas.ImportResult(
        inserted=inserted,
        skipped=skipped,
        errors=errors or None,
    )


@app.get("/healthz")
def health_check():
    return {"status": "ok"}


# Serve built frontend after API routes are defined to avoid shadowing /api
if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")


@app.get("/", include_in_schema=False)
def serve_index():
    if INDEX_FILE.exists():
        return FileResponse(INDEX_FILE)
    return {"message": "Frontend not built"}


@app.get("/{full_path:path}", include_in_schema=False)
def serve_spa(full_path: str):
    # Let API routes handle /api/... normally
    if full_path.startswith("api/") or full_path == "api":
        raise HTTPException(status_code=404, detail="Not Found")
    if INDEX_FILE.exists():
        return FileResponse(INDEX_FILE)
    raise HTTPException(status_code=404, detail="Not Found")
