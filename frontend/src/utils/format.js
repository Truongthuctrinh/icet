export const STATUS_LABELS = {
  ongoing: "Đang ra",
  completed: "Hoàn thành",
  paused: "Tạm dừng",
};

export function formatDate(iso) {
  return new Date(iso).toLocaleDateString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

export function timeAgo(iso) {
  const seconds = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (seconds < 60) return "vừa xong";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes} phút trước`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} giờ trước`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days} ngày trước`;
  return formatDate(iso);
}

export function countWords(text) {
  const trimmed = text.trim();
  return trimmed ? trimmed.split(/\s+/).length : 0;
}

const FIELD_NAMES = {
  username: "Tên đăng nhập",
  email: "Email",
  password: "Mật khẩu",
  display_name: "Tên hiển thị",
  title: "Tiêu đề",
  content: "Nội dung",
  description: "Giới thiệu",
};

function translateValidation(item) {
  const field = FIELD_NAMES[item.loc?.[item.loc.length - 1]] || "Dữ liệu";
  switch (item.type) {
    case "string_too_short":
      return `${field} cần ít nhất ${item.ctx?.min_length} ký tự.`;
    case "string_too_long":
      return `${field} tối đa ${item.ctx?.max_length} ký tự.`;
    case "string_pattern_mismatch":
      return `${field} chỉ gồm chữ không dấu, số và dấu gạch dưới.`;
    case "value_error":
      return field === "Email" ? "Email không đúng định dạng." : `${field} không hợp lệ.`;
    case "missing":
      return `Thiếu ${field.toLowerCase()}.`;
    default:
      return `${field} không hợp lệ.`;
  }
}

/** Chuyển lỗi từ API thành câu tiếng Việt hiển thị cho người dùng. */
export function apiError(error, fallback = "Có lỗi xảy ra. Thử lại sau ít phút.") {
  if (!error?.response) {
    return "Không kết nối được máy chủ. Kiểm tra backend (uvicorn) đã chạy chưa.";
  }
  const detail = error.response.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map(translateValidation).join(" ");
  return fallback;
}

export function formatDateTime(iso) {
  return new Date(iso).toLocaleString("vi-VN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

/** Rút gọn user agent thành "Trình duyệt trên Hệ điều hành". */
export function describeBrowser(ua) {
  if (!ua) return "Không rõ";
  const browser = /Edg\//.test(ua)
    ? "Edge"
    : /OPR\//.test(ua)
      ? "Opera"
      : /Chrome\//.test(ua)
        ? "Chrome"
        : /Firefox\//.test(ua)
          ? "Firefox"
          : /Safari\//.test(ua)
            ? "Safari"
            : /curl|python|httpx|wget|scrapy/i.test(ua)
              ? "Công cụ tự động"
              : "Trình duyệt khác";
  const os = /Windows/.test(ua)
    ? "Windows"
    : /Android/.test(ua)
      ? "Android"
      : /iPhone|iPad/.test(ua)
        ? "iOS"
        : /Mac OS/.test(ua)
          ? "macOS"
          : /Linux/.test(ua)
            ? "Linux"
            : "";
  return os ? `${browser} trên ${os}` : browser;
}
