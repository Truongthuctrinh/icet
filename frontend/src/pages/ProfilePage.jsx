import { useEffect, useState } from "react";
import { useParams } from "react-router";
import { userApi } from "../api/client";
import Avatar from "../components/Avatar";
import StoryListItem from "../components/StoryListItem";
import { EmptyState, ErrorNote, PageSpinner } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { apiError, formatDate } from "../utils/format";
import { checkImageFile, IMAGE_ACCEPT } from "../utils/image";

/** Chỉ hiện trên hồ sơ của chính mình. Đổi ảnh xong cập nhật luôn ảnh trên thanh menu. */
function AvatarEditor({ avatarUrl, onChanged }) {
  const { setUser } = useAuth();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const apply = async (request) => {
    setBusy(true);
    setError("");
    try {
      const me = await request();
      setUser(me);
      onChanged(me.avatar_url);
    } catch (err) {
      setError(apiError(err));
    } finally {
      setBusy(false);
    }
  };

  const handleChange = (e) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    const problem = checkImageFile(file);
    if (problem) return setError(problem);
    apply(() => userApi.uploadAvatar(file));
  };

  return (
    <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
      <label className={`cursor-pointer text-dusk hover:underline ${busy ? "pointer-events-none opacity-60" : ""}`}>
        {busy ? "Đang tải ảnh…" : avatarUrl ? "Đổi ảnh đại diện" : "Thêm ảnh đại diện"}
        <input type="file" accept={IMAGE_ACCEPT} onChange={handleChange} className="sr-only" disabled={busy} />
      </label>
      {avatarUrl && !busy && (
        <button type="button" onClick={() => apply(userApi.removeAvatar)} className="text-ink-soft hover:text-rose">
          Gỡ ảnh
        </button>
      )}
      {error && <span className="text-rose">{error}</span>}
    </div>
  );
}

export default function ProfilePage() {
  const { username } = useParams();
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    userApi
      .profile(username)
      .then(setProfile)
      .catch((err) => setError(err.response?.status === 404 ? "Không tìm thấy người dùng này." : apiError(err)))
      .finally(() => setLoading(false));
  }, [username]);

  if (loading) return <PageSpinner />;
  if (!profile)
    return (
      <div className="mx-auto max-w-3xl px-5 py-12">
        <ErrorNote>{error}</ErrorNote>
      </div>
    );

  return (
    <div className="mx-auto max-w-5xl px-5 py-10 sm:py-14">
      <div className="flex flex-wrap items-center gap-5">
        <Avatar user={profile} size="xl" />
        <div>
          <h1 className="font-serif text-4xl tracking-tight">{profile.display_name}</h1>
          <p className="mt-1 text-sm text-ink-soft">
            @{profile.username}, tham gia {formatDate(profile.created_at)}
          </p>
          {user?.username === profile.username && (
            <AvatarEditor
              avatarUrl={profile.avatar_url}
              onChanged={(avatar_url) => setProfile((p) => ({ ...p, avatar_url }))}
            />
          )}
        </div>
      </div>
      <dl className="mt-6 flex gap-8 text-sm">
        <div>
          <dt className="text-ink-soft">Truyện đã xuất bản</dt>
          <dd className="mt-0.5 font-serif text-2xl tabular-nums">{profile.story_count}</dd>
        </div>
        <div>
          <dt className="text-ink-soft">Lượt theo dõi</dt>
          <dd className="mt-0.5 font-serif text-2xl tabular-nums">{profile.total_followers}</dd>
        </div>
      </dl>

      <h2 className="mt-12 border-b border-mist pb-3 font-serif text-2xl">Truyện của {profile.display_name}</h2>
      {profile.stories.length === 0 ? (
        <div className="mt-6"><EmptyState title="Chưa có truyện nào được xuất bản" /></div>
      ) : (
        <ul className="divide-y divide-mist">
          {profile.stories.map((s) => <StoryListItem key={s.id} story={s} showAuthor={false} />)}
        </ul>
      )}
    </div>
  );
}
