from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .orm import Base
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# engine 객체: 데이터베이스 연결 정보를 설정하고 관리
# echo=True 사용되는 sql 출력
engine = create_engine(DATABASE_URL, echo=True)
SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)


#Base.metadata.drop_all(bind=engine)
#Base.metadata.create_all(bind=engine)

# sessionmaker를 통해 생성되는 session 객체: 데이터베이스와 통신하며 쿼리 실행, 트랜잭션 관리
# 파이썬 제너레이터
def get_db():
    session = SessionFactory()
    try:
        yield session          # ← 여기까지 모든 DB 작업 수행
        session.commit()       # 성공 경로: 커밋
    except Exception:
        session.rollback()     # 실패 경로: 롤백 (응답 검증 실패 포함)
        raise
    finally:
        session.close()
