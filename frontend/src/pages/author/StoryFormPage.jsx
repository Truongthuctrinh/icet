import { useEffect, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router";
import { genreApi, storyApi } from "../../api/client";
import StoryCover from "../../components/StoryCover";
import { BackLink, Button, ErrorNote, Field, PageSpinner } from "../../components/ui";
import { useAuth } from "../../context/AuthContext";
import { apiError, STATUS_LABELS } from "../../utils/format";
import { checkImageFile, IMAGE_ACCEPT, MAX_IMAGE_MB } from "../../utils/image";

/** Chọn ảnh bìa: xem trước ngay, chỉ tải lên khi bấm lưu. */
function CoverPicker({ title, authorName, currentUrl, file, removed, onPick, onRemove }) {
  const [preview, setPreview] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!file) {
      setPreview(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url); // giải phóng bộ nhớ khi đổi ảnh khác
  }, [file]);

  const handleChange = (e) => {
    const picked = e.target.files?.[0];
    e.target.value = ""; // cho phép chọn lại cùng 1 file
    if (!picked) return;
    const problem = checkImageFile(picked);
    setError(problem);
    if (!problem) onPick(picked);
  };

  const shown = preview ?? (removed ? null : currentUrl);
  return (
    <fieldset>
      <legend className="mb-1.5 block text-sm font-medium text-ink">Ảnh bìa</legend>
      <div className="flex items-end gap-5">
        <StoryCover
          story={{ title, author: { display_name: authorName }, cover_url: null }}
          previewUrl={shown}
          size="lg"
        />
        <div className="space-y-2">
          <label className="inline-flex cursor-pointer items-center rounded-lg border border-mist bg-white px-4 py-2 text-sm font-medium text-ink hover:border-dusk focus-within:outline focus-within:outline-2 focus-within:outline-dusk">
            {shown ? "Đổi ảnh khác" : "Chọn ảnh"}
            <input type="file" accept={IMAGE_ACCEPT} onChange={handleChange} className="sr-only" />
          </label>
          {shown && (
            <button type="button" onClick={onRemove} className="block text-sm text-rose hover:underline">
              Gỡ ảnh, dùng bìa chữ
            </button>
          )}
          <p className="max-w-56 text-[0.8125rem] text-ink-soft">
            JPG, PNG hoặc WebP, tối đa {MAX_IMAGE_MB} MB. Ảnh được cắt theo tỉ lệ bìa sách 2:3.
          </p>
          {error && <p className="text-[0.8125rem] text-rose">{error}</p>}
        </div>
      </div>
    </fieldset>
  );
}

