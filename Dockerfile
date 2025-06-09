# 베이스 이미지
FROM python:3.10-slim

# 작업 디렉토리 생성
WORKDIR /app

# 필요한 파일 복사
COPY ./requirements.txt /app/requirements.txt

# 패키지 설치
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# 소스 코드 복사
COPY ./src /app/src

# 포트 오픈
EXPOSE 8000

# Uvicorn 서버 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
