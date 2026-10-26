"""Analysis history routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import AnalysisHistory
from app.schemas.schemas import HistoryItem
from app.core.logging import get_logger

router = APIRouter(prefix="/api/v1/history", tags=["history"])
logger = get_logger(__name__)


@router.get("/", response_model=list[HistoryItem])
async def list_history(
    limit: int = 50,
    skip: int = 0,
    db: Session = Depends(get_db),
):
    """List analysis history records."""
    records = (
        db.query(AnalysisHistory)
        .order_by(AnalysisHistory.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return records


@router.get("/{analysis_id}")
async def get_history_item(analysis_id: str, db: Session = Depends(get_db)):
    """Get a specific history record by analysis_id."""
    record = db.query(AnalysisHistory).filter(
        AnalysisHistory.analysis_id == analysis_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Analysis record not found.")
    import json
    result = {
        "id": record.id,
        "analysis_id": record.analysis_id,
        "input_type": record.input_type,
        "analysis_type": record.analysis_type,
        "food_name": record.food_name,
        "provider": record.provider,
        "is_demo": record.is_demo,
        "created_at": record.created_at.isoformat(),
        "result": json.loads(record.result_json) if record.result_json else None,
    }
    return result


@router.delete("/{analysis_id}")
async def delete_history_item(analysis_id: str, db: Session = Depends(get_db)):
    """Delete a history record."""
    record = db.query(AnalysisHistory).filter(
        AnalysisHistory.analysis_id == analysis_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Analysis record not found.")
    db.delete(record)
    db.commit()
    return {"status": "deleted"}
