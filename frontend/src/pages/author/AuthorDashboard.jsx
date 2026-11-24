import { useEffect, useState } from "react";
import { Link } from "react-router";
import { storyApi } from "../../api/client";
import {
  Button,
  EmptyState,
  ErrorNote,
  PageSpinner,
  PublishBadge,
  StatusBadge,
} from "../../components/ui";
import { useAuth } from "../../context/AuthContext";
import { apiError, timeAgo } from "../../utils/format";

export default function AuthorDashboard() {
  const { user } = useAuth();
  const [stories, setStories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);

  useEffect(() => {
    storyApi
      .mine()
      .then(setStories)
      .catch((err) => setError(apiError(err)))
      .finally(() => setLoading(false));
  }, []);

  const togglePublish = async (story) => {
    setBusyId(story.id);
    setError("");
    try {
      const updated = await storyApi.update(story.id, { is_published: !story.is_published });
      setStories((prev) => prev.map((s) => (s.id === updated.id ? updated : s)));
    } catch (err) {
      setError(apiError(err));
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="mx-auto max-w-5xl px-5 py-10 sm:py-14">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-serif text-4xl tracking-tight">Góc tác giả</h1>
          <p className="mt-2 text-ink-soft">
            Chào {user.display_name}. Truyện của bạn, cả bản nháp lẫn đã xuất bản, đều ở đây.
          </p>
        </div>
        <Button to="/tac-gia/truyen-moi">Viết truyện mới</Button>
      </div>

      {error && (
        <div className="mt-6">
          <ErrorNote>{error}</ErrorNote>
        </div>
      )}

      {loading ? (
        <PageSpinner />
      ) : stories.length === 0 ? (
        <div className="mt-10">
          <EmptyState
            title="Bạn chưa có truyện nào"
            action={<Button to="/tac-gia/truyen-moi">Viết truyện đầu tiên</Button>}
          >
            Tạo truyện, viết chương đầu tiên rồi xuất bản để độc giả tìm thấy bạn.
          </EmptyState>
        </div>
      ) : (
        <ul className="mt-10 divide-y divide-mist rounded-xl border border-mist bg-white">
          {stories.map((story) => (
            <li key={story.id} className="flex flex-wrap items-center gap-x-6 gap-y-3 px-5 py-5">
              <div className="min-w-0 flex-1">
                <Link
                  to={`/tac-gia/truyen/${story.id}`}
                  className="font-serif text-xl text-ink hover:text-dusk"
                >
                  {story.title}
                </Link>
                <div className="mt-2 flex flex-wrap items-center gap-2.5 text-sm text-ink-soft">
                  <PublishBadge published={story.is_published} />
                  <StatusBadge status={story.status} />
                  <span>Sửa lần cuối {timeAgo(story.updated_at)}</span>
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button size="sm" variant="secondary" to={`/tac-gia/truyen/${story.id}`}>
                  Quản lý chương
                </Button>
                <Button
                  size="sm"
                  variant={story.is_published ? "ghost" : "primary"}
                  onClick={() => togglePublish(story)}
                  disabled={busyId === story.id}
                >
                  {story.is_published ? "Ẩn truyện" : "Xuất bản"}
                </Button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
