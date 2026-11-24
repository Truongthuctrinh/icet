import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useParams } from "react-router";
import { readingApi } from "../api/client";
import CommentsSection from "../components/CommentsSection";
import { BackLink, Button, ErrorNote, PageSpinner, Spinner } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { apiError } from "../utils/format";

const BATCH_SIZE = 8; // số đoạn mỗi lần tải (backend cho tối đa 10)
const BLOCKED_KEYS = ["c", "x", "a", "s", "p", "u"]; // copy, cut, select all, save, print, view source

/** Watermark hiển thị: tên người đọc in mờ chìm dưới nội dung -> ảnh chụp màn hình cũng mang tên họ. */
function buildWatermark(username) {
  const svg = `<svg xmlns='http://www.w3.org/2000/svg' width='280' height='170'><text x='40' y='100' transform='rotate(-22 140 85)' font-family='sans-serif' font-size='15' fill='#1e2440' fill-opacity='0.07'>@${username}</text></svg>`;
  return `url("data:image/svg+xml,${encodeURIComponent(svg)}")`;
}

export default function ReaderPage() {
  const { storyId, chapterId } = useParams();
  const { user } = useAuth();
  const location = useLocation();
  const jumpToComments = location.hash === "#binh-luan"; // đến từ thông báo bình luận

  const [meta, setMeta] = useState(null); // thông tin chương từ POST /session
  const [paragraphs, setParagraphs] = useState([]);
  const [phase, setPhase] = useState("opening"); // opening | ready | failed
  const [error, setError] = useState("");
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [scrollRatio, setScrollRatio] = useState(0);
  const [notice, setNotice] = useState("");
  const [rateLimited, setRateLimited] = useState(false);

  // Dùng ref để các hàm bất đồng bộ luôn đọc được giá trị mới nhất
  const readTokenRef = useRef(null);
  const nextStartRef = useRef(0);
  const hasMoreRef = useRef(true);
  const loadingRef = useRef(false);
  const rateLimitedRef = useRef(false); // bị 429 -> ngừng tự tải cho tới khi người đọc bấm "Tải tiếp"
  const sentinelRef = useRef(null);
  const noticeTimerRef = useRef(null);

  const openSession = useCallback(async () => {
    const data = await readingApi.openSession(storyId, chapterId);
    readTokenRef.current = data.session_token;
    setMeta(data);
    return data;
  }, [storyId, chapterId]);

  const loadMore = useCallback(async () => {
    if (loadingRef.current || rateLimitedRef.current || !hasMoreRef.current || !readTokenRef.current)
      return;
    loadingRef.current = true;
    setLoadingMore(true);

    const fetchBatch = () =>
      readingApi.paragraphs(storyId, chapterId, readTokenRef.current, nextStartRef.current, BATCH_SIZE);

    try {
      let batch;
      try {
        batch = await fetchBatch();
      } catch (err) {
        // Vé đọc hết hạn (30 phút) -> xin vé mới rồi tải tiếp đúng chỗ đang đọc
        if (err.response?.status !== 401) throw err;
        await openSession();
        batch = await fetchBatch();
      }
      setParagraphs((prev) => [...prev, ...batch.paragraphs]);
      nextStartRef.current = batch.start + batch.paragraphs.length;
      hasMoreRef.current = batch.has_more;
      setHasMore(batch.has_more);
    } catch (err) {
      setError(apiError(err, "Không tải được nội dung chương."));
      if (err.response?.status === 429) {
        // Bị giới hạn tốc độ: giữ nguyên vị trí, chờ người đọc bấm tải tiếp
        rateLimitedRef.current = true;
        setRateLimited(true);
      } else {
        hasMoreRef.current = false;
        setHasMore(false);
      }
    } finally {
      loadingRef.current = false;
      setLoadingMore(false);
    }
  }, [storyId, chapterId, openSession]);

  // Mở chương: reset trạng thái, xin vé đọc, tải đợt đầu
  useEffect(() => {
    let cancelled = false;
    setMeta(null);
    setParagraphs([]);
    setError("");
    setHasMore(true);
    setPhase("opening");
    readTokenRef.current = null;
    nextStartRef.current = 0;
    hasMoreRef.current = true;
    loadingRef.current = false;
    rateLimitedRef.current = false;
    setRateLimited(false);
    window.scrollTo(0, 0);

    openSession()
      .then(() => {
        if (cancelled) return;
        setPhase("ready");
        loadMore();
      })
      .catch((err) => {
        if (cancelled) return;
        setPhase("failed");
        setError(
          err.response?.status === 404
            ? "Chương này không tồn tại hoặc chưa được xuất bản."
            : apiError(err, "Không mở được chương này.")
        );
      });

    return () => {
      cancelled = true;
    };
  }, [openSession, loadMore]);

  // Cuộn gần cuối -> tải đợt tiếp theo
  useEffect(() => {
    if (phase !== "ready") return;
    const el = sentinelRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      (entries) => entries[0].isIntersecting && loadMore(),
      { rootMargin: "500px 0px" }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [phase, loadMore]);

  // Chương ngắn: đợt đầu chưa lấp đầy màn hình thì tải tiếp luôn
  useEffect(() => {
    if (phase !== "ready" || !hasMore || loadingMore || !sentinelRef.current) return;
    if (jumpToComments || sentinelRef.current.getBoundingClientRect().top < window.innerHeight + 500)
      loadMore();
  }, [paragraphs.length, phase, hasMore, loadingMore, loadMore, jumpToComments]);

  // Đến từ thông báo bình luận: tải hết chương rồi cuộn xuống phần bình luận
  useEffect(() => {
    if (jumpToComments && phase === "ready" && !hasMore) {
      setTimeout(() => document.getElementById("binh-luan")?.scrollIntoView({ behavior: "smooth" }), 150);
    }
  }, [jumpToComments, phase, hasMore]);

  // Thanh tiến độ đọc
  useEffect(() => {
    const onScroll = () => {
      const doc = document.documentElement;
      const max = doc.scrollHeight - doc.clientHeight;
      setScrollRatio(max > 0 ? Math.min(1, doc.scrollTop / max) : 1);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, [paragraphs.length]);

  const flashNotice = useCallback(() => {
    setNotice("Nội dung chương được bảo vệ: không thể sao chép, lưu hay in.");
    clearTimeout(noticeTimerRef.current);
    noticeTimerRef.current = setTimeout(() => setNotice(""), 2600);
  }, []);

  // Lớp bảo vệ 1: chặn phím tắt copy / lưu / in / xem mã nguồn
  useEffect(() => {
    const onKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && BLOCKED_KEYS.includes(e.key.toLowerCase())) {
        e.preventDefault();
        flashNotice();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
      clearTimeout(noticeTimerRef.current);
    };
  }, [flashNotice]);

  const watermark = useMemo(() => buildWatermark(user.username), [user.username]);

  const retryAfterLimit = () => {
    rateLimitedRef.current = false;
    setRateLimited(false);
    setError("");
    loadMore();
  };

  const blockEvent = (e) => {
    e.preventDefault();
    flashNotice();
  };

  if (phase === "opening") return <PageSpinner />;
  if (phase === "failed")
    return (
      <div className="mx-auto max-w-2xl space-y-4 px-5 py-12">
        <ErrorNote>{error}</ErrorNote>
        <BackLink to={`/truyen/${storyId}`}>Về trang truyện</BackLink>
      </div>
    );

  const { chapter, total_paragraphs: total } = meta;
  const progress = total > 0 ? (paragraphs.length / total) * scrollRatio : 0;
  const readingMinutes = Math.max(1, Math.round(chapter.word_count / 220));
  const chapterPath = (id) => `/truyen/${storyId}/chuong/${id}`;

  return (
    <div>
      {/* Thanh tiến độ */}
      <div className="fixed inset-x-0 top-0 z-20 h-[3px] bg-transparent" aria-hidden="true">
        <div
          className="h-full bg-marigold transition-[width] duration-150"
          style={{ width: `${Math.round(progress * 100)}%` }}
        />
      </div>

      <article className="mx-auto max-w-[40rem] px-5 py-10 sm:py-14">
        <BackLink to={`/truyen/${storyId}`}>{meta.story_title}</BackLink>

        <header className="mt-8">
          <p className="text-sm text-ink-soft">Chương {chapter.number}</p>
          <h1 className="mt-1 font-serif text-[2rem] leading-tight tracking-tight sm:text-[2.5rem]">
            {chapter.title}
          </h1>
          <p className="mt-3 text-sm text-ink-soft">
            {chapter.word_count.toLocaleString("vi-VN")} chữ, khoảng {readingMinutes} phút đọc
          </p>
        </header>

        <div
          className="protected-content mt-10"
          style={{ backgroundImage: watermark }}
          onCopy={blockEvent}
          onCut={blockEvent}
          onContextMenu={blockEvent}
          onDragStart={blockEvent}
        >
          {paragraphs.map((p) => (
            <p
              key={p.index}
              className="reader-paragraph mb-6 font-serif text-[1.15rem] leading-[1.9] text-ink sm:text-[1.1875rem]"
            >
              {p.text}
            </p>
          ))}
        </div>

        <div ref={sentinelRef} className="h-px" aria-hidden="true" />

        {loadingMore && (
          <p className="flex items-center gap-3 py-4 text-sm text-ink-soft">
            <Spinner /> Đang tải đoạn tiếp theo
          </p>
        )}

        {error && (
          <div className="space-y-3">
            <ErrorNote>{error}</ErrorNote>
            {rateLimited && (
              <Button variant="secondary" onClick={retryAfterLimit}>
                Tải tiếp
              </Button>
            )}
          </div>
        )}

        {!hasMore && !error && (
          <nav className="mt-12 border-t border-mist pt-8" aria-label="Điều hướng chương">
            <p className="font-serif text-lg italic text-ink-soft">Hết chương {chapter.number}.</p>
            <div className="mt-6 flex flex-wrap gap-3">
              {meta.prev_chapter_id && (
                <Button variant="secondary" to={chapterPath(meta.prev_chapter_id)}>
                  ‹ Chương trước
                </Button>
              )}
              <Button variant="ghost" to={`/truyen/${storyId}`}>
                Mục lục
              </Button>
              {meta.next_chapter_id ? (
                <Button to={chapterPath(meta.next_chapter_id)}>Chương sau ›</Button>
              ) : (
                <span className="self-center text-sm text-ink-soft">
                  Đây là chương mới nhất. Tác giả sẽ ra chương tiếp sớm.
                </span>
              )}
            </div>
          </nav>
        )}

        {!hasMore && !error && (
          <CommentsSection storyId={storyId} chapterId={chapterId} storyAuthorId={meta.story_author_id} />
        )}
      </article>

      <p className="print-only p-10 text-center">Nội dung chương trên ICeT không được phép in.</p>

      {notice && (
        <div
          role="status"
          className="fixed bottom-6 left-1/2 z-30 w-[min(92vw,26rem)] -translate-x-1/2 rounded-lg bg-ink px-4 py-3 text-center text-sm text-white shadow-lg"
        >
          {notice}
        </div>
      )}
    </div>
  );
}
