import axios from "axios";

const TOKEN_KEY = "icet_access_token";

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (token) => localStorage.setItem(TOKEN_KEY, token),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

// baseURL "/api": Vite proxy chuyển tiếp sang http://localhost:8000
export const api = axios.create({ baseURL: "/api" });

// Tự gắn access token vào mọi request
api.interceptors.request.use((config) => {
  const token = tokenStore.get();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Access token hết hạn -> đăng xuất (trừ các request tự xử lý 401, như tải đoạn văn)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    const url = error.config?.url || "";
    if (
      status === 401 &&
      tokenStore.get() &&
      !url.includes("/auth/login") &&
      !error.config?.skipAuthLogout
    ) {
      tokenStore.clear();
      window.dispatchEvent(new Event("icet:logout"));
    }
    return Promise.reject(error);
  }
);

const data = (request) => request.then((res) => res.data);

// Gửi file dạng multipart/form-data (trình duyệt tự đặt Content-Type kèm boundary)
const fileForm = (file) => {
  const form = new FormData();
  form.append("file", file);
  return form;
};

export const authApi = {
  login: (identifier, password) =>
    data(api.post("/auth/login", new URLSearchParams({ username: identifier, password }))),
  register: (payload) => data(api.post("/auth/register", payload)),
  me: () => data(api.get("/auth/me")),
};

export const storyApi = {
  /** filters: { q, genre, status, sort } */
  list: (skip = 0, limit = 12, filters = {}) =>
    data(api.get("/stories", { params: { skip, limit, ...filters } })),
  mine: () => data(api.get("/stories/mine")),
  get: (storyId) => data(api.get(`/stories/${storyId}`)),
  create: (payload) => data(api.post("/stories", payload)),
  update: (storyId, payload) => data(api.patch(`/stories/${storyId}`, payload)),
  remove: (storyId) => api.delete(`/stories/${storyId}`),
  uploadCover: (storyId, file) => data(api.put(`/stories/${storyId}/cover`, fileForm(file))),
  removeCover: (storyId) => data(api.delete(`/stories/${storyId}/cover`)),
};

export const chapterApi = {
  toc: (storyId) => data(api.get(`/stories/${storyId}/chapters`)),
  manage: (storyId) => data(api.get(`/stories/${storyId}/chapters/manage`)),
  create: (storyId, payload) => data(api.post(`/stories/${storyId}/chapters`, payload)),
  getForEdit: (storyId, chapterId) =>
    data(api.get(`/stories/${storyId}/chapters/${chapterId}/edit`)),
  update: (storyId, chapterId, payload) =>
    data(api.patch(`/stories/${storyId}/chapters/${chapterId}`, payload)),
  remove: (storyId, chapterId) => api.delete(`/stories/${storyId}/chapters/${chapterId}`),
};

export const readingApi = {
  openSession: (storyId, chapterId) =>
    data(api.post(`/stories/${storyId}/chapters/${chapterId}/session`)),
  paragraphs: (storyId, chapterId, readToken, start, limit) =>
    data(
      api.get(`/stories/${storyId}/chapters/${chapterId}/paragraphs`, {
        params: { start, limit },
        headers: { "X-Read-Token": readToken },
        skipAuthLogout: true, // trang đọc tự xử lý 401 (xin vé đọc mới)
      })
    ),
};

export const traceApi = {
  trace: (text) => data(api.post("/trace", { text })),
};

export const plagiarismApi = {
  reports: (status) => data(api.get("/plagiarism/reports", { params: status ? { status } : {} })),
  setStatus: (reportId, status) => data(api.patch(`/plagiarism/reports/${reportId}`, { status })),
  reindex: () => data(api.post("/plagiarism/reindex")),
};

export const genreApi = {
  list: () => data(api.get("/genres")),
};

export const commentApi = {
  list: (storyId, chapterId) => data(api.get(`/stories/${storyId}/chapters/${chapterId}/comments`)),
  add: (storyId, chapterId, content, parentId = null) =>
    data(
      api.post(`/stories/${storyId}/chapters/${chapterId}/comments`, {
        content,
        parent_id: parentId,
      })
    ),
  edit: (storyId, chapterId, commentId, content) =>
    data(api.patch(`/stories/${storyId}/chapters/${chapterId}/comments/${commentId}`, { content })),
  remove: (storyId, chapterId, commentId) =>
    data(api.delete(`/stories/${storyId}/chapters/${chapterId}/comments/${commentId}`)),
};

export const ratingApi = {
  summary: (storyId) => data(api.get(`/stories/${storyId}/ratings`)),
  rate: (storyId, score, review) => data(api.put(`/stories/${storyId}/ratings/me`, { score, review })),
  remove: (storyId) => api.delete(`/stories/${storyId}/ratings/me`),
};

export const followApi = {
  follow: (storyId) => data(api.post(`/stories/${storyId}/follow`)),
  unfollow: (storyId) => data(api.delete(`/stories/${storyId}/follow`)),
  mine: () => data(api.get("/me/following")),
};

export const notificationApi = {
  list: () => data(api.get("/notifications")),
  unreadCount: () => data(api.get("/notifications/unread-count")).then((r) => r.count),
  read: (id) => api.post(`/notifications/${id}/read`),
  readAll: () => api.post("/notifications/read-all"),
};

export const userApi = {
  profile: (username) => data(api.get(`/users/${encodeURIComponent(username)}`)),
  uploadAvatar: (file) => data(api.put("/users/me/avatar", fileForm(file))),
  removeAvatar: () => data(api.delete("/users/me/avatar")),
};

export const adminApi = {
  overview: () => data(api.get("/admin/overview")),
  users: (q) => data(api.get("/admin/users", { params: q ? { q } : {} })),
  updateUser: (id, payload) => data(api.patch(`/admin/users/${id}`, payload)),
  security: () => data(api.get("/admin/security")),
  unban: (ip) => api.delete(`/admin/security/bans/${encodeURIComponent(ip)}`),
  clearViolations: (subject) => api.delete(`/admin/security/violations/${encodeURIComponent(subject)}`),
};
