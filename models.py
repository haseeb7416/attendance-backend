from sqlalchemy import Column, String, Float, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from database import Base
import uuid
import datetime

class Teacher(Base):
    __tablename__ = "teachers"
    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name     = Column(String(150), nullable=False)
    email         = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at    = Column(DateTime, default=datetime.datetime.utcnow)

class Class(Base):
    __tablename__ = "classes"
    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name        = Column(String(100), nullable=False)
    course_code = Column(String(20), nullable=False)
    teacher_id  = Column(UUID(as_uuid=True), ForeignKey("teachers.id"))

class Student(Base):
    __tablename__ = "students"
    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name      = Column(String(150), nullable=False)
    student_code   = Column(String(30), unique=True, nullable=False)
    class_id       = Column(UUID(as_uuid=True), ForeignKey("classes.id"))
    face_embedding = Column(String, nullable=True)
    photo_url      = Column(String(500), nullable=True)
    created_at     = Column(DateTime, default=datetime.datetime.utcnow)

class Session(Base):
    __tablename__ = "sessions"
    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_id   = Column(UUID(as_uuid=True), ForeignKey("classes.id"))
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("teachers.id"))
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    ended_at   = Column(DateTime, nullable=True)
    status     = Column(String(20), default="active")

class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id       = Column(UUID(as_uuid=True), ForeignKey("sessions.id"))
    student_id       = Column(UUID(as_uuid=True), ForeignKey("students.id"))
    final_status     = Column(String(20))
    confidence       = Column(Float, nullable=True)
    engaged_count    = Column(Integer, default=0)
    distracted_count = Column(Integer, default=0)
    sleeping_count   = Column(Integer, default=0)
    phone_count      = Column(Integer, default=0)
    final_engagement = Column(String(30), nullable=True)
    recorded_at      = Column(DateTime, default=datetime.datetime.utcnow)