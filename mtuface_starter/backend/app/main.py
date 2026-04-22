from fastapi import FastAPI

from app.api.v1.checkin import router as checkin_router
from app.api.v1.register_face import router as register_router
from app.db.session import Base, engine

app = FastAPI(title="MTUface API", version="1.0.0")

# MVP bootstrap: create tables automatically.
Base.metadata.create_all(bind=engine)

app.include_router(register_router, prefix="/api/v1", tags=["face"])
app.include_router(checkin_router, prefix="/api/v1", tags=["attendance"])


@app.get("/health")
def health():
    return {"status": "ok"}
