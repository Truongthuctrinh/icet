import { useEffect, useState } from "react";
import { useParams } from "react-router";
import { userApi } from "../api/client";
import StoryListItem from "../components/StoryListItem";
import { EmptyState, ErrorNote, PageSpinner } from "../components/ui";
import { apiError, formatDate } from "../utils/format";

export default function ProfilePage() {
  const { username } = useParams();
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
        <div
          aria-hidden="true"
          className="flex h-16 w-16 items-center justify-center rounded-full bg-dusk font-serif text-2xl text-white"
        >
          {profile.display_name.trim().charAt(0).toUpperCase()}
        </div>
        <div>
          <h1 className="font-serif text-4xl tracking-tight">{profile.display_name}</h1>
          <p className="mt-1 text-sm text-ink-soft">
            @{profile.username}, tham gia {formatDate(profile.created_at)}
          </p>
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
