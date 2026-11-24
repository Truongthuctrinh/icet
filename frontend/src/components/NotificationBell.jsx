import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router";
import { notificationApi } from "../api/client";

const POLL_MS = 60_000; // thông báo lưu trong DB: hỏi lại mỗi phút + mỗi lần chuyển trang

export default function NotificationBell() {
  const [count, setCount] = useState(0);
  const location = useLocation();

  useEffect(() => {
    let alive = true;
    const refresh = () =>
      notificationApi.unreadCount().then((c) => alive && setCount(c)).catch(() => {});
    refresh();
    const timer = setInterval(refresh, POLL_MS);
    window.addEventListener("icet:notifications-changed", refresh);
    return () => {
      alive = false;
      clearInterval(timer);
      window.removeEventListener("icet:notifications-changed", refresh);
    };
  }, [location.pathname]);

  return (
    <Link
      to="/thong-bao"
      className="relative inline-flex h-9 w-9 items-center justify-center rounded-full text-ink-soft hover:bg-mist/60 hover:text-ink"
      aria-label={count ? `Thông báo, ${count} chưa đọc` : "Thông báo"}
    >
      <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
        <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
      </svg>
      {count > 0 && (
        <span className="absolute -right-0.5 -top-0.5 min-w-[1.15rem] rounded-full bg-rose px-1 text-center text-[0.65rem] font-semibold leading-[1.15rem] text-white tabular-nums">
          {count > 99 ? "99+" : count}
        </span>
      )}
    </Link>
  );
}
