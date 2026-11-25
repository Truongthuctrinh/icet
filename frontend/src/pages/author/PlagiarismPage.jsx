import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router";
import { plagiarismApi } from "../../api/client";
import { BackLink, Button, EmptyState, ErrorNote, PageSpinner } from "../../components/ui";
import { useAuth } from "../../context/AuthContext";
import { apiError, formatDateTime } from "../../utils/format";

const STATUS = {
  pending: { label: "Chờ xem xét", className: "bg-marigold/15 text-ink" },
  confirmed: { label: "Đã xác nhận, chương bị ẩn", className: "bg-rose/10 text-rose" },
  dismissed: { label: "Đã bỏ qua", className: "bg-mist text-ink-soft" },
};

const FILTERS = [
  { value: "", label: "Tất cả" },
  { value: "pending", label: "Chờ xem xét" },
  { value: "confirmed", label: "Đã xác nhận" },
  { value: "dismissed", label: "Đã bỏ qua" },
];

// Nguyên văn: MinHash bắt được chuỗi chữ giống nhau. Viết lại: embedding thấy cùng ý dù khác chữ.
function MatchKind({ method }) {
  const semantic = method === "semantic";
  return (
    <span
      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
        semantic ? "bg-dusk/10 text-dusk" : "bg-rose/10 text-rose"
      }`}
      title={semantic ? "Câu chữ khác nhưng cùng nội dung, có thể đã bị viết lại" : "Câu chữ gần như giống hệt"}
    >
      {semantic ? "Trùng ý (viết lại)" : "Trùng nguyên văn"}
    </span>
  );
}

function headline(report) {
  const s = report.suspect;
  const src = report.source;
  if (report.my_role === "source")
    return `Truyện "${src.story_title}" của bạn có thể đã bị sao chép`;
  if (report.my_role === "suspect")
    return `Chương "${s.chapter_title}" của bạn trùng với truyện của tác giả khác`;
  return `${s.author_display_name} nghi sao chép từ ${src.author_display_name}`;
}

function ChapterCard({ title, chapter }) {
  return (
    <div className="rounded-lg border border-mist bg-paper/60 px-4 py-3">
      <p className="text-[0.8125rem] text-ink-soft">{title}</p>
      <p className="mt-1 font-serif text-lg leading-snug text-ink">
        {chapter.story_title}, chương {chapter.chapter_number}
      </p>
      <p className="text-sm text-ink">{chapter.chapter_title}</p>
      <p className="mt-2 text-[0.8125rem] text-ink-soft">
        {chapter.author_display_name} (@{chapter.author_username}), đăng {formatDateTime(chapter.created_at)}
      </p>
    </div>
  );
}

function ReportCard({ report, isAdmin, onStatus, busy }) {
  const [open, setOpen] = useState(false);
  const percent = Math.round(report.score * 100);
  const status = STATUS[report.status];

  return (
    <li className="rounded-xl border border-mist bg-white">
      <div className="flex flex-wrap items-start gap-5 p-5">
        <div className="w-24 shrink-0 text-center">
          <p className="font-serif text-4xl leading-none text-rose tabular-nums">{percent}%</p>
          <p className="mt-1.5 text-[0.75rem] leading-tight text-ink-soft">nội dung chương bị trùng</p>
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2.5">
            <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${status.className}`}>
              {status.label}
            </span>
            <span className="text-[0.8125rem] text-ink-soft">
              phát hiện {formatDateTime(report.created_at)}
            </span>
          </div>
          <h2 className="mt-2 font-serif text-xl leading-snug">{headline(report)}</h2>
          <p className="mt-1 text-sm text-ink-soft">
            {report.matched_count} đoạn văn gần như giống hệt đoạn trong bản đăng trước.
          </p>

          {report.watermark_sessions.length > 0 && (
            <p className="mt-3 rounded-lg border border-rose/25 bg-rose/5 px-3 py-2 text-sm text-ink">
              Nội dung chương nghi sao chép còn mang dấu ẩn của phiên đọc{" "}
              {report.watermark_sessions.map((id) => `#${id}`).join(", ")}: văn bản được lấy trực tiếp
              từ trang đọc của ICeT.
              {(isAdmin || report.my_role === "source") && (
                <>
                  {" "}
                  <Link to="/tac-gia/truy-vet" className="font-medium text-dusk hover:underline">
                    Truy vết người đã lấy
                  </Link>
                </>
              )}
            </p>
          )}
        </div>
      </div>

      <div className="grid gap-3 border-t border-mist px-5 py-4 sm:grid-cols-2">
        <ChapterCard title="Bản đăng trước (nguồn)" chapter={report.source} />
        <ChapterCard title="Bản đăng sau (nghi sao chép)" chapter={report.suspect} />
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-mist px-5 py-3">
        <Button variant="ghost" size="sm" onClick={() => setOpen(!open)} aria-expanded={open}>
          {open ? "Ẩn các đoạn trùng" : `So sánh ${report.matches.length} đoạn trùng`}
        </Button>
        {isAdmin && (
          <div className="flex flex-wrap gap-2">
            {report.status !== "confirmed" && (
              <Button size="sm" variant="danger" disabled={busy} onClick={() => onStatus(report, "confirmed")}>
                Xác nhận và ẩn chương
              </Button>
            )}
            {report.status !== "dismissed" && (
              <Button size="sm" variant="secondary" disabled={busy} onClick={() => onStatus(report, "dismissed")}>
                Bỏ qua
              </Button>
            )}
            {report.status !== "pending" && (
              <Button size="sm" variant="ghost" disabled={busy} onClick={() => onStatus(report, "pending")}>
                Đưa về chờ xem xét
              </Button>
            )}
          </div>
        )}
      </div>

      {open && (
        <ol className="space-y-4 border-t border-mist px-5 py-5">
          {report.matches.map((m) => (
            <li key={`${m.suspect_index}-${m.source_index}`}>
              <p className="mb-2 flex flex-wrap items-center gap-x-2 gap-y-1 text-[0.8125rem] text-ink-soft">
                <MatchKind method={m.method} />
                <span>
                  {m.method === "semantic" ? "Giống nghĩa" : "Trùng chữ"} {Math.round(m.similarity * 100)}%: đoạn{" "}
                  {m.source_index + 1} bản gốc, đoạn {m.suspect_index + 1} bản nghi sao chép
                </span>
              </p>
              <div className="grid gap-3 sm:grid-cols-2">
                <p className="rounded-lg bg-paper px-4 py-3 font-serif text-[0.975rem] leading-[1.75] text-ink">
                  {m.source_text}
                </p>
                <p className="rounded-lg bg-rose/5 px-4 py-3 font-serif text-[0.975rem] leading-[1.75] text-ink">
                  {m.suspect_text}
                </p>
              </div>
            </li>
          ))}
        </ol>
      )}
    </li>
  );
}

