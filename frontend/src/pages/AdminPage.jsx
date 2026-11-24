import { useCallback, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router";
import { adminApi } from "../api/client";
import { Button, EmptyState, ErrorNote, PageSpinner } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { apiError, describeBrowser, formatDate, formatDateTime } from "../utils/format";

const TABS = [
  { id: "tong-quan", label: "Tổng quan" },
  { id: "nguoi-dung", label: "Người dùng" },
  { id: "bao-mat", label: "Bảo mật" },
];

const SCOPE_LABEL = {
  open_chapter: "mở chương quá nhanh",
  paragraphs: "tải nội dung quá nhanh",
  login: "đăng nhập sai liên tục",
  comment: "spam bình luận",
  honeypot: "dính bẫy honeypot",
};

function Stat({ label, value, tone }) {
  return (
    <div className="rounded-xl border border-mist bg-white px-5 py-4">
      <dt className="text-sm text-ink-soft">{label}</dt>
      <dd className={`mt-1 font-serif text-3xl tabular-nums ${tone === "alert" && value > 0 ? "text-rose" : "text-ink"}`}>
        {value.toLocaleString("vi-VN")}
      </dd>
    </div>
  );
}

function Overview() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => {
    adminApi.overview().then(setData).catch((err) => setError(apiError(err)));
  }, []);
  if (error) return <ErrorNote>{error}</ErrorNote>;
  if (!data) return <PageSpinner />;
  return (
    <div className="space-y-8">
      <section>
        <h2 className="font-serif text-xl">Nội dung và người dùng</h2>
        <dl className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Stat label="Người dùng" value={data.users} />
          <Stat label="Truyện đã xuất bản" value={data.stories_published} />
          <Stat label="Chương đã xuất bản" value={data.chapters_published} />
          <Stat label="Lượt mở chương 24 giờ qua" value={data.reading_sessions_24h} />
          <Stat label="Bình luận" value={data.comments} />
          <Stat label="Đánh giá" value={data.ratings} />
          <Stat label="Tổng lượt mở chương" value={data.reading_sessions_total} />
          <Stat label="Tài khoản bị khoá" value={data.locked_users} />
        </dl>
      </section>
      <section>
        <h2 className="font-serif text-xl">Cần chú ý</h2>
        <dl className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Stat label="Cảnh báo đạo văn chờ xem xét" value={data.plagiarism_pending} tone="alert" />
          <Stat label="Đạo văn đã xác nhận" value={data.plagiarism_confirmed} />
          <Stat label="IP đang bị cấm" value={data.banned_ips} tone="alert" />
          <Stat label="Lượt bot AI bị chặn" value={data.bot_hits} />
        </dl>
        {data.plagiarism_pending > 0 && (
          <div className="mt-4">
            <Button size="sm" to="/tac-gia/dao-van">Xem cảnh báo đạo văn</Button>
          </div>
        )}
      </section>
    </div>
  );
}

