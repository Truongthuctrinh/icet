import { useEffect, useState } from "react";
import { useSearchParams } from "react-router";
import { genreApi, storyApi } from "../api/client";
import StoryListItem from "../components/StoryListItem";
import { Button, EmptyState, ErrorNote, PageSpinner } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { apiError, STATUS_LABELS } from "../utils/format";

const PAGE_SIZE = 12;
const SORTS = [
  { value: "updated", label: "Mới cập nhật" },
  { value: "new", label: "Mới đăng" },
  { value: "rating", label: "Đánh giá cao" },
  { value: "followers", label: "Nhiều người theo dõi" },
];

export default function HomePage() {
  const { user } = useAuth();
  const [params, setParams] = useSearchParams();
  const filters = {
    q: params.get("q") || "",
    genre: params.get("genre") || "",
    status: params.get("status") || "",
    sort: params.get("sort") || "updated",
  };
  const filterKey = params.toString();
  const hasFilter = Boolean(filters.q || filters.genre || filters.status);

  const [genres, setGenres] = useState([]);
  const [search, setSearch] = useState(filters.q);
  const [stories, setStories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    genreApi.list().then(setGenres).catch(() => {});
  }, []);

  const cleanFilters = () =>
    Object.fromEntries(Object.entries(filters).filter(([, v]) => v));

  useEffect(() => {
    setLoading(true);
    setError("");
    storyApi
      .list(0, PAGE_SIZE, cleanFilters())
      .then((data) => {
        setStories(data);
        setHasMore(data.length === PAGE_SIZE);
      })
      .catch((err) => setError(apiError(err)))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterKey]);

  const setFilter = (key, value) => {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    setParams(next, { replace: true });
  };

  const loadMore = async () => {
    setLoadingMore(true);
    try {
      const data = await storyApi.list(stories.length, PAGE_SIZE, cleanFilters());
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
      {!hasFilter && (
        <section className="border-b border-mist">
          <div className="mx-auto max-w-5xl px-5 pb-16 pt-14 sm:pb-20 sm:pt-20">
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
              <Button variant="secondary" href="#truyen">
                Đọc truyện
              </Button>
            </div>
          </div>
        </section>
      )}

      <section id="truyen" className="mx-auto max-w-5xl scroll-mt-6 px-5 py-10">
        <form
          role="search"
          onSubmit={(e) => {
            e.preventDefault();
            setFilter("q", search.trim());
          }}
          className="flex gap-2"
        >
          <label htmlFor="search" className="sr-only">
            Tìm truyện
          </label>
          <input
            id="search"
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Tìm theo tên truyện, giới thiệu hoặc tác giả"
            className="w-full rounded-lg border border-mist bg-white px-4 py-2.5 text-ink placeholder:text-ink-soft/60 focus:border-dusk focus:outline-none focus:ring-2 focus:ring-dusk/15"
          />
          <Button type="submit">Tìm</Button>
        </form>

        <div className="mt-5 flex flex-wrap gap-2" role="group" aria-label="Lọc theo thể loại">
          <GenreChip active={!filters.genre} onClick={() => setFilter("genre", "")}>
            Tất cả thể loại
          </GenreChip>
          {genres.map((g) => (
            <GenreChip key={g.id} active={filters.genre === g.slug} onClick={() => setFilter("genre", g.slug)}>
              {g.name}
            </GenreChip>
          ))}
        </div>

        <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-b border-mist pb-3">
          <h2 className="font-serif text-2xl">
            {filters.q ? `Kết quả cho "${filters.q}"` : SORTS.find((s) => s.value === filters.sort)?.label}
          </h2>
          <div className="flex flex-wrap gap-2">
            <label className="sr-only" htmlFor="status">Tình trạng</label>
            <select
              id="status"
              value={filters.status}
              onChange={(e) => setFilter("status", e.target.value)}
              className="rounded-lg border border-mist bg-white px-3 py-2 text-sm text-ink"
            >
              <option value="">Mọi tình trạng</option>
              {Object.entries(STATUS_LABELS).map(([v, label]) => (
                <option key={v} value={v}>{label}</option>
              ))}
            </select>
            <label className="sr-only" htmlFor="sort">Sắp xếp</label>
            <select
              id="sort"
              value={filters.sort}
              onChange={(e) => setFilter("sort", e.target.value === "updated" ? "" : e.target.value)}
              className="rounded-lg border border-mist bg-white px-3 py-2 text-sm text-ink"
            >
              {SORTS.map((s) => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          </div>
        </div>

        {error && (
          <div className="mt-6">
            <ErrorNote>{error}</ErrorNote>
          </div>
        )}

        {loading ? (
          <PageSpinner />
        ) : stories.length === 0 && !error ? (
          <div className="mt-6">
            {hasFilter ? (
              <EmptyState
                title="Không tìm thấy truyện phù hợp"
                action={<Button variant="secondary" onClick={() => { setSearch(""); setParams({}); }}>Xoá bộ lọc</Button>}
              >
                Thử từ khoá khác hoặc bỏ bớt bộ lọc.
              </EmptyState>
            ) : (
              <EmptyState
                title="Chưa có truyện nào được xuất bản"
                action={<Button to={user ? "/tac-gia/truyen-moi" : "/dang-ky"}>Viết truyện đầu tiên</Button>}
              >
                Truyện xuất hiện ở đây ngay khi tác giả xuất bản.
              </EmptyState>
            )}
          </div>
        ) : (
          <ul className="divide-y divide-mist">
            {stories.map((story) => (
              <StoryListItem key={story.id} story={story} />
            ))}
          </ul>
        )}

        {hasMore && !loading && (
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

function GenreChip({ active, onClick, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={`rounded-full px-3.5 py-1.5 text-sm transition-colors ${
        active ? "bg-ink text-white" : "border border-mist bg-white text-ink-soft hover:text-ink"
      }`}
    >
      {children}
    </button>
  );
}
