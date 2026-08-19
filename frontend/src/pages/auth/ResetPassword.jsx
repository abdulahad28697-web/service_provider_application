import { useState } from "react";
import {
  ArrowRight,
  CheckCircle2,
  Eye,
  EyeOff,
  KeyRound,
  LockKeyhole,
} from "lucide-react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import api from "../../api/api";

export default function ResetPassword() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const tokenFromUrl = searchParams.get("token") || "";

  const [form, setForm] = useState({
    resetToken: tokenFromUrl,
    newPassword: "",
    confirmPassword: "",
  });

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
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

    if (!form.resetToken.trim()) {
      setError("Please provide a valid password reset token.");
      return;
    }

    if (form.newPassword !== form.confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    if (
      !/[a-z]/.test(form.newPassword) ||
      !/[A-Z]/.test(form.newPassword) ||
      !/[0-9]/.test(form.newPassword) ||
      form.newPassword.length < 8
    ) {
      setError(
        "Password must contain at least 8 characters, including uppercase, lowercase letters and a number.",
      );
      return;
    }

    setSubmitting(true);

    try {
      await api.post("/auth/reset-password", {
        reset_token: form.resetToken.trim(),
        new_password: form.newPassword,
      });

      navigate("/login", {
        state: {
          message: "Password reset successful! You can now log in with your new password.",
        },
      });
    } catch (requestError) {
      setError(
        requestError.response?.data?.message ||
          requestError.response?.data?.detail ||
          "The reset link or token is invalid or has expired.",
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="auth-page">
      <div className="auth-card">
        <div className="auth-heading">
          <span className="eyebrow">Secure Account</span>
          <h1>Set New Password</h1>
          <p>
            Create and confirm your new password to approve account recovery.
          </p>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        <form className="auth-form" onSubmit={handleSubmit}>
          <label className="form-field">
            <span>Verification Token</span>
            <div className="input-with-icon">
              <KeyRound size={18} />
              <input
                type="text"
                name="resetToken"
                value={form.resetToken}
                onChange={updateField}
                placeholder="Paste reset token from email"
                required
              />
            </div>
          </label>

          <label className="form-field">
            <span>New password</span>
            <div className="input-with-icon password-input">
              <LockKeyhole size={18} />
              <input
                type={showPassword ? "text" : "password"}
                name="newPassword"
                value={form.newPassword}
                onChange={updateField}
                placeholder="At least 8 characters"
                autoComplete="new-password"
                required
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword((curr) => !curr)}
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </label>

          <label className="form-field">
            <span>Confirm new password</span>
            <div className="input-with-icon password-input">
              <LockKeyhole size={18} />
              <input
                type={showConfirmPassword ? "text" : "password"}
                name="confirmPassword"
                value={form.confirmPassword}
                onChange={updateField}
                placeholder="Re-enter your new password"
                autoComplete="new-password"
                required
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowConfirmPassword((curr) => !curr)}
                aria-label={showConfirmPassword ? "Hide password" : "Show password"}
              >
                {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </label>

          <button
            type="submit"
            className="button button-full"
            disabled={submitting}
          >
            {submitting ? "Updating password..." : "Confirm & Reset Password"}
            {!submitting && <ArrowRight size={18} />}
          </button>
        </form>

        <p className="auth-switch">
          <Link to="/login">Return to sign in</Link>
        </p>
      </div>
    </section>
  );
}