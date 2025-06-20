from fastapi import FastAPI, Depends
from sqlalchemy.orm.session import Session
from sqlalchemy.sql.expression import text

from database.connection import get_db

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

# DB 연결 테스트용 - 추후 삭제
@app.get("/test-db")
def test_db(db: Session = Depends(get_db)):
    # 그냥 커넥션 테스트 쿼리
    db.execute(text("SELECT 1"))
    return {"db_connection": "ok"}