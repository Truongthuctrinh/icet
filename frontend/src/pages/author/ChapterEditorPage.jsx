import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router";
import { chapterApi, storyApi } from "../../api/client";
import { BackLink, Button, ErrorNote, Field, PageSpinner, PublishBadge } from "../../components/ui";
import { apiError, countWords } from "../../utils/format";

/** Dùng chung cho viết chương mới và sửa chương. */
export default function ChapterEditorPage() {
  const { storyId, chapterId } = useParams();
  const isEdit = Boolean(chapterId);
  const navigate = useNavigate();

  const [storyTitle, setStoryTitle] = useState("");
  const [chapter, setChapter] = useState(null); // chỉ có khi sửa
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const requests = [storyApi.mine()];
    if (isEdit) requests.push(chapterApi.getForEdit(storyId, chapterId));

    Promise.all(requests)
      .then(([mine, existing]) => {
        const story = mine.find((s) => String(s.id) === storyId);
        if (!story) throw new Error("not-owner");
        setStoryTitle(story.title);
        if (existing) {
          setChapter(existing);
          setTitle(existing.title);
          setContent(existing.content);
        }
      })
      .catch((err) =>
        setError(
          err.message === "not-owner" || err.response?.status === 403
            ? "Bạn không có quyền sửa truyện này."
            : apiError(err)
        )
      )
      .finally(() => setLoading(false));
  }, [isEdit, storyId, chapterId]);

  const words = countWords(content);
  const paragraphs = content.split("\n").filter((line) => line.trim()).length;

  const save = async (publish) => {
    setSaving(true);
    setError("");
    try {
      const payload = { title: title.trim(), content, is_published: publish };
      if (isEdit) await chapterApi.update(storyId, chapterId, payload);
      else await chapterApi.create(storyId, payload);
      navigate(`/tac-gia/truyen/${storyId}`);
    } catch (err) {
      setError(apiError(err));
      setSaving(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // Nút submit mặc định (Enter) giữ nguyên trạng thái hiện tại của chương
    save(isEdit ? chapter.is_published : false);
  };

  if (loading) return <PageSpinner />;
  if (!storyTitle)
    return (
      <div className="mx-auto max-w-3xl space-y-4 px-5 py-12">
        <ErrorNote>{error}</ErrorNote>
        <BackLink to="/tac-gia">Góc tác giả</BackLink>
      </div>
    );

  const canSave = title.trim() && content.trim() && !saving;

  return (
    <div className="mx-auto max-w-3xl px-5 py-10 sm:py-14">
      <BackLink to={`/tac-gia/truyen/${storyId}`}>{storyTitle}</BackLink>

      <div className="mt-6 flex flex-wrap items-center gap-3">
        <h1 className="font-serif text-3xl">
          {isEdit ? `Sửa chương ${chapter.number}` : "Chương mới"}
        </h1>
        {isEdit && <PublishBadge published={chapter.is_published} />}
      </div>

      <form onSubmit={handleSubmit} className="mt-8 space-y-6">
        <Field
          id="chapter-title"
          label="Tên chương"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          maxLength={200}
          required
        />

        <div>
          <label htmlFor="chapter-content" className="mb-1.5 block text-sm font-medium text-ink">
            Nội dung
          </label>
          <textarea
            id="chapter-content"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            maxLength={100000}
            required
            className="min-h-[60vh] w-full resize-y rounded-lg border border-mist bg-white px-5 py-4 font-serif text-[1.0625rem] leading-[1.85] text-ink focus:border-dusk focus:outline-none focus:ring-2 focus:ring-dusk/15"
            placeholder="Bắt đầu chương của bạn ở đây…"
          />
          <div className="mt-1.5 flex flex-wrap justify-between gap-2 text-[0.8125rem] text-ink-soft">
            <span>Mỗi dòng là một đoạn văn. Dòng trống thừa sẽ được bỏ qua khi lưu.</span>
            <span className="tabular-nums">
              {words.toLocaleString("vi-VN")} chữ, {paragraphs} đoạn
            </span>
          </div>
        </div>

        {error && <ErrorNote>{error}</ErrorNote>}

        <div className="flex flex-wrap gap-3 border-t border-mist pt-6">
          {isEdit && chapter.is_published ? (
            <>
              <Button type="submit" disabled={!canSave}>
                {saving ? "Đang lưu…" : "Lưu thay đổi"}
              </Button>
              <Button variant="secondary" onClick={() => save(false)} disabled={!canSave}>
                Lưu và chuyển về nháp
              </Button>
            </>
          ) : (
            <>
              <Button onClick={() => save(true)} disabled={!canSave}>
                {saving ? "Đang lưu…" : "Xuất bản"}
              </Button>
              <Button type="submit" variant="secondary" disabled={!canSave}>
                Lưu bản nháp
              </Button>
            </>
          )}
        </div>
      </form>
    </div>
  );
}
