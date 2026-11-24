import { Link, NavLink, Outlet, useNavigate } from "react-router";
import { useAuth } from "../context/AuthContext";
import { Button } from "./ui";

const navClass = ({ isActive }) =>
  `text-sm ${isActive ? "text-dusk font-medium" : "text-ink-soft hover:text-ink"}`;

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-mist bg-paper/90 backdrop-blur">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-x-6 gap-y-3 px-5 py-4">
          <Link to="/" className="flex items-baseline gap-1.5" aria-label="ICeT, về trang chủ">
            <span className="font-serif text-[1.65rem] font-semibold leading-none tracking-tight">
              ICeT
            </span>
            <span className="text-marigold" aria-hidden="true">✦</span>
          </Link>

          <nav className="flex flex-wrap items-center gap-x-5 gap-y-2">
            <NavLink to="/" end className={navClass}>
              Truyện
            </NavLink>
            {user ? (
              <>
                <NavLink to="/tac-gia" className={navClass}>
                  Góc tác giả
                </NavLink>
                <span className="text-sm text-ink">{user.display_name}</span>
                <Button variant="secondary" size="sm" onClick={handleLogout}>
                  Đăng xuất
                </Button>
              </>
            ) : (
              <>
                <NavLink to="/dang-nhap" className={navClass}>
                  Đăng nhập
                </NavLink>
                <Button to="/dang-ky" size="sm">
                  Đăng ký
                </Button>
              </>
            )}
          </nav>
        </div>
      </header>

      <main className="flex-1">
        <Outlet />
      </main>

      <footer className="border-t border-mist">
        <div className="mx-auto max-w-5xl px-5 py-8 text-sm text-ink-soft">
          ICeT, Imagine Come True. Nơi người viết nghiệp dư chia sẻ truyện chữ.
        </div>
      </footer>
    </div>
  );
}