/** Dùng chung cho tạo truyện mới (/tac-gia/truyen-moi) và sửa (/tac-gia/truyen/:id/sua). */
export default function StoryFormPage() {
  const { storyId } = useParams();
  const isEdit = Boolean(storyId);
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();

  const [cover, setCover] = useState({ current: null, file: null, removed: false });
  const [authorName, setAuthorName] = useState("");
  const [form, setForm] = useState({ title: "", description: "", status: "ongoing", genre_ids: [] });
  const [genres, setGenres] = useState([]);

  useEffect(() => {
    genreApi.list().then(setGenres).catch(() => {});
  }, []);

  const toggleGenre = (id) =>
    setForm((f) => ({
      ...f,
      genre_ids: f.genre_ids.includes(id)
        ? f.genre_ids.filter((g) => g !== id)
        : f.genre_ids.length < 5
          ? [...f.genre_ids, id]
          : f.genre_ids,
    }));
  const [loading, setLoading] = useState(isEdit);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(location.state?.coverError || "");

  useEffect(() => {
    if (!isEdit) return;
    storyApi
      .mine()
      .then((stories) => {
        const story = stories.find((s) => String(s.id) === storyId);
        if (!story) throw new Error("not-owner");
        setForm({
          title: story.title,
          description: story.description,
          status: story.status,
          genre_ids: story.genres.map((g) => g.id),
        });
        setCover({ current: story.cover_url, file: null, removed: false });
        setAuthorName(story.author.display_name);
      })
      .catch((err) =>
        setError(err.message === "not-owner" ? "Không tìm thấy truyện này trong truyện của bạn." : apiError(err))
      )
      .finally(() => setLoading(false));
  }, [isEdit, storyId]);

  const update = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      const payload = { ...form, title: form.title.trim() };
      const story = isEdit ? await storyApi.update(storyId, payload) : await storyApi.create(payload);
      try {
        if (cover.file) await storyApi.uploadCover(story.id, cover.file);
        else if (cover.removed && cover.current) await storyApi.removeCover(story.id);
      } catch (err) {
        // Truyện đã lưu, chỉ ảnh lỗi -> mở trang sửa (không tạo trùng truyện nếu bấm lưu lại)
        const coverError = `Đã lưu truyện nhưng chưa lưu được ảnh bìa: ${apiError(err)}`;
        if (isEdit) {
          setError(coverError);
          setSaving(false);
        } else {
          navigate(`/tac-gia/truyen/${story.id}/sua`, { replace: true, state: { coverError } });
        }
        return;
      }
      navigate(`/tac-gia/truyen/${story.id}`);
    } catch (err) {
      setError(apiError(err));
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm(`Xoá truyện "${form.title}" cùng toàn bộ chương? Không thể hoàn tác.`)) return;
    try {
      await storyApi.remove(storyId);
      navigate("/tac-gia");
    } catch (err) {
      setError(apiError(err));
    }
  };

  if (loading) return <PageSpinner />;

  return (
    <div className="mx-auto max-w-2xl px-5 py-10 sm:py-14">
      <BackLink to={isEdit ? `/tac-gia/truyen/${storyId}` : "/tac-gia"}>
        {isEdit ? "Quản lý truyện" : "Góc tác giả"}
      </BackLink>
      <h1 className="mt-6 font-serif text-3xl">{isEdit ? "Sửa thông tin truyện" : "Truyện mới"}</h1>
      {!isEdit && (
        <p className="mt-2 text-ink-soft">
          Truyện mới được lưu ở dạng bản nháp. Bạn xuất bản khi đã sẵn sàng.
        </p>
      )}

      <form onSubmit={handleSubmit} className="mt-8 space-y-6">
        <Field
          id="title"
          label="Tên truyện"
          value={form.title}
          onChange={update("title")}
          maxLength={200}
          required
        />
        <CoverPicker
          title={form.title}
          authorName={authorName || user?.display_name}
          currentUrl={cover.current}
          file={cover.file}
          removed={cover.removed}
          onPick={(file) => setCover((c) => ({ ...c, file, removed: false }))}
          onRemove={() => setCover((c) => ({ ...c, file: null, removed: true }))}
        />
        <Field
          id="description"
          as="textarea"
          rows={6}
          label="Giới thiệu"
          hint="Vài dòng để độc giả biết truyện kể về điều gì."
          value={form.description}
          onChange={update("description")}
          maxLength={5000}
        />
        <fieldset>
          <legend className="mb-1.5 block text-sm font-medium text-ink">Thể loại</legend>
          <div className="flex flex-wrap gap-2">
            {genres.map((g) => {
              const active = form.genre_ids.includes(g.id);
              return (
                <button
                  key={g.id}
                  type="button"
                  aria-pressed={active}
                  onClick={() => toggleGenre(g.id)}
                  className={`rounded-full px-3 py-1.5 text-sm transition-colors ${
                    active ? "bg-dusk text-white" : "border border-mist bg-white text-ink-soft hover:text-ink"
                  }`}
                >
                  {g.name}
                </button>
              );
            })}
          </div>
          <p className="mt-1.5 text-[0.8125rem] text-ink-soft">Chọn tối đa 5 thể loại ({form.genre_ids.length}/5).</p>
        </fieldset>
        <Field id="status" as="select" label="Tình trạng" value={form.status} onChange={update("status")}>
          {Object.entries(STATUS_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </Field>

        {error && <ErrorNote>{error}</ErrorNote>}

        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-mist pt-6">
          <Button type="submit" disabled={saving}>
            {saving ? "Đang lưu…" : isEdit ? "Lưu thay đổi" : "Tạo truyện"}
          </Button>
          {isEdit && (
            <Button variant="danger" onClick={handleDelete}>
              Xoá truyện
            </Button>
          )}
        </div>
      </form>
    </div>
  );
}
