import { useState } from "react";
import {
  ArrowRight,
  LockKeyhole,
  Mail,
  ShieldCheck,
} from "lucide-react";
import {
  Navigate,
  useLocation,
  useNavigate,
} from "react-router-dom";

import { useAuth } from "../../context/AuthContext";

export default function AdminLogin() {
  const navigate = useNavigate();
  const location = useLocation();
  const {
    login,
    logout,
    user,
    loading,
    isAuthenticated,
  } = useAuth();

  const [form, setForm] = useState({
    email: "",
    password: "",
  });

  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (!loading && isAuthenticated && user?.role === "admin") {
    return <Navigate to="/admin" replace />;
  }

  const updateField = (event) => {
    const { name, value } = event.target;

    setForm((current) => ({
      ...current,
      [name]: value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setSubmitting(true);

    try {
      const currentUser = await login(
        form.email,
        form.password,
      );

      if (currentUser?.role !== "admin") {
        logout();
        setError(
          "Access denied. This account is not an administrator account.",
        );
        return;
      }

      const requestedPath =
        location.state?.from?.pathname;

      navigate(
        requestedPath?.startsWith("/admin")
          ? requestedPath
          : "/admin",
        { replace: true },
      );
    } catch (requestError) {
      setError(
        requestError.response?.data?.message ||
          requestError.response?.data?.detail ||
          "Invalid administrator email or password.",
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="admin-login-page">
      <section className="admin-login-card">
        <div className="admin-login-icon">
          <ShieldCheck size={32} />
        </div>

        <span className="eyebrow">
          Restricted access
        </span>

        <h1>Administrator sign in</h1>

        <p className="admin-login-description">
          Sign in to review provider applications and
          manage the ServiceHub platform.
        </p>

        {error && (
          <div className="alert alert-error">
            {error}
          </div>
        )}

        <form
          className="auth-form"
          onSubmit={handleSubmit}
        >
          <label className="form-field">
            <span>Administrator email</span>

            <div className="input-with-icon">
              <Mail size={18} />

              <input
                type="email"
                name="email"
                value={form.email}
                onChange={updateField}
                placeholder="admin@example.com"
                autoComplete="email"
                required
              />
            </div>
          </label>

          <label className="form-field">
            <span>Password</span>

            <div className="input-with-icon">
              <LockKeyhole size={18} />

              <input
                type="password"
                name="password"
                value={form.password}
                onChange={updateField}
                placeholder="Enter your password"
                autoComplete="current-password"
                required
              />
            </div>
          </label>

          <button
            type="submit"
            className="button button-full"
            disabled={submitting}
          >
            {submitting
              ? "Checking access..."
              : "Sign in as administrator"}

            {!submitting && <ArrowRight size={18} />}
          </button>
        </form>

        <p className="admin-security-note">
          Provider passwords are never displayed or
          available to administrators.
        </p>
      </section>
    </main>
  );
}