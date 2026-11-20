"""Minimal FastAPI service. Week 1 exposes /health, /model/version and /analyze."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.models import MODEL_VERSION
from app.parsing import ParseError, parse_eml_bytes
from app.pipeline import analyze_message

app = FastAPI(title="Email Analyzer", version="0.1.0")


class AnalyzeRequest(BaseModel):
    raw_email: str = Field(min_length=1, description="Full raw email text, headers included")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/model/version")
def model_version() -> dict:
    return {"model_version": MODEL_VERSION}


@app.post("/analyze")
def analyze(request: AnalyzeRequest) -> dict:
    try:
        message = parse_eml_bytes(request.raw_email.encode("utf-8", errors="replace"))
    except ParseError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return analyze_message(message)
