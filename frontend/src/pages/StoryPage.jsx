import { useCallback, useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router";
import { chapterApi, followApi, storyApi } from "../api/client";
import RatingsSection from "../components/RatingsSection";
import StoryCover from "../components/StoryCover";
import { StarDisplay } from "../components/Stars";
import { BackLink, Button, EmptyState, ErrorNote, PageSpinner, StatusBadge } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { apiError, formatDate, timeAgo } from "../utils/format";

export default function StoryPage() {
  const { storyId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [story, setStory] = useState(null);
  const [chapters, setChapters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [followBusy, setFollowBusy] = useState(false);

  const loadStory = useCallback(() => storyApi.get(storyId).then(setStory), [storyId]);

  useEffect(() => {
    setLoading(true);
    Promise.all([loadStory(), chapterApi.toc(storyId).then(setChapters)])
      .catch((err) =>
        setError(err.response?.status === 404 ? "Truyện này không tồn tại hoặc chưa được xuất bản." : apiError(err))
      )
      .finally(() => setLoading(false));
  }, [storyId, loadStory, user?.id]);

  // Cuộn tới #danh-gia khi đến từ thông báo
  useEffect(() => {
    if (!loading && location.hash) document.querySelector(location.hash)?.scrollIntoView();
  }, [loading, location.hash]);

  const toggleFollow = async () => {
    if (!user) return navigate("/dang-nhap", { state: { from: location.pathname } });
    setFollowBusy(true);
    try {
      const res = story.is_following ? await followApi.unfollow(story.id) : await followApi.follow(story.id);
      setStory({ ...story, ...res });
    } catch (err) {
      setError(apiError(err));
    } finally {
      setFollowBusy(false);
    }
  };

  if (loading) return <PageSpinner />;
  if (!story)
    return (
      <div className="mx-auto max-w-3xl space-y-4 px-5 py-12">
        <ErrorNote>{error}</ErrorNote>
        <BackLink to="/">Về danh sách truyện</BackLink>
      </div>
    );

  const isOwner = user?.id === story.author.id;
  const first = chapters[0];
  const latest = chapters[chapters.length - 1];
  const readPath = (chapter) => `/truyen/${story.id}/chuong/${chapter.id}`;

  return (
    <div className="mx-auto max-w-3xl px-5 py-10 sm:py-14">
      <BackLink to="/">Tất cả truyện</BackLink>

      <div className="mt-6 flex flex-col gap-6 sm:flex-row sm:items-start sm:gap-8">
        <StoryCover story={story} size="lg" />
        <div className="min-w-0 flex-1">
          <h1 className="font-serif text-[2.25rem] leading-tight tracking-tight sm:text-[2.75rem]">{story.title}</h1>
          <p className="mt-3 text-ink-soft">
            Tác giả{" "}
            <Link to={`/nguoi-dung/${story.author.username}`} className="font-medium text-ink hover:text-dusk hover:underline">
              {story.author.display_name}
            </Link>
          </p>
          <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-2 text-sm text-ink-soft">
            <StatusBadge status={story.status} />
            {story.rating_count > 0 && (
              <a href="#danh-gia" className="inline-flex items-center gap-1.5 hover:text-dusk">
                <StarDisplay value={story.rating_avg} size="text-sm" />
                {story.rating_avg.toFixed(1)} ({story.rating_count})
              </a>
            )}
            <span>{story.follower_count} người theo dõi</span>
            <span>Cập nhật {timeAgo(story.updated_at)}</span>
          </div>
          {story.genres.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {story.genres.map((g) => (
                <Link key={g.id} to={`/?genre=${g.slug}`} className="rounded-full border border-dusk/25 px-2.5 py-0.5 text-xs text-dusk hover:bg-dusk/5">
                  {g.name}
                </Link>
              ))}
            </div>
          )}
          <div className="mt-6 flex flex-wrap gap-3">
            {first && <Button to={readPath(first)}>Đọc từ chương {first.number}</Button>}
            {latest && latest.id !== first.id && (
              <Button variant="secondary" to={readPath(latest)}>Chương mới nhất</Button>
            )}
            {!isOwner && (
              <Button variant={story.is_following ? "secondary" : "ghost"} onClick={toggleFollow} disabled={followBusy}>
                {story.is_following ? "Đang theo dõi" : "Theo dõi truyện"}
              </Button>
            )}
            {isOwner && (
              <Button variant="ghost" to={`/tac-gia/truyen/${story.id}`}>Quản lý truyện</Button>
            )}
          </div>
          {!isOwner && !story.is_following && (
            <p className="mt-2 text-[0.8125rem] text-ink-soft">Theo dõi để nhận thông báo khi có chương mới.</p>
          )}
        </div>
      </div>

      {error && <div className="mt-6"><ErrorNote>{error}</ErrorNote></div>}

      <p className="mt-8 whitespace-pre-line font-serif text-lg leading-[1.8] text-ink/85">
        {story.description || "Tác giả chưa viết giới thiệu cho truyện này."}
      </p>

      <section className="mt-14">
        <div className="flex items-baseline justify-between border-b border-mist pb-3">
          <h2 className="font-serif text-2xl">Mục lục</h2>
          <span className="text-sm text-ink-soft">{chapters.length} chương</span>
        </div>
        {chapters.length === 0 ? (
          <div className="mt-6">
            <EmptyState title="Chưa có chương nào">Tác giả chưa xuất bản chương nào. Theo dõi truyện để được báo khi có chương mới.</EmptyState>
          </div>
        ) : (
          <ol className="divide-y divide-mist">
            {chapters.map((chapter) => (
              <li key={chapter.id}>
                <Link to={readPath(chapter)} className="group flex items-baseline gap-4 py-4">
                  <span className="w-20 shrink-0 text-sm tabular-nums text-ink-soft">Chương {chapter.number}</span>
                  <span className="flex-1 font-serif text-lg group-hover:text-dusk">{chapter.title}</span>
                  <span className="hidden shrink-0 text-sm text-ink-soft sm:inline">
                    {chapter.word_count.toLocaleString("vi-VN")} chữ, {formatDate(chapter.updated_at)}
                  </span>
                </Link>
              </li>
            ))}
          </ol>
        )}
      </section>

      <RatingsSection key={`${story.id}-${user?.id}`} story={story} myRating={story.my_rating} onChanged={loadStory} />
    </div>
  );
}
