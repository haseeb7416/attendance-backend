from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import AttendanceRecord, Student, Session
from schemas import AttendancePayload, AttendanceReport
from typing import List

router = APIRouter()

# Calculate final engagement from counts
def calculate_engagement(engaged, distracted, sleeping, phone):
    total = engaged + distracted + sleeping + phone

    if total == 0:
        return None

    percentages = {
        "ENGAGED":      (engaged    / total) * 100,
        "DISTRACTED":   (distracted / total) * 100,
        "SLEEPING":     (sleeping   / total) * 100,
        "USING_PHONE":  (phone      / total) * 100
    }

    # Rule 1: sleeping 30% or more → SLEEPING
    if percentages["SLEEPING"] >= 30:
        return "SLEEPING"

    # Rule 2: phone 30% or more → USING_PHONE
    if percentages["USING_PHONE"] >= 30:
        return "USING_PHONE"

    # Rule 3: engaged 50% or more → ENGAGED
    if percentages["ENGAGED"] >= 50:
        return "ENGAGED"

    # Rule 4: everything else → DISTRACTED
    return "DISTRACTED"


# AI submits attendance results
@router.post("/sessions/{session_id}/submit")
async def submit_attendance(
    session_id: str,
    payload: AttendancePayload,
    db: AsyncSession = Depends(get_db)
):
    # Check session exists
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Save each student result
    for item in payload.results:

        # Get engagement counts
        counts = item.engagement_counts
        engaged    = counts.ENGAGED     if counts else 0
        distracted = counts.DISTRACTED  if counts else 0
        sleeping   = counts.SLEEPING    if counts else 0
        phone      = counts.USING_PHONE if counts else 0

        # Calculate final engagement
        final_engagement = calculate_engagement(engaged, distracted, sleeping, phone)

        record = AttendanceRecord(
            session_id=session_id,
            student_id=item.student_id,
            final_status=item.final_status,
            confidence=item.confidence,
            engaged_count=engaged,
            distracted_count=distracted,
            sleeping_count=sleeping,
            phone_count=phone,
            final_engagement=final_engagement
        )
        db.add(record)

    await db.commit()
    return {"message": "Attendance saved", "total": len(payload.results)}


# Mobile app fetches attendance report
@router.get("/sessions/{session_id}/report", response_model=List[AttendanceReport])
async def get_report(session_id: str, db: AsyncSession = Depends(get_db)):

    # Check session exists
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get all attendance records with student info
    result = await db.execute(
        select(AttendanceRecord, Student)
        .join(Student, AttendanceRecord.student_id == Student.id)
        .where(AttendanceRecord.session_id == session_id)
    )
    rows = result.all()

    if not rows:
        raise HTTPException(status_code=404, detail="No attendance records found for this session")

    return [
        AttendanceReport(
            student_id=record.student_id,
            full_name=student.full_name,
            student_code=student.student_code,
            final_status=record.final_status,
            confidence=record.confidence,
            final_engagement=record.final_engagement,
            engaged_count=record.engaged_count,
            distracted_count=record.distracted_count,
            sleeping_count=record.sleeping_count,
            phone_count=record.phone_count
        )
        for record, student in rows
    ]


# Get one student's full attendance history
@router.get("/students/{student_id}/history")
async def get_student_history(student_id: str, db: AsyncSession = Depends(get_db)):

    # Check student exists
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Get all records for this student
    result = await db.execute(
        select(AttendanceRecord, Session)
        .join(Session, AttendanceRecord.session_id == Session.id)
        .where(AttendanceRecord.student_id == student_id)
    )
    rows = result.all()

    return {
        "student_id": str(student_id),
        "full_name": student.full_name,
        "student_code": student.student_code,
        "total_sessions": len(rows),
        "total_present": sum(1 for r, s in rows if r.final_status == "PRESENT"),
        "total_absent": sum(1 for r, s in rows if r.final_status == "ABSENT"),
        "history": [
            {
                "session_id": str(record.session_id),
                "date": session.started_at,
                "final_status": record.final_status,
                "final_engagement": record.final_engagement,
                "confidence": record.confidence
            }
            for record, session in rows
        ]
    }