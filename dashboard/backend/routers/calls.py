import os
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..models import CallRecord, Agent
from ..schemas import CallRecordRead
from ..auth import get_current_user

router = APIRouter(prefix="/calls", tags=["calls"])


@router.get("")
def list_calls(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    escalated: Optional[bool] = None,
    language: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    _: Agent = Depends(get_current_user),
):
    query = db.query(CallRecord)

    if date_from:
        query = query.filter(CallRecord.start_time >= date_from)
    if date_to:
        query = query.filter(CallRecord.start_time <= date_to)
    if escalated is not None:
        query = query.filter(CallRecord.escalated == escalated)
    if language:
        query = query.filter(CallRecord.language == language)

    total = query.count()
    records = query.order_by(CallRecord.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {"total": total, "page": page, "page_size": page_size, "items": records}


@router.get("/{call_id}", response_model=CallRecordRead)
def get_call(
    call_id: int,
    db: Session = Depends(get_db),
    _: Agent = Depends(get_current_user),
):
    record = db.query(CallRecord).filter(CallRecord.id == call_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Call record not found")
    return record


@router.get("/{call_id}/audio")
def get_audio(
    call_id: int,
    db: Session = Depends(get_db),
    _: Agent = Depends(get_current_user),
):
    record = db.query(CallRecord).filter(CallRecord.id == call_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Call record not found")
    if not record.audio_path or not os.path.exists(record.audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(record.audio_path, media_type="audio/wav")
