import { BrowserRouter, Route, Routes } from "react-router";
import Layout from "./components/Layout";
import RequireAuth from "./components/RequireAuth";
import { AuthProvider } from "./context/AuthContext";
import HomePage from "./pages/HomePage";
import LoginPage from "./pages/LoginPage";
import NotFoundPage from "./pages/NotFoundPage";
import ReaderPage from "./pages/ReaderPage";
import RegisterPage from "./pages/RegisterPage";
import StoryPage from "./pages/StoryPage";
import AuthorDashboard from "./pages/author/AuthorDashboard";
import ChapterEditorPage from "./pages/author/ChapterEditorPage";
import ManageStoryPage from "./pages/author/ManageStoryPage";
import StoryFormPage from "./pages/author/StoryFormPage";
import TracePage from "./pages/author/TracePage";

const authed = (page) => <RequireAuth>{page}</RequireAuth>;

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route element={<Layout />}>
            {/* Người đọc */}
            <Route index element={<HomePage />} />
            <Route path="dang-nhap" element={<LoginPage />} />
            <Route path="dang-ky" element={<RegisterPage />} />
            <Route path="truyen/:storyId" element={<StoryPage />} />
            <Route path="truyen/:storyId/chuong/:chapterId" element={authed(<ReaderPage />)} />

            {/* Góc tác giả */}
            <Route path="tac-gia" element={authed(<AuthorDashboard />)} />
            <Route path="tac-gia/truy-vet" element={authed(<TracePage />)} />
            <Route path="tac-gia/truyen-moi" element={authed(<StoryFormPage />)} />
            <Route path="tac-gia/truyen/:storyId" element={authed(<ManageStoryPage />)} />
            <Route path="tac-gia/truyen/:storyId/sua" element={authed(<StoryFormPage />)} />
            <Route path="tac-gia/truyen/:storyId/chuong-moi" element={authed(<ChapterEditorPage />)} />
            <Route
              path="tac-gia/truyen/:storyId/chuong/:chapterId/sua"
              element={authed(<ChapterEditorPage />)}
            />

            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
