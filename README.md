# Face Recognition Attendance - MTU

He thong diem danh sinh vien bang nhan dien khuon mat, gom:
- Backend Flask + SocketIO (web admin + mobile API)
- AI engine (InsightFace hoac YOLO + ResNet)
- MySQL (XAMPP phu hop cho local dev)
- Flutter mobile app (`mobile_flutter/`)

## 1) Yeu cau moi truong

- Python 3.10+ (khuyen nghi)
- MySQL 8.x (XAMPP)
- Pip packages trong `requirements.txt`

## 2) Cau truc du an

Xem chi tiet tai `docs/PROJECT_STRUCTURE.md`.

Thu muc chinh:
- `app.py`: Flask app factory
- `run_server.py`: entrypoint chay server
- `routes/`: API + web routes
- `services/`: business logic
- `core/`: AI core
- `db/`: schema + connection + seed
- `mobile_flutter/`: mobile app
- `scripts/`: script van hanh (init db)

## 3) Setup nhanh

### B1. Tao virtual environment va cai dependencies

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### B2. Cau hinh `.env`

Copy `.env.example` -> `.env` va cap nhat:
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- `AI_ENGINE` (`insightface` hoac `yolo_resnet`)
- Cac threshold can thiet

### B3. Khoi tao database

```bash
python scripts/init_db.py
```

## 4) Chay he thong

```bash
python run_server.py
```

Server mac dinh: `http://localhost:5000`

## 5) Mobile app

Flutter app nam o `mobile_flutter/`.
Chay:

```bash
cd mobile_flutter
flutter pub get
flutter run
```

## 6) Bao mat

- Khong commit file `.env`.
- Khong de token that trong source.
- Neu token da lo, rotate ngay (Telegram BotFather, JWT secret, DB password).

## 7) Docker (tuy chon)

Du an co san `Dockerfile` va `docker-compose.yml` cho moi truong dong goi.
