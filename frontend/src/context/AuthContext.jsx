import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { authApi, tokenStore } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Mở web: nếu còn token thì hỏi backend xem token còn hợp lệ không
  useEffect(() => {
    if (!tokenStore.get()) {
      setLoading(false);
      return;
    }
    authApi
      .me()
      .then(setUser)
      .catch(() => tokenStore.clear())
      .finally(() => setLoading(false));
  }, []);

  // Token hết hạn ở bất kỳ request nào -> client.js phát sự kiện này
  useEffect(() => {
    const onLogout = () => setUser(null);
    window.addEventListener("icet:logout", onLogout);
    return () => window.removeEventListener("icet:logout", onLogout);
  }, []);

  const login = useCallback(async (identifier, password) => {
    const { access_token } = await authApi.login(identifier, password);
    tokenStore.set(access_token);
    const me = await authApi.me();
    setUser(me);
    return me;
  }, []);

  const register = useCallback(
    async (payload) => {
      await authApi.register(payload);
      return login(payload.username, payload.password);
    },
    [login]
  );

  const logout = useCallback(() => {
    tokenStore.clear();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, loading, login, register, logout }),
    [user, loading, login, register, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
