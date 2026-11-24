import { useState } from "react";
import { Link } from "react-router";
import { traceApi } from "../../api/client";
import { BackLink, Button, EmptyState, ErrorNote } from "../../components/ui";
import { apiError, describeBrowser, formatDateTime } from "../../utils/format";

const INVISIBLE = /[​‌‍]/g;

export default function TracePage() {
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const invisibleCount = (text.match(INVISIBLE) || []).length;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);
    try {
      setResult(await traceApi.trace(text));
    } catch (err) {
      setError(apiError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl px-5 py-10 sm:py-14">
      <BackLink to="/tac-gia">Góc tác giả</BackLink>
      <h1 className="mt-6 font-serif text-[2.25rem] leading-tight tracking-tight">
        Truy vết nội dung bị sao chép
      </h1>
      <p className="mt-3 max-w-2xl leading-relaxed text-ink-soft">
        Mỗi lần độc giả mở một chương, ICeT gắn vào nội dung một dấu ẩn không nhìn thấy, riêng cho
        lần đọc đó. Thấy truyện của bạn bị đăng lại ở nơi khác? Dán đoạn văn vào đây để biết nó được
        lấy từ lần đọc nào.
      </p>

      <form onSubmit={handleSubmit} className="mt-8">
        <label htmlFor="leaked" className="mb-1.5 block text-sm font-medium text-ink">
          Đoạn văn nghi bị sao chép
        </label>
        <textarea
          id="leaked"
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={8}
          required
          placeholder="Dán đoạn văn bạn tìm thấy ở trang web khác…"
          className="w-full resize-y rounded-lg border border-mist bg-white px-4 py-3 font-serif leading-[1.8] text-ink focus:border-dusk focus:outline-none focus:ring-2 focus:ring-dusk/15"
        />
        <div className="mt-2 flex flex-wrap items-center justify-between gap-3">
          <p className="text-[0.8125rem] text-ink-soft">
            {text
              ? invisibleCount > 0
                ? `Phát hiện ${invisibleCount.toLocaleString("vi-VN")} ký tự vô hình trong đoạn văn.`
                : "Không thấy ký tự vô hình nào trong đoạn văn."
              : "Đoạn văn càng dài, khả năng còn dấu ẩn càng cao."}
          </p>
          <Button type="submit" disabled={!text.trim() || loading}>
            {loading ? "Đang truy vết…" : "Truy vết"}
          </Button>
        </div>
      </form>

      {error && (
        <div className="mt-6">
          <ErrorNote>{error}</ErrorNote>
        </div>
      )}

      {result && (
        <section className="mt-10" aria-live="polite">
          <h2 className="font-serif text-2xl">Kết quả</h2>
          <p className="mt-2 text-ink-soft">
            Tìm thấy {result.marks_found} dấu ẩn, thuộc {result.sessions_found} lần đọc.
          </p>

          {result.sessions_found === 0 ? (
            <div className="mt-6">
              <EmptyState title="Không có dấu ẩn hợp lệ">
                Đoạn văn có thể đã bị gõ lại thủ công, bị lọc bỏ ký tự vô hình, hoặc không được lấy từ
                ICeT.
              </EmptyState>
            </div>
          ) : (
            <ul className="mt-6 space-y-4">
              {result.matches.map((m) => (
                <li key={m.session_id} className="rounded-xl border border-rose/25 bg-white p-5">
                  <p className="text-sm text-ink-soft">Nội dung được lấy từ lần đọc của</p>
                  <p className="mt-1 font-serif text-2xl text-ink">
                    {m.reader_display_name}{" "}
                    <span className="font-sans text-base text-ink-soft">@{m.reader_username}</span>
                  </p>
                  <dl className="mt-4 grid gap-x-6 gap-y-3 text-sm sm:grid-cols-2">
                    <div>
                      <dt className="text-ink-soft">Chương đã đọc</dt>
                      <dd className="mt-0.5 text-ink">
                        <Link
                          to={`/tac-gia/truyen/${m.story_id}`}
                          className="hover:text-dusk hover:underline"
                        >
                          {m.story_title}, chương {m.chapter_number}: {m.chapter_title}
                        </Link>
                      </dd>
                    </div>
                    <div>
                      <dt className="text-ink-soft">Thời điểm mở chương</dt>
                      <dd className="mt-0.5 tabular-nums text-ink">{formatDateTime(m.read_at)}</dd>
                    </div>
                    <div>
                      <dt className="text-ink-soft">Địa chỉ IP</dt>
                      <dd className="mt-0.5 tabular-nums text-ink">{m.ip_address || "Không rõ"}</dd>
                    </div>
                    <div>
                      <dt className="text-ink-soft">Thiết bị</dt>
                      <dd className="mt-0.5 text-ink" title={m.user_agent || ""}>
                        {describeBrowser(m.user_agent)}
                      </dd>
                    </div>
                  </dl>
                  <p className="mt-4 text-[0.8125rem] text-ink-soft">Mã phiên đọc #{m.session_id}</p>
                </li>
              ))}
            </ul>
          )}

          {result.hidden_matches > 0 && (
            <p className="mt-4 text-sm text-ink-soft">
              {result.hidden_matches} lần đọc khác thuộc truyện của tác giả khác nên không hiển thị ở
              đây.
            </p>
          )}
        </section>
      )}
    </div>
  );
}
