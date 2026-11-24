import { Navigate, useLocation } from "react-router";
import { useAuth } from "../context/AuthContext";
import { PageSpinner } from "./ui";

/** Bọc các trang cần đăng nhập. Chưa đăng nhập -> chuyển sang /dang-nhap rồi quay lại. */
export default function RequireAuth({ children }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) return <PageSpinner />;
  if (!user) return <Navigate to="/dang-nhap" state={{ from: location.pathname }} replace />;
  return children;
}
