import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router";
import { chapterApi, storyApi } from "../../api/client";
import {
  BackLink,
  Button,
  EmptyState,
  ErrorNote,
  PageSpinner,
  PublishBadge,
  StatusBadge,
} from "../../components/ui";
import { apiError, timeAgo } from "../../utils/format";

export default function ManageStoryPage() {
  const { storyId } = useParams();
  const [story, setStory] = useState(null);
  const [chapters, setChapters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);

  const load = useCallback(async () => {
    const [mine, list] = await Promise.all([storyApi.mine(), chapterApi.manage(storyId)]);
    const found = mine.find((s) => String(s.id) === storyId);
    if (!found) throw new Error("not-owner");
    setStory(found);
    setChapters(list);
  }, [storyId]);

  useEffect(() => {
    load()
      .catch((err) =>
        setError(
          err.message === "not-owner" || err.response?.status === 403 || err.response?.status === 404
            ? "Không tìm thấy truyện này trong truyện của bạn."
            : apiError(err)
        )
      )
      .finally(() => setLoading(false));
  }, [load]);

  const toggleStory = async () => {
    setError("");
    try {
      setStory(await storyApi.update(story.id, { is_published: !story.is_published }));
    } catch (err) {
      setError(apiError(err));
    }
  };

  const toggleChapter = async (chapter) => {
    setBusyId(chapter.id);
    setError("");
    try {
      await chapterApi.update(story.id, chapter.id, { is_published: !chapter.is_published });
      await load(); // tải lại để thứ tự "mới cập nhật" của truyện cũng đúng
    } catch (err) {
      setError(apiError(err));
    } finally {
      setBusyId(null);
    }
  };

  const deleteChapter = async (chapter) => {
    if (!window.confirm(`Xoá chương ${chapter.number}: "${chapter.title}"? Không thể hoàn tác.`)) return;
    setBusyId(chapter.id);
    try {
      await chapterApi.remove(story.id, chapter.id);
      setChapters((prev) => prev.filter((c) => c.id !== chapter.id));
    } catch (err) {
      setError(apiError(err));
    } finally {
      setBusyId(null);
    }
  };

  if (loading) return <PageSpinner />;
  if (!story)
    return (
      <div className="mx-auto max-w-3xl space-y-4 px-5 py-12">
        <ErrorNote>{error}</ErrorNote>
        <BackLink to="/tac-gia">Góc tác giả</BackLink>
      </div>
    );

  const publishedCount = chapters.filter((c) => c.is_published).length;

  return (
    <div className="mx-auto max-w-4xl px-5 py-10 sm:py-14">
      <BackLink to="/tac-gia">Góc tác giả</BackLink>

      <div className="mt-6 flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <h1 className="font-serif text-[2.25rem] leading-tight tracking-tight">{story.title}</h1>
          <div className="mt-3 flex flex-wrap items-center gap-2.5 text-sm text-ink-soft">
            <PublishBadge published={story.is_published} />
            <StatusBadge status={story.status} />
            <span>
              {publishedCount}/{chapters.length} chương đã xuất bản
            </span>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button size="sm" variant="secondary" to={`/tac-gia/truyen/${story.id}/sua`}>
            Sửa thông tin
          </Button>
          {story.is_published && (
            <Button size="sm" variant="secondary" to={`/truyen/${story.id}`}>
              Xem như độc giả
            </Button>
          )}
          <Button size="sm" variant={story.is_published ? "ghost" : "primary"} onClick={toggleStory}>
            {story.is_published ? "Ẩn truyện" : "Xuất bản truyện"}
          </Button>
        </div>
      </div>

      {!story.is_published && (
        <p className="mt-6 rounded-lg border border-marigold/40 bg-marigold/10 px-4 py-3 text-sm text-ink">
          Truyện đang là bản nháp nên độc giả chưa thấy, kể cả các chương đã xuất bản. Xuất bản
          truyện khi bạn sẵn sàng.
        </p>
      )}

      {error && (
        <div className="mt-6">
          <ErrorNote>{error}</ErrorNote>
        </div>
      )}

      <section className="mt-10">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-mist pb-3">
          <h2 className="font-serif text-2xl">Các chương</h2>
          <Button size="sm" to={`/tac-gia/truyen/${story.id}/chuong-moi`}>
            Viết chương mới
          </Button>
        </div>

        {chapters.length === 0 ? (
          <div className="mt-6">
            <EmptyState
              title="Chưa có chương nào"
              action={<Button to={`/tac-gia/truyen/${story.id}/chuong-moi`}>Viết chương 1</Button>}
            >
              Viết chương đầu tiên. Bạn có thể lưu nháp và xuất bản sau.
            </EmptyState>
          </div>
        ) : (
          <ol className="divide-y divide-mist">
            {chapters.map((chapter) => (
              <li key={chapter.id} className="flex flex-wrap items-center gap-x-5 gap-y-3 py-4">
                <span className="w-20 shrink-0 text-sm tabular-nums text-ink-soft">
                  Chương {chapter.number}
                </span>
                <div className="min-w-0 flex-1">
                  <Link
                    to={`/tac-gia/truyen/${story.id}/chuong/${chapter.id}/sua`}
                    className="font-serif text-lg hover:text-dusk"
                  >
                    {chapter.title}
                  </Link>
                  <div className="mt-1 flex flex-wrap items-center gap-2.5 text-[0.8125rem] text-ink-soft">
                    <PublishBadge published={chapter.is_published} />
                    <span>{chapter.word_count.toLocaleString("vi-VN")} chữ</span>
                    <span>sửa {timeAgo(chapter.updated_at)}</span>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    variant="secondary"
                    to={`/tac-gia/truyen/${story.id}/chuong/${chapter.id}/sua`}
                  >
                    Sửa
                  </Button>
                  <Button
                    size="sm"
                    variant={chapter.is_published ? "ghost" : "primary"}
                    onClick={() => toggleChapter(chapter)}
                    disabled={busyId === chapter.id}
                  >
                    {chapter.is_published ? "Chuyển về nháp" : "Xuất bản"}
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="hover:text-rose"
                    onClick={() => deleteChapter(chapter)}
                    disabled={busyId === chapter.id}
                  >
                    Xoá
                  </Button>
                </div>
              </li>
            ))}
          </ol>
        )}
      </section>
    </div>
  );
}
