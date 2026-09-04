from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse


PROJECT_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = PROJECT_DIR / "frontend"
DATA_DIR = PROJECT_DIR / "data" / "gallery_cases"
CATALOG_PATH = PROJECT_DIR / "data" / "catalog.json"
NO_CACHE_HEADERS = {"Cache-Control": "no-store"}
IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")

app = FastAPI(title="InFlak Case Gallery", version="1.0.0")


def _catalog() -> dict[str, Any]:
    try:
        payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Gallery catalog is unavailable: {error}") from error
    if not isinstance(payload, dict) or not isinstance(payload.get("cases"), list):
        raise RuntimeError("Gallery catalog has an invalid structure.")
    return payload


def _safe_identifier(value: str) -> str:
    if not IDENTIFIER_PATTERN.fullmatch(value):
        raise HTTPException(status_code=404, detail="Gallery item not found.")
    return value


def _case(case_id: str) -> dict[str, Any]:
    safe_case_id = _safe_identifier(case_id)
    for item in _catalog()["cases"]:
        if item.get("caseId") == safe_case_id:
            return item
    raise HTTPException(status_code=404, detail="Gallery case not found.")


def _confined_file(relative_path: str) -> Path:
    candidate = (DATA_DIR / relative_path).resolve()
    try:
        candidate.relative_to(DATA_DIR.resolve())
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Gallery file not found.") from error
    if not candidate.is_file():
        raise HTTPException(status_code=404, detail="Gallery file not found.")
    return candidate


@app.get("/health")
async def health() -> dict[str, Any]:
    return {"ok": True, "projectDir": str(PROJECT_DIR), "caseCount": len(_catalog()["cases"])}


@app.get("/")
async def root() -> RedirectResponse:
    return RedirectResponse(url="/gallery/")


@app.get("/gallery/")
async def gallery() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "gallery.html", headers=NO_CACHE_HEADERS)


@app.get("/gallery/gallery.css")
async def gallery_css() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "gallery.css", headers=NO_CACHE_HEADERS)


@app.get("/gallery/gallery.js")
async def gallery_js() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "gallery.js", headers=NO_CACHE_HEADERS)


@app.get("/assets/inflak-logo.png")
async def logo() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "assets" / "inflak-logo.png")


@app.get("/api/gallery/cases")
async def gallery_cases() -> dict[str, Any]:
    payload = _catalog()
    cases = [
        {key: value for key, value in item.items() if key not in {"videoFile", "historyFile"}}
        for item in payload["cases"]
    ]
    return {"cases": cases, "count": len(cases), "facets": payload["facets"]}


@app.get("/api/gallery/cases/{case_id}/video")
async def gallery_case_video(case_id: str) -> FileResponse:
    item = _case(case_id)
    path = _confined_file(str(item.get("videoFile") or ""))
    return FileResponse(path, media_type="video/mp4", headers={"Cache-Control": "public, max-age=3600"})


@app.get("/api/gallery/cases/{case_id}/runs/{run_id}/history")
async def gallery_case_history(case_id: str, run_id: str) -> FileResponse:
    item = _case(case_id)
    safe_run_id = _safe_identifier(run_id)
    run = item.get("run") or {}
    if str(run.get("runId") or "") != safe_run_id:
        raise HTTPException(status_code=404, detail="Gallery history not found.")
    path = _confined_file(str(item.get("historyFile") or ""))
    return FileResponse(path, media_type="application/x-ndjson", headers=NO_CACHE_HEADERS)
