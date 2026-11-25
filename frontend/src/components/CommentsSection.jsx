import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router";
import { commentApi } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { apiError, timeAgo } from "../utils/format";
import Avatar from "./Avatar";
import { Button, ErrorNote } from "./ui";

const TEXTAREA =
  "w-full rounded-lg border border-mist bg-white px-3.5 py-2.5 text-ink placeholder:text-ink-soft/60 focus:border-dusk focus:outline-none focus:ring-2 focus:ring-dusk/15";

function CommentForm({ initial = "", placeholder, submitLabel, onSubmit, onCancel, autoFocus }) {
  const [text, setText] = useState(initial);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await onSubmit(text.trim());
      setText("");
    } catch (err) {
      setError(apiError(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={submit} className="space-y-2">
      <textarea
        rows={3}
        value={text}
        maxLength={2000}
        autoFocus={autoFocus}
        onChange={(e) => setText(e.target.value)}
        placeholder={placeholder}
        aria-label={placeholder}
        className={TEXTAREA}
      />
      {error && <ErrorNote>{error}</ErrorNote>}
      <div className="flex gap-2">
        <Button type="submit" size="sm" disabled={!text.trim() || busy}>
          {busy ? "Đang gửi…" : submitLabel}
        </Button>
        {onCancel && (
          <Button size="sm" variant="ghost" onClick={onCancel}>
            Huỷ
          </Button>
        )}
      </div>
    </form>
  );
}

function CommentItem({ comment, canModerate, onReply, onEdit, onDelete, isReply }) {
  const { user } = useAuth();
  const [mode, setMode] = useState(null); // null | "reply" | "edit"
  const mine = user?.id === comment.user.id;

  return (
    <li className={isReply ? "border-l-2 border-mist pl-4" : ""}>
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <Link to={`/nguoi-dung/${comment.user.username}`} className="flex items-center gap-2 font-medium text-ink hover:text-dusk">
          <Avatar user={comment.user} size="xs" />
          {comment.user.display_name}
        </Link>
        {comment.is_story_author && (
          <span className="rounded-full bg-dusk/10 px-2 py-0.5 text-[0.7rem] font-medium text-dusk">Tác giả</span>
        )}
        <span className="text-ink-soft">{timeAgo(comment.created_at)}</span>
        {comment.is_edited && <span className="text-ink-soft">(đã sửa)</span>}
      </div>

      {mode === "edit" ? (
        <div className="mt-2">
          <CommentForm
            initial={comment.content}
            placeholder="Sửa bình luận"
            submitLabel="Lưu"
            autoFocus
            onSubmit={async (text) => {
              await onEdit(comment.id, text);
              setMode(null);
            }}
            onCancel={() => setMode(null)}
          />
        </div>
      ) : comment.is_deleted ? (
        <p className="mt-1 text-sm italic text-ink-soft">Bình luận này đã bị xoá.</p>
      ) : (
        <p className="mt-1 whitespace-pre-line leading-relaxed text-ink/90">{comment.content}</p>
      )}

      {!comment.is_deleted && mode !== "edit" && user && (
        <div className="mt-1.5 flex gap-4 text-[0.8125rem] text-ink-soft">
          <button type="button" className="hover:text-dusk" onClick={() => setMode(mode === "reply" ? null : "reply")}>
            Trả lời
          </button>
          {mine && (
            <button type="button" className="hover:text-dusk" onClick={() => setMode("edit")}>
              Sửa
            </button>
          )}
          {(mine || canModerate) && (
            <button
              type="button"
              className="hover:text-rose"
              onClick={() => window.confirm("Xoá bình luận này?") && onDelete(comment.id)}
            >
              Xoá
            </button>
          )}
        </div>
      )}

      {mode === "reply" && (
        <div className="mt-3">
          <CommentForm
            placeholder={`Trả lời ${comment.user.display_name}`}
            submitLabel="Gửi trả lời"
            autoFocus
            onSubmit={async (text) => {
              await onReply(comment.id, text);
              setMode(null);
            }}
            onCancel={() => setMode(null)}
          />
        </div>
      )}

      {comment.replies?.length > 0 && (
        <ul className="mt-4 space-y-4">
          {comment.replies.map((r) => (
            <CommentItem
              key={r.id}
              comment={r}
              canModerate={canModerate}
              onReply={onReply}
              onEdit={onEdit}
              onDelete={onDelete}
              isReply
            />
          ))}
        </ul>
      )}
    </li>
  );
}

export default function CommentsSection({ storyId, chapterId, storyAuthorId }) {
  const { user } = useAuth();
  const location = useLocation();
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    commentApi
      .list(storyId, chapterId)
      .then(setComments)
      .catch((err) => setError(apiError(err)))
      .finally(() => setLoading(false));
  }, [storyId, chapterId]);

  const canModerate = user && (user.id === storyAuthorId || user.role === "admin");
  const run = async (request) => setComments(await request);
  const total = comments.reduce(
    (n, c) => n + (c.is_deleted ? 0 : 1) + c.replies.filter((r) => !r.is_deleted).length,
    0
  );

  return (
    <section id="binh-luan" className="mt-16 scroll-mt-6 border-t border-mist pt-10" aria-labelledby="binh-luan-title">
      <h2 id="binh-luan-title" className="font-serif text-2xl">
        Bình luận {total > 0 && <span className="text-ink-soft">({total})</span>}
      </h2>

      <div className="mt-5">
        {user ? (
          <CommentForm
            placeholder="Bạn nghĩ gì về chương này?"
            submitLabel="Gửi bình luận"
            onSubmit={(text) => run(commentApi.add(storyId, chapterId, text))}
          />
        ) : (
          <p className="text-sm text-ink-soft">
            <Link to="/dang-nhap" state={{ from: location.pathname }} className="font-medium text-dusk hover:underline">
              Đăng nhập
            </Link>{" "}
            để bình luận.
          </p>
        )}
      </div>

      {error && <div className="mt-4"><ErrorNote>{error}</ErrorNote></div>}

      {!loading && comments.length === 0 && !error && (
        <p className="mt-6 text-ink-soft">Chưa có bình luận nào. Hãy là người đầu tiên chia sẻ cảm nhận.</p>
      )}

      <ul className="mt-8 space-y-7">
        {comments.map((c) => (
          <CommentItem
            key={c.id}
            comment={c}
            canModerate={canModerate}
            onReply={(parentId, text) => run(commentApi.add(storyId, chapterId, text, parentId))}
            onEdit={(id, text) => run(commentApi.edit(storyId, chapterId, id, text))}
            onDelete={(id) => run(commentApi.remove(storyId, chapterId, id)).catch((err) => setError(apiError(err)))}
          />
        ))}
      </ul>
    </section>
  );
}
