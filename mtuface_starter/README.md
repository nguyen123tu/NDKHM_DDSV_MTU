# MTUface Starter Kit

Bo starter kit FastAPI + InsightFace + PostgreSQL de ban bat dau nhanh cho bai toan diem danh khuon mat.

## 1) Chay nhanh bang Docker

```bash
cd mtuface_starter
docker compose up --build
```

API docs: `http://localhost:8000/docs`

## 2) Chay local khong Docker

```bash
cd mtuface_starter/backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
set DATABASE_URL=sqlite:///./mtuface.db
uvicorn app.main:app --reload --port 8000
```

## 3) API co san

- `POST /api/v1/register-face`
  - form-data: `student_code`, `full_name`, `image`
- `POST /api/v1/check-in`
  - form-data: `image`

## 4) Thu tu test

1. Goi `register-face` 2-3 lan cho moi sinh vien (nhieu goc mat).
2. Goi `check-in` bang anh moi.
3. Kiem tra ket qua `success`, `confidence`, `student_code`.

## 5) Notes quan trong

- Threshold mac dinh: `0.45` (`FACE_THRESHOLD`).
- MVP luu embedding dang JSON de don gian; production nen chuyen `pgvector`.
- InsightFace lan dau init co the cham do load model.
