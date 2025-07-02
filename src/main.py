from fastapi import FastAPI, Depends
from sqlalchemy.orm.session import Session
from sqlalchemy.sql.expression import text
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect
from src.api.user import router as user_router

from src.database.connection import get_db

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Hello": "World"}

# DB 연결 테스트용 - 추후 삭제
@app.get("/test-db")
def test_db(db: Session = Depends(get_db)):
    # 그냥 커넥션 테스트 쿼리
    db.execute(text("SELECT 1"))
    return {"db_connection": "ok"}


app.include_router(user_router)

