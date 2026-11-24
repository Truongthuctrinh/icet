import { useEffect, useState } from "react";
import { Link, useParams } from "react-router";
import { chapterApi, storyApi } from "../api/client";
import { BackLink, Button, EmptyState, ErrorNote, PageSpinner, StatusBadge } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { apiError, formatDate, timeAgo } from "../utils/format";

export default function StoryPage() {
  const { storyId } = useParams();
  const { user } = useAuth();
  const [story, setStory] = useState(null);
  const [chapters, setChapters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    Promise.all([storyApi.get(storyId), chapterApi.toc(storyId)])
      .then(([storyData, tocData]) => {
        setStory(storyData);
        setChapters(tocData);
      })
      .catch((err) =>
        setError(
          err.response?.status === 404
            ? "Truyện này không tồn tại hoặc chưa được xuất bản."
            : apiError(err)
        )
      )
      .finally(() => setLoading(false));
  }, [storyId]);

  if (loading) return <PageSpinner />;
  if (error)
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

      <h1 className="mt-6 font-serif text-[2.25rem] leading-tight tracking-tight sm:text-5xl">
        {story.title}
      </h1>
      <div className="mt-4 flex flex-wrap items-center gap-3 text-sm text-ink-soft">
        <span>
          Tác giả <span className="font-medium text-ink">{story.author.display_name}</span>
        </span>
        <StatusBadge status={story.status} />
        <span>Cập nhật {timeAgo(story.updated_at)}</span>
      </div>

      <p className="mt-6 whitespace-pre-line font-serif text-lg leading-[1.8] text-ink/85">
        {story.description || "Tác giả chưa viết giới thiệu cho truyện này."}
      </p>

      <div className="mt-8 flex flex-wrap gap-3">
        {first && <Button to={readPath(first)}>Đọc từ chương {first.number}</Button>}
        {latest && latest.id !== first.id && (
          <Button variant="secondary" to={readPath(latest)}>
            Đọc chương mới nhất
          </Button>
        )}
        {isOwner && (
          <Button variant="ghost" to={`/tac-gia/truyen/${story.id}`}>
            Quản lý truyện
          </Button>
        )}
      </div>

      <section className="mt-14">
        <div className="flex items-baseline justify-between border-b border-mist pb-3">
          <h2 className="font-serif text-2xl">Mục lục</h2>
          <span className="text-sm text-ink-soft">{chapters.length} chương</span>
        </div>

        {chapters.length === 0 ? (
          <div className="mt-6">
            <EmptyState title="Chưa có chương nào">
              Tác giả chưa xuất bản chương nào. Quay lại sau nhé.
            </EmptyState>
          </div>
        ) : (
          <ol className="divide-y divide-mist">
            {chapters.map((chapter) => (
              <li key={chapter.id}>
                <Link
                  to={readPath(chapter)}
                  className="group flex items-baseline gap-4 py-4 hover:text-dusk"
                >
                  <span className="w-20 shrink-0 text-sm tabular-nums text-ink-soft">
                    Chương {chapter.number}
                  </span>
                  <span className="flex-1 font-serif text-lg group-hover:text-dusk">
                    {chapter.title}
                  </span>
                  <span className="hidden shrink-0 text-sm text-ink-soft sm:inline">
                    {chapter.word_count.toLocaleString("vi-VN")} chữ, {formatDate(chapter.updated_at)}
                  </span>
                </Link>
              </li>
            ))}
          </ol>
        )}
      </section>
    </div>
  );
}
