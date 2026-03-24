from pydantic import BaseModel, EmailStr
from typing import Optional, List
from uuid import UUID
from datetime import datetime

# Auth
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Teacher
class TeacherCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str

class TeacherOut(BaseModel):
    id: UUID
    full_name: str
    email: str
    class Config:
        from_attributes = True

# Class
class ClassCreate(BaseModel):
    name: str
    course_code: str
    teacher_id: UUID

class ClassOut(BaseModel):
    id: UUID
    name: str
    course_code: str
    teacher_id: UUID
    class Config:
        from_attributes = True

# Student
class StudentCreate(BaseModel):
    full_name: str
    student_code: str
    class_id: UUID
    photo_url: Optional[str] = None

class StudentOut(BaseModel):
    id: UUID
    full_name: str
    student_code: str
    class_id: UUID
    photo_url: Optional[str]
    class Config:
        from_attributes = True

class EmbeddingUpdate(BaseModel):
    face_embedding: List[float]

# Session
class SessionCreate(BaseModel):
    class_id: UUID
    teacher_id: UUID
class SessionOut(BaseModel):
    id: UUID
    class_id: UUID
    status: str
    started_at: datetime
    class Config:
        from_attributes = True

# Attendance
class EngagementCounts(BaseModel):
    ENGAGED: int = 0
    DISTRACTED: int = 0
    SLEEPING: int = 0
    USING_PHONE: int = 0

class SingleResult(BaseModel):
    student_id: UUID
    final_status: str
    confidence: Optional[float] = None
    engagement_counts: Optional[EngagementCounts] = None

class AttendancePayload(BaseModel):
    results: List[SingleResult]

class AttendanceReport(BaseModel):
    student_id: UUID
    full_name: str
    student_code: str
    final_status: str
    confidence: Optional[float]
    final_engagement: Optional[str]
    engaged_count: int
    distracted_count: int
    sleeping_count: int
    phone_count: int