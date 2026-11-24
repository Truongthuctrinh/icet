import { Link } from "react-router";
import { STATUS_LABELS } from "../utils/format";

const BUTTON_BASE =
  "inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-colors disabled:pointer-events-none disabled:opacity-50";

const BUTTON_VARIANTS = {
  primary: "bg-dusk text-white hover:bg-dusk-deep",
  secondary: "border border-mist bg-white text-ink hover:border-dusk/40 hover:text-dusk",
  ghost: "text-ink-soft hover:text-dusk",
  danger: "border border-rose/30 bg-white text-rose hover:bg-rose hover:text-white",
};

const BUTTON_SIZES = {
  md: "",
  sm: "px-3 py-1.5 text-[0.8125rem]",
};

/** Nút dùng chung. Có `to` -> thành Link, có `href` -> thành thẻ a. */
export function Button({ variant = "primary", size = "md", to, href, className = "", ...props }) {
  const cls = `${BUTTON_BASE} ${BUTTON_VARIANTS[variant]} ${BUTTON_SIZES[size]} ${className}`;
  if (to) return <Link to={to} className={cls} {...props} />;
  if (href) return <a href={href} className={cls} {...props} />;
  return <button type="button" className={cls} {...props} />;
}

const INPUT_CLASS =
  "w-full rounded-lg border border-mist bg-white px-3.5 py-2.5 text-ink placeholder:text-ink-soft/60 focus:border-dusk focus:outline-none focus:ring-2 focus:ring-dusk/15";

/** Ô nhập có nhãn, gợi ý và lỗi. as="textarea" | "select" để đổi loại. */
export function Field({ label, hint, id, as: Component = "input", className = "", children, ...props }) {
  return (
    <div className={className}>
      <label htmlFor={id} className="mb-1.5 block text-sm font-medium text-ink">
        {label}
      </label>
      <Component id={id} className={INPUT_CLASS} {...props}>
        {children}
      </Component>
      {hint && <p className="mt-1.5 text-[0.8125rem] text-ink-soft">{hint}</p>}
    </div>
  );
}

export function Spinner({ className = "" }) {
  return (
    <span
      role="status"
      aria-label="Đang tải"
      className={`inline-block h-4 w-4 animate-spin rounded-full border-2 border-dusk/25 border-t-dusk ${className}`}
    />
  );
}

export function PageSpinner() {
  return (
    <div className="flex justify-center py-24">
      <Spinner className="h-6 w-6" />
    </div>
  );
}

export function ErrorNote({ children }) {
  return (
    <p role="alert" className="rounded-lg border border-rose/25 bg-rose/5 px-4 py-3 text-sm text-rose">
      {children}
    </p>
  );
}

export function EmptyState({ title, children, action }) {
  return (
    <div className="rounded-xl border border-dashed border-mist px-6 py-14 text-center">
      <p className="font-serif text-xl text-ink">{title}</p>
      {children && <p className="mx-auto mt-2 max-w-md text-ink-soft">{children}</p>}
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
}

export function StatusBadge({ status }) {
  return (
    <span className="inline-flex items-center rounded-full bg-mist/70 px-2.5 py-0.5 text-xs font-medium text-ink-soft">
      {STATUS_LABELS[status] || status}
    </span>
  );
}

export function PublishBadge({ published }) {
  return published ? (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-sage/10 px-2.5 py-0.5 text-xs font-medium text-sage">
      <span className="h-1.5 w-1.5 rounded-full bg-sage" />
      Đã xuất bản
    </span>
  ) : (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-mist px-2.5 py-0.5 text-xs font-medium text-ink-soft">
      <span className="h-1.5 w-1.5 rounded-full border border-ink-soft/60" />
      Bản nháp
    </span>
  );
}

export function BackLink({ to, children }) {
  return (
    <Link to={to} className="text-sm text-ink-soft hover:text-dusk">
      ‹ {children}
    </Link>
  );
}
