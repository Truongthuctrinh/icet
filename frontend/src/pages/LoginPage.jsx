import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router";
import { Button, ErrorNote, Field } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { apiError } from "../utils/format";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState({ identifier: "", password: "" });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const update = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await login(form.identifier.trim(), form.password);
      navigate(location.state?.from || "/", { replace: true });
    } catch (err) {
      setError(apiError(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-sm px-5 py-16">
      <h1 className="font-serif text-3xl">Đăng nhập</h1>
      {location.state?.from && (
        <p className="mt-2 text-ink-soft">Đăng nhập để đọc chương và theo dõi truyện.</p>
      )}

      <form onSubmit={handleSubmit} className="mt-8 space-y-5">
        <Field
          id="identifier"
          label="Tên đăng nhập hoặc email"
          autoComplete="username"
          value={form.identifier}
          onChange={update("identifier")}
          required
        />
        <Field
          id="password"
          label="Mật khẩu"
          type="password"
          autoComplete="current-password"
          value={form.password}
          onChange={update("password")}
          required
        />
        {error && <ErrorNote>{error}</ErrorNote>}
        <Button type="submit" className="w-full" disabled={submitting}>
          {submitting ? "Đang đăng nhập…" : "Đăng nhập"}
        </Button>
      </form>

      <p className="mt-6 text-sm text-ink-soft">
        Chưa có tài khoản?{" "}
        <Link to="/dang-ky" state={location.state} className="font-medium text-dusk hover:underline">
          Đăng ký
        </Link>
      </p>
    </div>
  );
}
