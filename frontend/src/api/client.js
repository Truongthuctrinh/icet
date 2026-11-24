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

export const authApi = {
  login: (identifier, password) =>
    data(api.post("/auth/login", new URLSearchParams({ username: identifier, password }))),
  register: (payload) => data(api.post("/auth/register", payload)),
  me: () => data(api.get("/auth/me")),
};

export const storyApi = {
  list: (skip = 0, limit = 12) => data(api.get("/stories", { params: { skip, limit } })),
  mine: () => data(api.get("/stories/mine")),
  get: (storyId) => data(api.get(`/stories/${storyId}`)),
  create: (payload) => data(api.post("/stories", payload)),
  update: (storyId, payload) => data(api.patch(`/stories/${storyId}`, payload)),
  remove: (storyId) => api.delete(`/stories/${storyId}`),
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
