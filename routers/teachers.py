from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import Teacher
from schemas import TeacherCreate, TeacherOut
from passlib.context import CryptContext

router = APIRouter()
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/", response_model=TeacherOut)
async def create_teacher(data: TeacherCreate, db: AsyncSession = Depends(get_db)):
    
    # Check if email already exists
    result = await db.execute(select(Teacher).where(Teacher.email == data.email))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create new teacher
    teacher = Teacher(
        full_name=data.full_name,
        email=data.email,
        password_hash=pwd.hash(data.password)
    )
    db.add(teacher)
    await db.commit()
    await db.refresh(teacher)
    return teacher
    # Get all teachers
@router.get("/", response_model=List[TeacherOut])
async def get_teachers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Teacher))
    teachers = result.scalars().all()
    return teachers