export default function PlagiarismPage() {
  const { user } = useAuth();
  const isAdmin = user.role === "admin";
  const [filter, setFilter] = useState("");
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);
  const [reindexInfo, setReindexInfo] = useState("");

  const load = useCallback(() => {
    setLoading(true);
    setError("");
    plagiarismApi
      .reports(filter)
      .then(setReports)
      .catch((err) => setError(apiError(err)))
      .finally(() => setLoading(false));
  }, [filter]);

  useEffect(load, [load]);

  const handleStatus = async (report, status) => {
    setBusyId(report.id);
    try {
      const updated = await plagiarismApi.setStatus(report.id, status);
      setReports((prev) =>
        filter && filter !== status
          ? prev.filter((r) => r.id !== report.id)
          : prev.map((r) => (r.id === report.id ? updated : r))
      );
    } catch (err) {
      setError(apiError(err));
    } finally {
      setBusyId(null);
    }
  };

  const handleReindex = async () => {
    setReindexInfo("Đang quét lại toàn bộ chương…");
    try {
      const res = await plagiarismApi.reindex();
      setReindexInfo(
        res.queued
          ? `Đã giao ${res.chapters} chương cho worker quét lại (so cả nguyên văn lẫn ý). Tải lại trang sau ít phút để xem kết quả.`
          : `Đã quét ${res.chapters} chương (chỉ so nguyên văn vì worker chưa chạy), ${res.reports} cảnh báo được tạo hoặc cập nhật.`
      );
      load();
    } catch (err) {
      setReindexInfo("");
      setError(apiError(err));
    }
  };

  return (
    <div className="mx-auto max-w-4xl px-5 py-10 sm:py-14">
      <BackLink to="/tac-gia">Góc tác giả</BackLink>
      <div className="mt-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-serif text-[2.25rem] leading-tight tracking-tight">Cảnh báo đạo văn</h1>
          <p className="mt-2 max-w-2xl leading-relaxed text-ink-soft">
            {isAdmin
              ? "Mọi chương mới được so với toàn bộ kho truyện. Xem từng cặp đoạn trùng rồi xác nhận hoặc bỏ qua cảnh báo."
              : "Mỗi khi một chương được lưu, ICeT so nó với toàn bộ kho truyện. Cảnh báo liên quan đến truyện của bạn hiện ở đây."}
          </p>
        </div>
        {isAdmin && (
          <Button variant="secondary" size="sm" onClick={handleReindex}>
            Quét lại toàn bộ chương
          </Button>
        )}
      </div>
      {reindexInfo && <p className="mt-3 text-sm text-ink-soft">{reindexInfo}</p>}

      <div className="mt-8 flex flex-wrap gap-2" role="group" aria-label="Lọc theo trạng thái">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            type="button"
            onClick={() => setFilter(f.value)}
            aria-pressed={filter === f.value}
            className={`rounded-full px-3.5 py-1.5 text-sm transition-colors ${
              filter === f.value ? "bg-ink text-white" : "border border-mist bg-white text-ink-soft hover:text-ink"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {error && (
        <div className="mt-6">
          <ErrorNote>{error}</ErrorNote>
        </div>
      )}

      {loading ? (
        <PageSpinner />
      ) : reports.length === 0 ? (
        <div className="mt-6">
          <EmptyState title="Không có cảnh báo nào">
            {filter
              ? "Không có cảnh báo ở trạng thái này."
              : "Chưa phát hiện chương nào trùng nội dung với truyện của bạn."}
          </EmptyState>
        </div>
      ) : (
        <ul className="mt-6 space-y-5">
          {reports.map((r) => (
            <ReportCard
              key={r.id}
              report={r}
              isAdmin={isAdmin}
              onStatus={handleStatus}
              busy={busyId === r.id}
            />
          ))}
        </ul>
      )}
    </div>
  );
}
