from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import Class
from schemas import ClassCreate, ClassOut
from typing import List

router = APIRouter()

# Create a class
@router.post("/", response_model=ClassOut)
async def create_class(data: ClassCreate, db: AsyncSession = Depends(get_db)):

    # Check if course code already exists
    result = await db.execute(select(Class).where(Class.course_code == data.course_code))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Course code already exists")

    new_class = Class(
        name=data.name,
        course_code=data.course_code,
        teacher_id=data.teacher_id
    )
    db.add(new_class)
    await db.commit()
    await db.refresh(new_class)
    return new_class


# Get all classes for a teacher
@router.get("/", response_model=List[ClassOut])
async def get_classes(teacher_id: str, db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(Class).where(Class.teacher_id == teacher_id))
    classes = result.scalars().all()
    return classes


# Get one class
@router.get("/{class_id}", response_model=ClassOut)
async def get_class(class_id: str, db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(Class).where(Class.id == class_id))
    one_class = result.scalar_one_or_none()

    if not one_class:
        raise HTTPException(status_code=404, detail="Class not found")

    return one_class
