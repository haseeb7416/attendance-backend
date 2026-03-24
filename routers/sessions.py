from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import Session
from schemas import SessionCreate, SessionOut
from typing import List
import datetime

router = APIRouter()

# Start a new session
@router.post("/", response_model=SessionOut)
async def start_session(data: SessionCreate, db: AsyncSession = Depends(get_db)):

    # Check if there is already an active session for this class
    result = await db.execute(
        select(Session).where(
            Session.class_id == data.class_id,
            Session.status == "active"
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="A session is already active for this class")

    new_session = Session(
        class_id=data.class_id,
        teacher_id=data.teacher_id
    )
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    return new_session


# End a session
@router.post("/{session_id}/end")
async def end_session(session_id: str, db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status == "ended":
        raise HTTPException(status_code=400, detail="Session already ended")

    session.status = "ended"
    session.ended_at = datetime.datetime.utcnow()
    await db.commit()
    return {"message": "Session ended successfully"}


# Get session status (AI polls this)
@router.get("/{session_id}")
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "id": str(session.id),
        "class_id": str(session.class_id),
        "status": session.status,
        "started_at": session.started_at,
        "ended_at": session.ended_at
    }


# Get all past sessions for a class
@router.get("/", response_model=List[SessionOut])
async def get_sessions(class_id: str, db: AsyncSession = Depends(get_db)):

    result = await db.execute(
        select(Session).where(Session.class_id == class_id)
    )
    sessions = result.scalars().all()
    return sessions