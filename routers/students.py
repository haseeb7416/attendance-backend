
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import Student
from schemas import StudentCreate, StudentOut, EmbeddingUpdate
from typing import List
import json

router = APIRouter()

# Create a student
@router.post("/", response_model=StudentOut)
async def create_student(data: StudentCreate, db: AsyncSession = Depends(get_db)):

    # Check if student code already exists
    result = await db.execute(select(Student).where(Student.student_code == data.student_code))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Student code already exists")

    new_student = Student(
        full_name=data.full_name,
        student_code=data.student_code,
        class_id=data.class_id,
        photo_url=data.photo_url
    )
    db.add(new_student)
    await db.commit()
    await db.refresh(new_student)
    return new_student


# Get all students in a class
@router.get("/", response_model=List[StudentOut])
async def get_students(class_id: str, db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(Student).where(Student.class_id == class_id))
    students = result.scalars().all()
    return students


# Get one student
@router.get("/{student_id}", response_model=StudentOut)
async def get_student(student_id: str, db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    return student


# AI calls this to save face embedding
@router.put("/{student_id}/embedding")
async def update_embedding(student_id: str, data: EmbeddingUpdate, db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Convert list of numbers to string for storage
    student.face_embedding = json.dumps(data.face_embedding)
    await db.commit()
    return {"message": "Embedding saved successfully"}


# Delete a student
@router.delete("/{student_id}")
async def delete_student(student_id: str, db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    await db.delete(student)
    await db.commit()
    return {"message": "Student deleted successfully"}