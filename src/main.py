from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm.session import Session
from sqlalchemy.sql.expression import text
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from api import user, travel_log, travel_review, profile, travel_stamp
import os

from database.connection import get_db

app = FastAPI()


# Add CORS middleware first, before including routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:3001",
        "https://localhost:3000",
        "https://localhost:3001",
        "https://frontend-psi-five-43.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router)
app.include_router(travel_log.router)
app.include_router(travel_review.router)
app.include_router(profile.router)
app.include_router(travel_stamp.router)

@app.get("/")
def read_root():
    return {"message": "GilTongmu!"}

# DB 연결 테스트용 - 추후 삭제
@app.get("/test-db")
def test_db(db: Session = Depends(get_db)):
    # 그냥 커넥션 테스트 쿼리
    db.execute(text("SELECT 1"))
    return {"db_connection": "ok"}





