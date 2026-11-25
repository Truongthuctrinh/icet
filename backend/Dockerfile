# Một image dùng chung cho API và worker (khác nhau ở lệnh chạy trong docker-compose.yml)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Cài thư viện trước, chép code sau: sửa code không phải cài lại thư viện (build nhanh hơn)
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Chạy bằng user thường, không dùng root
RUN useradd --create-home icet \
    && mkdir -p /app/media /models \
    && chown -R icet:icet /app/media /models
USER icet

EXPOSE 8000
# Cập nhật bảng DB rồi mới mở API
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2"]
