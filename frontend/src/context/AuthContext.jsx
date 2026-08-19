import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import api from "../api/api";

const AuthContext = createContext(null);

export function normalizeUser(rawUser) {
  if (!rawUser || typeof rawUser !== "object") {
    return null;
  }

  const idVal = rawUser.id ?? rawUser.user_id ?? null;
  const roleVal =
    typeof rawUser.role === "string"
      ? rawUser.role.toLowerCase()
      : rawUser.role?.value
        ? String(rawUser.role.value).toLowerCase()
        : String(rawUser.role || "customer").toLowerCase();

  return {
    ...rawUser,
    id: idVal,
    user_id: rawUser.user_id ?? idVal,
    role: roleVal,
  };
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const token = localStorage.getItem("access_token");
    if (!token) return null;

    const storedUser = localStorage.getItem("current_user");
    try {
      return storedUser ? normalizeUser(JSON.parse(storedUser)) : null;
    } catch {
      return null;
    }
  });

  const [loading, setLoading] = useState(() => {
    const token = localStorage.getItem("access_token");
    const storedUser = localStorage.getItem("current_user");
    // If we already have token and stored user, we don't block initial render
    return Boolean(token && !storedUser);
  });

  const fetchCurrentUser = useCallback(async () => {
    const token = localStorage.getItem("access_token");

    if (!token) {
      setUser(null);
      setLoading(false);
      return null;
    }

    try {
      const response = await api.get("/users/me");
      const currentUser = normalizeUser(response.data.data);

      setUser(currentUser);
      localStorage.setItem(
        "current_user",
        JSON.stringify(currentUser),
      );

      return currentUser;
    } catch (error) {
      // Only wipe session if server explicitly returns 401 Unauthorized
      if (error.response?.status === 401) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("current_user");
        setUser(null);
        return null;
      }

      // If it's a network glitch or server reload, retain cached user if present
      const stored = localStorage.getItem("current_user");
      if (stored) {
        try {
          const cached = normalizeUser(JSON.parse(stored));
          setUser(cached);
          return cached;
        } catch {
          // ignore JSON parse error
        }
      }

      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCurrentUser();

    const handleFocus = () => {
      const token = localStorage.getItem("access_token");
      if (token) {
        fetchCurrentUser();
      }
    };

    window.addEventListener("focus", handleFocus);
    return () => window.removeEventListener("focus", handleFocus);
  }, [fetchCurrentUser]);

  const login = useCallback(
    async (email, password) => {
      const response = await api.post("/auth/login", {
        email: email.trim().toLowerCase(),
        password,
      });

      const tokenData = response.data.data;

      localStorage.setItem(
        "access_token",
        tokenData.access_token,
      );

      return fetchCurrentUser();
    },
    [fetchCurrentUser],
  );

  const register = useCallback(
    async ({
      fullName,
      email,
      password,
      role = "customer",
    }) => {
      return api.post("/auth/register", {
        full_name: fullName.trim(),
        email: email.trim().toLowerCase(),
        password,
        role,
      });
    },
    [],
  );

  const logout = useCallback(() => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("current_user");
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({
      user,
      loading,
      isAuthenticated: Boolean(user),
      login,
      register,
      logout,
      refreshUser: fetchCurrentUser,
    }),
    [
      user,
      loading,
      login,
      register,
      logout,
      fetchCurrentUser,
    ],
  );

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth must be used inside AuthProvider.",
    );
  }

  return context;
}