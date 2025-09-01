# #Define Backend v1
동의과학대학교 컴퓨터소프트웨어과 캡스톤디자인경진대회 백엔드 레포지토리  
자동차 입출차 관리 및 요금 계산 시스템 (FastAPI + SQLite)  

![Python](https://img.shields.io/badge/python-3.11-blue)

## 목차
- [설명](#설명)
- [설치](#설치)
- [사용법](#사용법)

## 설명
동의과학대학교 캡스톤디자인경진대회 #Define 팀에서 사용중인 백엔드 레포지토리입니다.  
FastAPI + SQLite3 를 사용하여 제작하였습니다.  

## 설치
```bash
git clone https://github.com/DITdefine/define_v1_backend.git
cd define_v1_backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 사용법
- 앱 실행, 기본 기능 안내
```bash
uvicorn main:app --port 8000 --host 0.0.0.0 --reload # 서버실행

http://127.0.0.1:8000/docs # 접속
```