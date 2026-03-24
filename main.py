from fastapi import FastAPI
from database import engine, Base
from routers import auth, teachers, classes, students, sessions, attendance

app = FastAPI(title="AI Attendance System")

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(auth.router,       prefix="/auth",       tags=["Auth"])
app.include_router(teachers.router,   prefix="/teachers",   tags=["Teachers"])
app.include_router(classes.router,    prefix="/classes",    tags=["Classes"])
app.include_router(students.router,   prefix="/students",   tags=["Students"])
app.include_router(sessions.router,   prefix="/sessions",   tags=["Sessions"])
app.include_router(attendance.router, prefix="/attendance", tags=["Attendance"])

@app.get("/")
def root():
    return {"message": "Attendance backend is running"}