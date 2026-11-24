import { useEffect, useState } from "react";
import { Link } from "react-router";
import { storyApi } from "../api/client";
import { Button, EmptyState, ErrorNote, PageSpinner, StatusBadge } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { apiError, timeAgo } from "../utils/format";

const PAGE_SIZE = 12;

export default function HomePage() {
  const { user } = useAuth();
  const [stories, setStories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    storyApi
      .list(0, PAGE_SIZE)
      .then((data) => {
        setStories(data);
        setHasMore(data.length === PAGE_SIZE);
      })
      .catch((err) => setError(apiError(err)))
      .finally(() => setLoading(false));
  }, []);

  const loadMore = async () => {
    setLoadingMore(true);
    try {
      const data = await storyApi.list(stories.length, PAGE_SIZE);
      setStories((prev) => [...prev, ...data]);
      setHasMore(data.length === PAGE_SIZE);
    } catch (err) {
      setError(apiError(err));
    } finally {
      setLoadingMore(false);
    }
  };

  return (
    <>
      <section className="border-b border-mist">
        <div className="mx-auto max-w-5xl px-5 pb-16 pt-14 sm:pb-24 sm:pt-20">
          <h1 className="max-w-3xl font-serif text-[2.5rem] leading-[1.1] tracking-tight sm:text-[3.75rem]">
            Viết điều bạn tưởng tượng.
            <br />
            <span className="text-ink-soft">Đọc điều người khác mơ.</span>
          </h1>
          <p className="mt-6 max-w-xl text-lg leading-relaxed text-ink-soft">
            ICeT là nơi người viết nghiệp dư đăng truyện chữ theo từng chương, và độc giả theo dõi
            từ chương đầu đến chương mới nhất. Nội dung được bảo vệ khỏi sao chép và thu thập tự
            động.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button to={user ? "/tac-gia" : "/dang-ky"}>Bắt đầu viết</Button>
            <Button variant="secondary" href="#moi-cap-nhat">
              Đọc truyện mới
            </Button>
          </div>
        </div>
      </section>

      <section id="moi-cap-nhat" className="mx-auto max-w-5xl scroll-mt-6 px-5 py-12">
        <h2 className="font-serif text-2xl">Mới cập nhật</h2>

        {loading && <PageSpinner />}
        {error && (
          <div className="mt-6">
            <ErrorNote>{error}</ErrorNote>
          </div>
        )}

        {!loading && !error && stories.length === 0 && (
          <div className="mt-6">
            <EmptyState
              title="Chưa có truyện nào được xuất bản"
              action={<Button to={user ? "/tac-gia/truyen-moi" : "/dang-ky"}>Viết truyện đầu tiên</Button>}
            >
              Truyện xuất hiện ở đây ngay khi tác giả xuất bản.
            </EmptyState>
          </div>
        )}

        <ul className="mt-4 divide-y divide-mist">
          {stories.map((story) => (
            <li key={story.id}>
              <Link to={`/truyen/${story.id}`} className="group block py-6">
                <div className="flex items-baseline justify-between gap-4">
                  <h3 className="font-serif text-xl text-ink transition-colors group-hover:text-dusk sm:text-[1.375rem]">
                    {story.title}
                  </h3>
                  <span className="shrink-0 text-sm text-ink-soft">{timeAgo(story.updated_at)}</span>
                </div>
                <div className="mt-1.5 flex flex-wrap items-center gap-3 text-sm text-ink-soft">
                  <span>{story.author.display_name}</span>
                  <StatusBadge status={story.status} />
                </div>
                <p className="mt-2.5 line-clamp-2 max-w-2xl leading-relaxed text-ink/80">
                  {story.description || "Tác giả chưa viết giới thiệu cho truyện này."}
                </p>
              </Link>
            </li>
          ))}
        </ul>

        {hasMore && (
          <div className="mt-6">
            <Button variant="secondary" onClick={loadMore} disabled={loadingMore}>
              {loadingMore ? "Đang tải…" : "Xem thêm truyện"}
            </Button>
          </div>
        )}
      </section>
    </>
  );
}
