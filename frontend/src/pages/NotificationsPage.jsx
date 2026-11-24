import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { notificationApi } from "../api/client";
import { Button, EmptyState, ErrorNote, PageSpinner } from "../components/ui";
import { apiError, timeAgo } from "../utils/format";

const KIND_LABEL = {
  new_chapter: "Chương mới",
  comment: "Bình luận",
  reply: "Trả lời",
  rating: "Đánh giá",
  plagiarism_source: "Đạo văn",
  plagiarism_suspect: "Đạo văn",
  plagiarism_confirmed: "Đạo văn",
};

export default function NotificationsPage() {
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    notificationApi
      .list()
      .then(setItems)
      .catch((err) => setError(apiError(err)))
      .finally(() => setLoading(false));
  }, []);

  const changed = () => window.dispatchEvent(new Event("icet:notifications-changed"));

  const open = async (n) => {
    if (!n.is_read) {
      await notificationApi.read(n.id).catch(() => {});
      changed();
    }
    if (n.link) navigate(n.link);
    else setItems((prev) => prev.map((x) => (x.id === n.id ? { ...x, is_read: true } : x)));
  };

  const readAll = async () => {
    await notificationApi.readAll();
    setItems((prev) => prev.map((x) => ({ ...x, is_read: true })));
    changed();
  };

  const unread = items.filter((n) => !n.is_read).length;

  return (
    <div className="mx-auto max-w-2xl px-5 py-10 sm:py-14">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-serif text-4xl tracking-tight">Thông báo</h1>
          <p className="mt-2 text-ink-soft">{unread ? `${unread} thông báo chưa đọc.` : "Bạn đã xem hết thông báo."}</p>
        </div>
        {unread > 0 && (
          <Button variant="secondary" size="sm" onClick={readAll}>
            Đánh dấu tất cả đã đọc
          </Button>
        )}
      </div>

      {error && <div className="mt-6"><ErrorNote>{error}</ErrorNote></div>}

      {loading ? (
        <PageSpinner />
      ) : items.length === 0 ? (
        <div className="mt-8">
          <EmptyState title="Chưa có thông báo" action={<Button to="/">Tìm truyện để theo dõi</Button>}>
            Theo dõi truyện để được báo khi có chương mới. Bình luận và đánh giá cho truyện của bạn cũng hiện ở đây.
          </EmptyState>
        </div>
      ) : (
        <ul className="mt-8 divide-y divide-mist rounded-xl border border-mist bg-white">
          {items.map((n) => (
            <li key={n.id}>
              <button
                type="button"
                onClick={() => open(n)}
                className={`flex w-full items-start gap-4 px-5 py-4 text-left hover:bg-paper ${n.is_read ? "" : "bg-dusk/[0.03]"}`}
              >
                <span
                  className={`mt-2 h-2 w-2 shrink-0 rounded-full ${n.is_read ? "bg-transparent" : "bg-dusk"}`}
                  aria-label={n.is_read ? undefined : "Chưa đọc"}
                />
                <span className="min-w-0 flex-1">
                  <span className="text-[0.75rem] font-medium text-dusk">{KIND_LABEL[n.kind] || "Thông báo"}</span>
                  <span className={`mt-0.5 block leading-snug ${n.is_read ? "text-ink-soft" : "text-ink"}`}>{n.message}</span>
                  <span className="mt-1 block text-[0.8125rem] text-ink-soft">{timeAgo(n.created_at)}</span>
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
