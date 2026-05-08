from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import Student, StudentPhoto
from schemas import StudentCreate, StudentOut, PhotoEmbeddingUpdate, StudentPhotoOut, StudentPhotosAdd
from typing import List
import json
import shutil
import os

router = APIRouter()


# Upload a photo
@router.post("/upload-photo")
async def upload_photo(file: UploadFile = File(...)):
    os.makedirs("uploads", exist_ok=True)
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"photo_url": file_path}


# Create a student
@router.post("/", response_model=StudentOut)
async def create_student(data: StudentCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Student).where(Student.student_code == data.student_code))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Student code already exists")

    new_student = Student(
        full_name=data.full_name,
        student_code=data.student_code,
        class_id=data.class_id
    )
    db.add(new_student)
    await db.commit()
    await db.refresh(new_student)
    return new_student


# Add photos to a student
@router.post("/{student_id}/photos")
async def add_student_photos(
    student_id: str,
    data: StudentPhotosAdd,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    result = await db.execute(
        select(StudentPhoto).where(StudentPhoto.student_id == student_id)
    )
    existing_photos = result.scalars().all()
    if len(existing_photos) + len(data.photo_urls) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 photos allowed per student")

    for url in data.photo_urls:
        photo = StudentPhoto(
            student_id=student_id,
            photo_url=url
        )
        db.add(photo)

    await db.commit()
    return {"message": f"{len(data.photo_urls)} photos added successfully"}


# Get all photos for a student
@router.get("/{student_id}/photos", response_model=List[StudentPhotoOut])
async def get_student_photos(student_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(StudentPhoto).where(StudentPhoto.student_id == student_id)
    )
    photos = result.scalars().all()
    return photos


# Get photos with no embedding (AI polls this)
@router.get("/no-embedding")
async def get_students_no_embedding(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(StudentPhoto).where(StudentPhoto.face_embedding == None)
    )
    photos = result.scalars().all()
    return photos


# AI saves embedding for one photo
@router.put("/{student_id}/photos/{photo_id}/embedding")
async def update_photo_embedding(
    student_id: str,
    photo_id: str,
    data: PhotoEmbeddingUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(StudentPhoto).where(
            StudentPhoto.id == photo_id,
            StudentPhoto.student_id == student_id
        )
    )
    photo = result.scalar_one_or_none()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    photo.face_embedding = json.dumps(data.face_embedding)
    await db.commit()
    return {"message": "Embedding saved successfully"}


# Get all students in a class with embeddings (AI uses this)
@router.get("/")
async def get_students(class_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Student).where(Student.class_id == class_id)
    )
    students = result.scalars().all()

    response = []
    for student in students:
        photos_result = await db.execute(
            select(StudentPhoto).where(StudentPhoto.student_id == student.id)
        )
        photos = photos_result.scalars().all()

        response.append({
            "id": str(student.id),
            "full_name": student.full_name,
            "student_code": student.student_code,
            "embeddings": [
                json.loads(p.face_embedding)
                for p in photos
                if p.face_embedding is not None
            ]
        })

    return response


# Get one student
@router.get("/{student_id}", response_model=StudentOut)
async def get_student(student_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


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