import { createRoot } from "react-dom/client";
import App from "./App.jsx";
import "./index.css";

// Không bọc StrictMode: ở chế độ dev, StrictMode chạy effect 2 lần
// -> mỗi lần mở chương sẽ tạo 2 dòng reading_sessions, làm rối dữ liệu demo.
createRoot(document.getElementById("root")).render(<App />);
