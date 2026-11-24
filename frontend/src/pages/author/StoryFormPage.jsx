import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router";
import { storyApi } from "../../api/client";
import { BackLink, Button, ErrorNote, Field, PageSpinner } from "../../components/ui";
import { apiError, STATUS_LABELS } from "../../utils/format";

/** Dùng chung cho tạo truyện mới (/tac-gia/truyen-moi) và sửa (/tac-gia/truyen/:id/sua). */
export default function StoryFormPage() {
  const { storyId } = useParams();
  const isEdit = Boolean(storyId);
  const navigate = useNavigate();

  const [form, setForm] = useState({ title: "", description: "", status: "ongoing" });
  const [loading, setLoading] = useState(isEdit);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isEdit) return;
    storyApi
      .mine()
      .then((stories) => {
        const story = stories.find((s) => String(s.id) === storyId);
        if (!story) throw new Error("not-owner");
        setForm({ title: story.title, description: story.description, status: story.status });
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
