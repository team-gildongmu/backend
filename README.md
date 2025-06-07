## 🚀 설치 방법

1. 가상환경 생성 및 활성화
```bash
# 가상환경 생성 (원하는 가상환경 폴더명으로 생성)
python3.10 -m venv [가상환경폴더명]

cd [가상환경폴더명]

# 가상환경 활성화
source bin/activate #mac
Scripts\activate.bat #window
```

2. 필요한 패키지 설치
```bash
pip install -r requirements.txt
```

3. 서버 실행
```bash
uvicorn main:app --reload
```