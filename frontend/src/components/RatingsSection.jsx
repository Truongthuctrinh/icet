import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router";
import { ratingApi } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { apiError, timeAgo } from "../utils/format";
import { StarDisplay, StarInput } from "./Stars";
import Avatar from "./Avatar";
import { Button, ErrorNote } from "./ui";

export default function RatingsSection({ story, myRating, onChanged }) {
  const { user } = useAuth();
  const location = useLocation();
  const [summary, setSummary] = useState(null);
  const [score, setScore] = useState(myRating?.score || 0);
  const [review, setReview] = useState(myRating?.review || "");
  const [editing, setEditing] = useState(!myRating);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const isOwner = user?.id === story.author.id;

  const load = () => ratingApi.summary(story.id).then(setSummary).catch(() => {});
  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [story.id]);

  const save = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      await ratingApi.rate(story.id, score, review);
      setEditing(false);
      await load();
      onChanged?.();
    } catch (err) {
      setError(apiError(err));
    } finally {
      setSaving(false);
    }
  };

  const remove = async () => {
    await ratingApi.remove(story.id);
    setScore(0);
    setReview("");
    setEditing(true);
    await load();
    onChanged?.();
  };

  const max = summary ? Math.max(1, ...Object.values(summary.distribution)) : 1;

  return (
    <section id="danh-gia" className="mt-14 scroll-mt-6">
      <div className="flex items-baseline justify-between border-b border-mist pb-3">
        <h2 className="font-serif text-2xl">Đánh giá</h2>
        <span className="text-sm text-ink-soft">{summary?.rating_count ?? 0} lượt</span>
      </div>

      {summary && summary.rating_count > 0 && (
        <div className="mt-6 flex flex-wrap items-center gap-8">
          <div className="text-center">
            <p className="font-serif text-5xl leading-none tabular-nums">{summary.rating_avg.toFixed(1)}</p>
            <div className="mt-2">
              <StarDisplay value={summary.rating_avg} />
            </div>
          </div>
          <dl className="min-w-[14rem] flex-1 space-y-1.5">
            {[5, 4, 3, 2, 1].map((s) => (
              <div key={s} className="flex items-center gap-3 text-sm">
                <dt className="w-10 shrink-0 text-ink-soft">{s} sao</dt>
                <dd className="h-2 flex-1 overflow-hidden rounded-full bg-mist">
                  <div className="h-full rounded-full bg-marigold" style={{ width: `${(summary.distribution[s] / max) * 100}%` }} />
                </dd>
                <span className="w-6 text-right tabular-nums text-ink-soft">{summary.distribution[s]}</span>
              </div>
            ))}
          </dl>
        </div>
      )}

      {!user ? (
        <p className="mt-6 text-sm text-ink-soft">
          <Link to="/dang-nhap" state={{ from: location.pathname }} className="font-medium text-dusk hover:underline">
            Đăng nhập
          </Link>{" "}
          để đánh giá truyện này.
        </p>
      ) : isOwner ? null : editing ? (
        <form onSubmit={save} className="mt-6 rounded-xl border border-mist bg-white p-5">
          <p className="mb-2 text-sm font-medium text-ink">{myRating ? "Sửa đánh giá của bạn" : "Bạn thấy truyện này thế nào?"}</p>
          <StarInput value={score} onChange={setScore} />
          <label htmlFor="review" className="sr-only">Nhận xét</label>
          <textarea
            id="review"
            rows={3}
            value={review}
            maxLength={2000}
            onChange={(e) => setReview(e.target.value)}
            placeholder="Vài dòng nhận xét cho tác giả (không bắt buộc)"
            className="mt-3 w-full rounded-lg border border-mist bg-white px-3.5 py-2.5 text-ink placeholder:text-ink-soft/60 focus:border-dusk focus:outline-none focus:ring-2 focus:ring-dusk/15"
          />
          {error && <div className="mt-3"><ErrorNote>{error}</ErrorNote></div>}
          <div className="mt-3 flex gap-2">
            <Button type="submit" size="sm" disabled={!score || saving}>
              {saving ? "Đang gửi…" : "Gửi đánh giá"}
            </Button>
            {myRating && (
              <Button size="sm" variant="ghost" onClick={() => setEditing(false)}>Huỷ</Button>
            )}
          </div>
        </form>
      ) : (
        <div className="mt-6 flex flex-wrap items-center gap-3 text-sm text-ink-soft">
          <span>Bạn đã chấm</span>
          <StarDisplay value={score} size="text-sm" />
          <Button size="sm" variant="ghost" onClick={() => setEditing(true)}>Sửa</Button>
          <Button size="sm" variant="ghost" className="hover:text-rose" onClick={remove}>Xoá đánh giá</Button>
        </div>
      )}

      {summary && summary.items.length > 0 && (
        <ul className="mt-6 divide-y divide-mist">
          {summary.items.map((r) => (
            <li key={r.id} className="py-4">
              <div className="flex flex-wrap items-center gap-3 text-sm">
                <Link to={`/nguoi-dung/${r.user.username}`} className="flex items-center gap-2 font-medium text-ink hover:text-dusk">
                  <Avatar user={r.user} size="xs" />
                  {r.user.display_name}
                </Link>
                <StarDisplay value={r.score} size="text-sm" />
                <span className="text-ink-soft">{timeAgo(r.updated_at)}</span>
              </div>
              {r.review && <p className="mt-1.5 whitespace-pre-line leading-relaxed text-ink/85">{r.review}</p>}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
