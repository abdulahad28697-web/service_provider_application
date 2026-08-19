import { useState } from "react";
import {
  ArrowRight,
  Eye,
  EyeOff,
  LockKeyhole,
  Mail,
  ShieldCheck,
  UserRound,
} from "lucide-react";
import {
  Link,
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

  const [showPassword, setShowPassword] = useState(false);
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
          "Access denied. This account does not have administrator privileges.",
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
      const detail = requestError.response?.data?.detail;
      let msg = requestError.response?.data?.message;
      if (typeof detail === "string") msg = detail;
      else if (Array.isArray(detail)) msg = detail.map((d) => d.msg).join(". ");

      setError(msg || "Invalid administrator email or password.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="admin-login-page">
      <section className="admin-login-card">
        <div className="admin-login-icon">
          <ShieldCheck size={36} />
        </div>

        <span className="eyebrow">
          Secure portal
        </span>

        <h1>Administrator Sign In</h1>

        <p className="admin-login-description">
          Sign in to review provider applications, verify businesses, and manage
          platform operations.
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
                placeholder="admin@gmail.com"
                autoComplete="email"
                required
              />
            </div>
          </label>

          <label className="form-field">
            <span>Password</span>

            <div className="input-with-icon password-input">
              <LockKeyhole size={18} />

              <input
                type={showPassword ? "text" : "password"}
                name="password"
                value={form.password}
                onChange={updateField}
                placeholder="Enter admin password"
                autoComplete="current-password"
                required
              />

              <button
                type="button"
                className="password-toggle"
                onClick={() =>
                  setShowPassword((current) => !current)
                }
                aria-label={
                  showPassword ? "Hide password" : "Show password"
                }
                title={
                  showPassword ? "Hide password" : "Show password"
                }
              >
                {showPassword ? (
                  <EyeOff size={19} />
                ) : (
                  <Eye size={19} />
                )}
              </button>
            </div>
          </label>

          <button
            type="submit"
            className="button button-full button-admin-submit"
            disabled={submitting}
          >
            {submitting
              ? "Checking access..."
              : "Sign in to Admin Dashboard"}

            {!submitting && <ArrowRight size={18} />}
          </button>
        </form>

        <div className="admin-login-footer-links">
          <Link to="/login" className="admin-back-standard-link">
            <UserRound size={16} />
            Customer or Provider Sign In
          </Link>
        </div>

        <p className="admin-security-note">
          Protected administrative portal. All actions are logged in the audit trail.
        </p>
      </section>
    </main>
  );
}