function Users() {
  const { user: me } = useAuth();
  const [q, setQ] = useState("");
  const [users, setUsers] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(null);

  const load = useCallback((query = "") => {
    adminApi.users(query).then(setUsers).catch((err) => setError(apiError(err)));
  }, []);
  useEffect(() => load(), [load]);

  const update = async (u, payload, confirmText) => {
    if (confirmText && !window.confirm(confirmText)) return;
    setBusy(u.id);
    setError("");
    try {
      const updated = await adminApi.updateUser(u.id, payload);
      setUsers((prev) => prev.map((x) => (x.id === u.id ? updated : x)));
    } catch (err) {
      setError(apiError(err));
    } finally {
      setBusy(null);
    }
  };

  return (
    <div>
      <form
        role="search"
        className="flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          load(q.trim());
        }}
      >
        <label htmlFor="user-search" className="sr-only">Tìm người dùng</label>
        <input
          id="user-search"
          type="search"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Tìm theo tên đăng nhập, tên hiển thị hoặc email"
          className="w-full rounded-lg border border-mist bg-white px-4 py-2.5 focus:border-dusk focus:outline-none focus:ring-2 focus:ring-dusk/15"
        />
        <Button type="submit">Tìm</Button>
      </form>
      {error && <div className="mt-4"><ErrorNote>{error}</ErrorNote></div>}
      {!users ? (
        <PageSpinner />
      ) : users.length === 0 ? (
        <div className="mt-6"><EmptyState title="Không tìm thấy người dùng" /></div>
      ) : (
        <div className="mt-6 overflow-x-auto rounded-xl border border-mist bg-white">
          <table className="w-full min-w-[46rem] text-sm">
            <thead className="border-b border-mist text-left text-ink-soft">
              <tr>
                <th className="px-4 py-3 font-medium">Người dùng</th>
                <th className="px-4 py-3 font-medium">Tham gia</th>
                <th className="px-4 py-3 text-right font-medium">Truyện</th>
                <th className="px-4 py-3 text-right font-medium">Mở chương 24h</th>
                <th className="px-4 py-3 text-right font-medium">Vi phạm</th>
                <th className="px-4 py-3 font-medium">Trạng thái</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-mist">
              {users.map((u) => (
                <tr key={u.id} className={u.is_active ? "" : "bg-rose/[0.03]"}>
                  <td className="px-4 py-3">
                    <Link to={`/nguoi-dung/${u.username}`} className="font-medium text-ink hover:text-dusk">
                      {u.display_name}
                    </Link>
                    <div className="text-[0.8125rem] text-ink-soft">@{u.username}, {u.email}</div>
                  </td>
                  <td className="px-4 py-3 tabular-nums text-ink-soft">{formatDate(u.created_at)}</td>
                  <td className="px-4 py-3 text-right tabular-nums">{u.story_count}</td>
                  <td className="px-4 py-3 text-right tabular-nums">{u.reading_sessions_24h}</td>
                  <td className={`px-4 py-3 text-right tabular-nums ${u.violations ? "font-medium text-rose" : ""}`}>
                    {u.violations}
                  </td>
                  <td className="px-4 py-3">
                    {!u.is_active ? (
                      <span className="rounded-full bg-rose/10 px-2.5 py-0.5 text-xs font-medium text-rose">Bị khoá</span>
                    ) : u.role === "admin" ? (
                      <span className="rounded-full bg-dusk/10 px-2.5 py-0.5 text-xs font-medium text-dusk">Quản trị</span>
                    ) : (
                      <span className="text-ink-soft">Hoạt động</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {u.id !== me.id &&
                      (u.is_active ? (
                        <Button
                          size="sm"
                          variant="danger"
                          disabled={busy === u.id}
                          onClick={() => update(u, { is_active: false }, `Khoá tài khoản @${u.username}? Người này sẽ bị đăng xuất ngay.`)}
                        >
                          Khoá
                        </Button>
                      ) : (
                        <Button size="sm" variant="secondary" disabled={busy === u.id} onClick={() => update(u, { is_active: true })}>
                          Mở khoá
                        </Button>
                      ))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function Security() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const load = useCallback(() => {
    adminApi.security().then(setData).catch((err) => setError(apiError(err)));
  }, []);
  useEffect(() => load(), [load]);

  const unban = async (ip) => {
    await adminApi.unban(ip).catch((err) => setError(apiError(err)));
    load();
  };
  const clear = async (subject) => {
    await adminApi.clearViolations(subject).catch((err) => setError(apiError(err)));
    load();
  };

  if (error) return <ErrorNote>{error}</ErrorNote>;
  if (!data) return <PageSpinner />;

  return (
    <div className="space-y-12">
      <div className="flex justify-end">
        <Button size="sm" variant="secondary" onClick={load}>Tải lại</Button>
      </div>

      <section>
        <h2 className="font-serif text-xl">IP đang bị cấm</h2>
        <p className="mt-1 text-sm text-ink-soft">IP gọi vào đường dẫn bẫy honeypot sẽ bị chặn mọi truy cập trong một thời gian.</p>
        {data.bans.length === 0 ? (
          <p className="mt-4 text-ink-soft">Không có IP nào bị cấm.</p>
        ) : (
          <ul className="mt-4 divide-y divide-mist rounded-xl border border-mist bg-white">
            {data.bans.map((b) => (
              <li key={b.ip} className="flex flex-wrap items-center gap-4 px-5 py-3">
                <span className="font-medium tabular-nums">{b.ip}</span>
                <span className="text-sm text-ink-soft">
                  lý do: {b.reason === "honeypot" ? "dính bẫy honeypot" : b.reason}, còn {Math.ceil(b.expires_in / 60)} phút
                </span>
                <Button size="sm" variant="secondary" className="ml-auto" onClick={() => unban(b.ip)}>
                  Gỡ cấm
                </Button>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2 className="font-serif text-xl">Vi phạm giới hạn truy cập</h2>
        <p className="mt-1 text-sm text-ink-soft">Tài khoản hoặc IP vượt ngưỡng rate limit. Con số cao bất thường thường là bot cào dữ liệu.</p>
        {data.violations.length === 0 ? (
          <p className="mt-4 text-ink-soft">Chưa có vi phạm nào.</p>
        ) : (
          <ul className="mt-4 divide-y divide-mist rounded-xl border border-mist bg-white">
            {data.violations.map((v) => (
              <li key={v.subject} className="flex flex-wrap items-center gap-x-4 gap-y-1 px-5 py-3">
                <span className="w-12 font-serif text-2xl tabular-nums text-rose">{v.total}</span>
                <span className="min-w-0 flex-1">
                  <span className="font-medium">
                    {v.username ? (
                      <Link to={`/nguoi-dung/${v.username}`} className="hover:text-dusk">
                        {v.display_name} (@{v.username})
                      </Link>
                    ) : (
                      v.subject.replace(/^ip:/, "IP ")
                    )}
                  </span>
                  <span className="block text-[0.8125rem] text-ink-soft">
                    {Object.entries(v.by_scope).map(([k, n]) => `${n} lần ${SCOPE_LABEL[k] || k}`).join(", ")}
                  </span>
                </span>
                <Button size="sm" variant="ghost" onClick={() => clear(v.subject)}>Xoá ghi nhận</Button>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2 className="font-serif text-xl">Nhật ký bẫy honeypot</h2>
        {data.honeypot_log.length === 0 ? (
          <p className="mt-4 text-ink-soft">Chưa có ai dính bẫy.</p>
        ) : (
          <ul className="mt-4 divide-y divide-mist rounded-xl border border-mist bg-white text-sm">
            {data.honeypot_log.map((h, i) => (
              <li key={i} className="flex flex-wrap gap-x-4 px-5 py-2.5">
                <span className="tabular-nums text-ink-soft">{formatDateTime(h.at * 1000)}</span>
                <span className="font-medium tabular-nums">{h.ip}</span>
                <span>{h.user_id ? `tài khoản #${h.user_id}` : "chưa đăng nhập"}</span>
                <span className="text-ink-soft" title={h.ua}>{describeBrowser(h.ua)}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2 className="font-serif text-xl">Crawler AI bị chặn</h2>
        {Object.keys(data.bot_hits).length === 0 ? (
          <p className="mt-4 text-ink-soft">Chưa chặn bot nào.</p>
        ) : (
          <dl className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
            {Object.entries(data.bot_hits).map(([bot, n]) => (
              <Stat key={bot} label={bot} value={n} />
            ))}
          </dl>
        )}
      </section>
    </div>
  );
}

export default function AdminPage() {
  const [params, setParams] = useSearchParams();
  const tab = params.get("tab") || "tong-quan";

  return (
    <div className="mx-auto max-w-5xl px-5 py-10 sm:py-14">
      <h1 className="font-serif text-4xl tracking-tight">Quản trị</h1>
      <p className="mt-2 text-ink-soft">Theo dõi hoạt động, quản lý tài khoản và các lớp bảo vệ nội dung.</p>

      <div className="mt-8 flex flex-wrap gap-2 border-b border-mist" role="tablist">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={tab === t.id}
            onClick={() => setParams({ tab: t.id }, { replace: true })}
            className={`-mb-px border-b-2 px-4 py-2.5 text-sm transition-colors ${
              tab === t.id ? "border-dusk font-medium text-dusk" : "border-transparent text-ink-soft hover:text-ink"
            }`}
          >
            {t.label}
          </button>
        ))}
        <Link to="/tac-gia/dao-van" className="-mb-px border-b-2 border-transparent px-4 py-2.5 text-sm text-ink-soft hover:text-ink">
          Cảnh báo đạo văn
        </Link>
      </div>

      <div className="mt-8" role="tabpanel">
        {tab === "tong-quan" && <Overview />}
        {tab === "nguoi-dung" && <Users />}
        {tab === "bao-mat" && <Security />}
      </div>
    </div>
  );
}
