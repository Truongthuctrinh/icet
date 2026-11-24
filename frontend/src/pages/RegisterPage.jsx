import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router";
import { Button, ErrorNote, Field } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { apiError } from "../utils/format";

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState({ display_name: "", username: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const update = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await register({
        ...form,
        display_name: form.display_name.trim(),
        username: form.username.trim(),
        email: form.email.trim(),
      });
      navigate(location.state?.from || "/tac-gia", { replace: true });
    } catch (err) {
      setError(apiError(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-sm px-5 py-16">
      <h1 className="font-serif text-3xl">Tạo tài khoản</h1>
      <p className="mt-2 text-ink-soft">Một tài khoản để vừa đọc vừa viết truyện.</p>

      <form onSubmit={handleSubmit} className="mt-8 space-y-5">
        <Field
          id="display_name"
          label="Tên hiển thị"
          hint="Tên độc giả thấy trên truyện của bạn. Có thể là bút danh."
          value={form.display_name}
          onChange={update("display_name")}
          maxLength={100}
          required
        />
        <Field
          id="username"
          label="Tên đăng nhập"
          hint="Từ 3 ký tự, chỉ gồm chữ không dấu, số và dấu gạch dưới."
          autoComplete="username"
          value={form.username}
          onChange={update("username")}
          pattern="[A-Za-z0-9_]{3,50}"
          required
        />
        <Field
          id="email"
          label="Email"
          type="email"
          autoComplete="email"
          value={form.email}
          onChange={update("email")}
          required
        />
        <Field
          id="password"
          label="Mật khẩu"
          type="password"
          hint="Ít nhất 8 ký tự."
          autoComplete="new-password"
          value={form.password}
          onChange={update("password")}
          minLength={8}
          required
        />
        {error && <ErrorNote>{error}</ErrorNote>}
        <Button type="submit" className="w-full" disabled={submitting}>
          {submitting ? "Đang tạo tài khoản…" : "Tạo tài khoản"}
        </Button>
      </form>

      <p className="mt-6 text-sm text-ink-soft">
        Đã có tài khoản?{" "}
        <Link to="/dang-nhap" state={location.state} className="font-medium text-dusk hover:underline">
          Đăng nhập
        </Link>
      </p>
    </div>
  );
}
