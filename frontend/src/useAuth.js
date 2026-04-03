import { useCallback, useEffect, useState } from "react";
import api from "./api/api.js";

export function useAuth() {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Проверяем сессию при загрузке приложения
  const checkAuth = useCallback(async () => {
    try {
      const res = await api.get("/auth/user/");
      setUser(res.data);
      setIsAuthenticated(true);
    } catch {
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);  

  useEffect(() => {
    const handlePageShow = (e) => {
      if (e.persisted) checkAuth();
    };
    window.addEventListener("pageshow", handlePageShow);
    return () => window.removeEventListener("pageshow", handlePageShow);
  }, [checkAuth]);

  const login = useCallback(async (email, password) => {
    const res = await api.post("/auth/login/", { email, password });
    setUser(res.data.user);
    setIsAuthenticated(true);
    return res.data;
  }, []);

  const logout = useCallback(async () => {
    await api.post("/auth/logout/");
    setUser(null);
    setIsAuthenticated(false);
  }, []);

  return { user, isAuthenticated, isLoading, login, logout };
}
