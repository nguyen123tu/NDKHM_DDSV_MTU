# Project Structure (Refactor Guide)

Muc tieu: giu code hien tai chay on dinh va sap xep theo module de de mo rong.

## Thu muc chinh

- `app.py`: Flask app factory + register blueprint + socket.
- `run_server.py`: entrypoint chay server development.
- `config.py`: cau hinh ung dung, doc tu `.env`.
- `routes/`: Flask blueprints (web admin + mobile API).
- `services/`: business logic va xu ly nghiep vu.
- `core/`: AI engines, detector, embedder, matcher, camera manager.
- `db/`: ket noi DB, schema va seed.
- `templates/`: giao dien web admin.
- `static/`: JS/CSS/frontend assets.
- `database/`: dataset anh huan luyen va uploads (du lieu nhay cam).
- `models/`: file model va embeddings.
- `mobile_flutter/`: ung dung mobile Flutter.
- `scripts/`: script van hanh (init db, migration, batch jobs).
- `docs/`: tai lieu kien truc, setup, API.

## Luong du lieu chinh

1. Mobile/web gui yeu cau diem danh.
2. `routes/` validate input, goi `services/attendance_service.py`.
3. `core/engine.py` + `core/matcher.py` xu ly nhan dien.
4. `db/connection.py` ghi log diem danh + metadata.
5. Anh bang chung luu vao object path trong `database/` (MVP) hoac object storage.

## Huong nang cap tiep theo

- Tach `api/mobile` va `web/admin` thanh 2 package rieng.
- Dua xu ly AI sang service rieng (FastAPI) khi scale lon.
- Chuyen luu tru anh bang chung sang MinIO/S3 + signed URL.
