# ICeT frontend (React + Vite + Tailwind v4)

## Chạy khi dev
1. Backend đang chạy ở http://localhost:8000 (uvicorn) và `docker compose up -d` đã bật DB.
2. Trong thư mục `frontend`:
   ```bash
   npm install      # chỉ cần lần đầu
   npm run dev
   ```
3. Mở http://localhost:5173

Vite chuyển tiếp mọi request `/api/...` sang FastAPI (xem `vite.config.js`), nên không cần cấu hình CORS khi dev.

## Cấu trúc
- `src/api/client.js`: axios + toàn bộ hàm gọi API
- `src/context/AuthContext.jsx`: trạng thái đăng nhập
- `src/components/`: Layout (header/footer), RequireAuth, ui (Button, Field, Badge…)
- `src/pages/`: trang người đọc (Home, Story, Reader, Login, Register)
- `src/pages/author/`: Góc tác giả (Dashboard, StoryForm, ManageStory, ChapterEditor)
