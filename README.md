# ICeT — Imagine Come True

Web đăng và đọc truyện chữ cho người viết nghiệp dư, tập trung vào **bảo vệ nội dung**:
chống sao chép, chống thu thập tự động (kể cả bot AI), truy vết người làm rò rỉ và phát hiện đạo văn
(cả chép nguyên văn lẫn viết lại).


## Công nghệ

| Phần | Công nghệ |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic |
| Cơ sở dữ liệu | PostgreSQL 17 + pgvector (chỉ mục HNSW) |
| Bộ nhớ đệm, hàng đợi | Redis 7, arq (worker chạy việc nền) |
| Phát hiện đạo văn | MinHash + LSH (tự cài bằng numpy), embedding đa ngôn ngữ `paraphrase-multilingual-MiniLM-L12-v2` (fastembed, ONNX, chạy bằng CPU) |
| Frontend | React 19, Vite, React Router, Tailwind CSS 4, Axios |
| Triển khai | Docker Compose: db, redis, api, worker, web (nginx) |

## Kiến trúc

```
Trình duyệt ──► web (nginx :8080) ──► /api ──► api (FastAPI) ──► db (PostgreSQL + pgvector)
                    │                              │    └────────► redis (rate limit, cấm IP, hàng đợi)
                    └── /media (ảnh, đọc thẳng)    │                    │
                                                   └── đưa việc ──► worker (arq: MinHash + embedding)
```

## Các lớp bảo vệ nội dung

1. **Trình duyệt:** chặn bôi đen, sao chép, chuột phải, in; nền chìm tên người đọc.
2. **API:** chương không bao giờ trả về nguyên bài. Người đọc phải mở phiên đọc để nhận vé đọc (30 phút),
   rồi tải từng lượt tối đa 10 đoạn. Rate limit bằng Redis cho mở chương, tải đoạn, đăng nhập,
   bình luận và tải ảnh.
3. **Watermark ẩn:** mỗi lượt đọc chèn ký tự vô hình (zero-width) mang mã phiên đọc kèm checksum.
   Văn bản bị dán ở nơi khác có thể truy ra tài khoản đã đọc (trang Truy vết).
4. **Phát hiện đạo văn:**
   - MinHash + LSH bắt chép nguyên văn hoặc sửa vài chữ.
   - Embedding bắt văn viết lại bằng chữ khác. Ngưỡng cosine 0,65 được đo trên tiếng Việt:
     đoạn viết lại ≥ 0,75, đoạn cùng chủ đề ≤ 0,53.
   - Bản viết trước là bản gốc. Chương có ≥ 15% số chữ bị trùng thì tạo cảnh báo; admin xác nhận
     thì chương vi phạm bị ẩn.
5. **Chặn bot:** chặn 22 bot AI theo User-Agent, có `robots.txt`, header `X-Robots-Tag: noai`.
   Bẫy honeypot cấm IP 30 phút. Header chống nhúng iframe.
6. **Ảnh tải lên:** kiểm tra định dạng thật bằng Pillow (không tin đuôi file), chặn bom giải nén,
   vẽ lại thành WebP và xoá EXIF (toạ độ GPS). Tên file ngẫu nhiên.

---

## Cách 1: Chạy trọn bộ bằng Docker (demo, chấm bài)

Cần: Docker Desktop (Windows bật WSL2) hoặc Docker Engine.

```bash
git clone <địa chỉ repo> icet && cd icet
cp .env.example .env            # rồi mở .env đổi mật khẩu DB và JWT_SECRET
docker compose --profile full up -d --build
```

- Lần đầu build mất vài phút. Worker tải model embedding (~220 MB) một lần, lưu trong volume `models`.
- Mở **http://localhost:8080**

Tạo dữ liệu mẫu (chỉ chạy khi DB còn trống):

```bash
docker compose exec api python -m app.scripts.seed_demo
```

| Tài khoản | Mật khẩu | Vai trò |
|---|---|---|
| `admin` | `admin12345` (đổi bằng `SEED_ADMIN_PASSWORD`) | Quản trị |
| `lamthu` | `matkhau123` | Tác giả "Hồ ký ức" (bản gốc) |
| `tuanvu` | `matkhau123` | Tác giả "Gió mùa đông bắc" (bản gốc) |
| `daovan` | `matkhau123` | Tác giả "Bản sao": chép 1 đoạn nguyên văn và viết lại 3 đoạn |

Đăng nhập `admin` hoặc `lamthu`, vào **Góc tác giả → Đạo văn** để xem 2 cảnh báo mẫu
(nhãn đỏ "Trùng nguyên văn", nhãn tím "Trùng ý").

Các lệnh thường dùng:

```bash
docker compose --profile full ps            # xem trạng thái
docker compose --profile full logs -f worker # xem log worker
docker compose --profile full down           # tắt (dữ liệu vẫn giữ trong volume)
```

## Cách 2: Chạy để phát triển (sửa code thấy ngay)

Cần: Python 3.12, Node 22, Docker (chỉ để chạy PostgreSQL và Redis).

```bash
cp .env.example .env
docker compose up -d                      # chỉ bật db + redis

cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload             # terminal 1: API ở :8000

arq app.worker.WorkerSettings             # terminal 2: worker (tuỳ chọn, cần cho so sánh theo ý)

cd ../frontend && npm install && npm run dev   # terminal 3: giao diện ở :5173
```

Không bật worker thì web vẫn chạy bình thường; kiểm tra đạo văn chạy ngay trong API và chỉ so nguyên văn.

## Kiểm thử

```bash
cd backend
pip install -r requirements-dev.txt
pytest -q                     # dùng SQLite + Redis giả, không cần Docker
```

Muốn chạy test trên PostgreSQL thật (kiểm tra truy vấn pgvector), dùng một DB **riêng cho test**
(test xoá sạch bảng):

```bash
TEST_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/icet_test pytest -q
```

Hiệu chỉnh ngưỡng embedding:

```bash
python -m app.scripts.calibrate_embedding
```

## Cấu trúc thư mục

```
icet/
├── docker-compose.yml      db, redis (luôn bật) + api, worker, web (profile "full")
├── .env.example            mẫu cấu hình
├── backend/
│   ├── Dockerfile          dùng chung cho api và worker
│   ├── alembic/            migration cơ sở dữ liệu
│   ├── app/
│   │   ├── core/           cấu hình, bảo mật, rate limit, watermark, minhash, embedder, ảnh, shield
│   │   ├── models/         bảng SQLAlchemy
│   │   ├── schemas/        dữ liệu vào/ra (Pydantic)
│   │   ├── services/       nghiệp vụ (đọc, đạo văn, so nghĩa, cộng đồng, quản trị, ảnh)
│   │   ├── routers/        endpoint API
│   │   ├── scripts/        seed_demo, calibrate_embedding
│   │   ├── worker.py       worker arq
│   │   └── main.py
│   └── tests/
└── frontend/
    ├── Dockerfile, nginx.conf
    └── src/ (api, components, context, pages, utils)
```
