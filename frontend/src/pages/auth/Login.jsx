import { useState } from "react";
import {
  ArrowRight,
  Eye,
  EyeOff,
  LockKeyhole,
  Mail,
  ShieldCheck,
} from "lucide-react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../../context/AuthContext";

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();

  const [form, setForm] = useState({
    email: "",
    password: "",
  });

  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

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
      const user = await login(form.email, form.password);

      if (user?.role?.toLowerCase() === "admin") {
        navigate("/admin");
      } else if (user?.role?.toLowerCase() === "provider") {
        navigate("/provider");
      } else {
        navigate("/");
      }
    } catch (requestError) {
      const detail = requestError.response?.data?.detail;
      let msg = requestError.response?.data?.message;
      if (typeof detail === "string") msg = detail;
      else if (Array.isArray(detail)) msg = detail.map((d) => d.msg).join(". ");

      setError(msg || "Invalid email or password.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="auth-page">
      <div className="auth-card">
        <span className="eyebrow">Welcome back</span>

        <h1>Sign in to ServiceHub</h1>

        <p>
          Manage bookings and connect with trusted professionals.
        </p>

        {location.state?.message && (
          <div className="alert alert-success">
            {location.state.message}
          </div>
        )}

        {error && (
          <div className="alert alert-error">{error}</div>
        )}

        <form className="auth-form" onSubmit={handleSubmit}>
          <label className="form-field">
            <span>Email address</span>

            <div className="input-with-icon">
              <Mail size={18} />

              <input
                type="email"
                name="email"
                value={form.email}
                onChange={updateField}
                placeholder="you@example.com"
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
                placeholder="Enter your password"
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

          <div className="form-options">
            <Link to="/forgot-password">
              Forgot password?
            </Link>
          </div>

          <button
            className="button button-full"
            type="submit"
            disabled={submitting}
          >
            {submitting ? "Signing in..." : "Sign in"}
            {!submitting && <ArrowRight size={18} />}
          </button>
        </form>

        <div className="auth-admin-switch">
          <span>Platform Administrator?</span>
          <Link to="/admin/login" className="admin-portal-link">
            <ShieldCheck size={16} />
            Sign in to Admin Portal
          </Link>
        </div>

        <p className="auth-switch">
          New to ServiceHub?{" "}
          <Link to="/register">Create an account</Link>
        </p>
      </div>
    </section>
  );
}