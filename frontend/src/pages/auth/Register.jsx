import { useState } from "react";
import {
  ArrowRight,
  Eye,
  EyeOff,
  LockKeyhole,
  Mail,
  User,
} from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../../context/AuthContext";

export default function Register() {
  const navigate = useNavigate();
  const { register } = useAuth();

  const [form, setForm] = useState({
    fullName: "",
    email: "",
    role: "customer",
    password: "",
    confirmPassword: "",
  });

  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

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

    if (form.password !== form.confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    if (
      !/[a-z]/.test(form.password) ||
      !/[A-Z]/.test(form.password) ||
      !/[0-9]/.test(form.password) ||
      form.password.length < 8
    ) {
      setError(
        "Password must contain at least 8 characters, including uppercase, lowercase and a number.",
      );
      return;
    }

    setSubmitting(true);

    try {
      await register(form);

      navigate("/login", {
        state: {
          message:
            "Account created successfully. Please sign in.",
        },
      });
    } catch (requestError) {
      const detail = requestError.response?.data?.detail;
      let msg = requestError.response?.data?.message;
      if (typeof detail === "string") msg = detail;
      else if (Array.isArray(detail)) msg = detail.map((d) => d.msg).join(". ");

      setError(msg || "Unable to create your account.");
    } finally {

      setSubmitting(false);
    }
  };

  return (
    <section className="auth-page">
      <div className="auth-card">
        <div className="auth-heading">
          <span className="eyebrow">Get started</span>

          <h1>Create your ServiceHub account</h1>

          <p>
            Find trusted providers and manage every booking
            from one place.
          </p>
        </div>

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
            <span>Full name</span>

            <div className="input-with-icon">
              <User size={18} />

              <input
                type="text"
                name="fullName"
                value={form.fullName}
                onChange={updateField}
                placeholder="Ahmed Ali"
                autoComplete="name"
                minLength={2}
                required
              />
            </div>
          </label>

          <label className="form-field">
            <span>Account type</span>

            <select
              name="role"
              value={form.role}
              onChange={updateField}
              required
            >
              <option value="customer">
                Customer
              </option>

              <option value="provider">
                Service provider
              </option>
            </select>
          </label>

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
      placeholder="Minimum 8 characters"
      autoComplete="new-password"
      required
    />

    <button
      type="button"
      className="password-toggle"
      onClick={() => setShowPassword((current) => !current)}
      aria-label={showPassword ? "Hide password" : "Show password"}
      title={showPassword ? "Hide password" : "Show password"}
    >
      {showPassword ? <EyeOff size={19} /> : <Eye size={19} />}
    </button>
  </div>
</label>

          <label className="form-field">
  <span>Confirm password</span>

  <div className="input-with-icon password-input">
    <LockKeyhole size={18} />

    <input
      type={showConfirmPassword ? "text" : "password"}
      name="confirmPassword"
      value={form.confirmPassword}
      onChange={updateField}
      placeholder="Repeat your password"
      autoComplete="new-password"
      required
    />

    <button
      type="button"
      className="password-toggle"
      onClick={() =>
        setShowConfirmPassword((current) => !current)
      }
      aria-label={
        showConfirmPassword
          ? "Hide confirm password"
          : "Show confirm password"
      }
      title={
        showConfirmPassword
          ? "Hide confirm password"
          : "Show confirm password"
      }
    >
      {showConfirmPassword ? (
        <EyeOff size={19} />
      ) : (
        <Eye size={19} />
      )}
    </button>
  </div>
</label>

          <button
            className="button button-full"
            type="submit"
            disabled={submitting}
          >
            {submitting
              ? "Creating account..."
              : "Create account"}

            {!submitting && <ArrowRight size={18} />}
          </button>
        </form>

        <p className="auth-switch">
          Already have an account?{" "}
          <Link to="/login">Sign in</Link>
        </p>
      </div>
    </section>
  );
}