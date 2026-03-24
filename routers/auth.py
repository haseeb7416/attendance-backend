from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import Teacher
from schemas import LoginRequest, TokenOut, TeacherOut
from passlib.context import CryptContext
from jose import jwt
from dotenv import load_dotenv
import os
import datetime

load_dotenv()
router = APIRouter()
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

def make_token(teacher_id: str):
    payload = {
        "sub": teacher_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    }
    return jwt.encode(payload, os.getenv("SECRET_KEY"), algorithm=os.getenv("ALGORITHM"))


@router.post("/login", response_model=TokenOut)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):

    # Find teacher by email
    result = await db.execute(select(Teacher).where(Teacher.email == data.email))
    teacher = result.scalar_one_or_none()

    # Check email and password
    if not teacher or not pwd.verify(data.password, teacher.password_hash):
        raise HTTPException(status_code=401, detail="Wrong email or password")

    # Make token and return
    token = make_token(str(teacher.id))
    return {"access_token": token}


@router.get("/me", response_model=TeacherOut)
async def get_me(token: str, db: AsyncSession = Depends(get_db)):

    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")])
        teacher_id = payload.get("sub")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(Teacher).where(Teacher.id == teacher_id))
    teacher = result.scalar_one_or_none()

    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    return teacher