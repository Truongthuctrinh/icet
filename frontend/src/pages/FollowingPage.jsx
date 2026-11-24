import { useEffect, useState } from "react";
import { followApi } from "../api/client";
import StoryListItem from "../components/StoryListItem";
import { Button, EmptyState, ErrorNote, PageSpinner } from "../components/ui";
import { apiError } from "../utils/format";

export default function FollowingPage() {
  const [stories, setStories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    followApi
      .mine()
      .then(setStories)
      .catch((err) => setError(apiError(err)))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="mx-auto max-w-5xl px-5 py-10 sm:py-14">
      <h1 className="font-serif text-4xl tracking-tight">Tủ truyện</h1>
      <p className="mt-2 text-ink-soft">Truyện bạn đang theo dõi, truyện vừa ra chương mới ở trên cùng.</p>
      {error && <div className="mt-6"><ErrorNote>{error}</ErrorNote></div>}
      {loading ? (
        <PageSpinner />
      ) : stories.length === 0 ? (
        <div className="mt-8">
          <EmptyState title="Tủ truyện đang trống" action={<Button to="/">Khám phá truyện</Button>}>
            Bấm "Theo dõi truyện" ở trang truyện bất kỳ để thêm vào đây.
          </EmptyState>
        </div>
      ) : (
        <ul className="mt-4 divide-y divide-mist">
          {stories.map((s) => <StoryListItem key={s.id} story={s} />)}
        </ul>
      )}
    </div>
  );
}
