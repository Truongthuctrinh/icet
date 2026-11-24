"""Chạy app thật với SQLite (file tạm) + Redis giả (fakeredis). Không cần Docker."""
import os

os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-pytest-only-0123456789")
os.environ.setdefault("TRUSTED_PROXIES", "127.0.0.1,testclient")  # TestClient đóng vai proxy

import fakeredis
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.core.rate_limit as rate_limit_module
import app.core.shield as shield_module
import app.services.admin_service as admin_service_module
import app.main as main_module
import app.routers.auth as auth_router_module
import app.services.plagiarism_service as plagiarism_module
from app.core.database import Base, get_db


@pytest.fixture()
def client(tmp_path):
    # Mỗi test 1 file SQLite tạm, mỗi phiên DB có kết nối RIÊNG (giống PostgreSQL thật).
    # Không dùng SQLite-trong-RAM + 1 kết nối chung: FastAPI chạy request ở nhiều luồng,
    # 2 luồng dùng chung 1 kết nối sẽ thỉnh thoảng đọc sai dữ liệu (lỗi chập chờn).
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}",
        connect_args={"check_same_thread": False, "timeout": 30},
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    fake = fakeredis.FakeRedis(decode_responses=True)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    # Thay DB + Redis thật bằng bản giả cho mọi chỗ đang dùng
    main_module.SessionLocal = TestSession
    plagiarism_module.SessionLocal = TestSession
    for module in (rate_limit_module, auth_router_module, main_module, shield_module, admin_service_module):
        module.redis_client = fake
    main_module.app.dependency_overrides[get_db] = override_get_db

    with TestClient(main_module.app) as c:
        c.fake_redis = fake
        yield c
    main_module.app.dependency_overrides.clear()
    engine.dispose()


def register_and_login(client, username, display_name=None):
    client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": f"{username}@test.vn",
            "password": "matkhau123",
            "display_name": display_name or username.capitalize(),
        },
    )
    token = client.post(
        "/api/auth/login", data={"username": username, "password": "matkhau123"}
    ).json()["access_token"]
    client.fake_redis.flushall()  # không để bộ đếm đăng nhập ảnh hưởng test khác
    return {"Authorization": f"Bearer {token}"}


def make_admin(client, username="quantri"):
    headers = register_and_login(client, username)
    import app.main as m
    from app.models import User

    db = m.SessionLocal()
    db.query(User).filter_by(username=username).update({"role": "admin"})
    db.commit()
    db.close()
    return headers
