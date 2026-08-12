import { useState } from "react";
import {
  ArrowRight,
  KeyRound,
  LockKeyhole,
} from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

import api from "../../api/api";

export default function ResetPassword() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    resetToken: "",
    newPassword: "",
    confirmPassword: "",
  });

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

    if (form.newPassword !== form.confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setSubmitting(true);

    try {
      await api.post("/auth/reset-password", {
        reset_token: form.resetToken.trim(),
        new_password: form.newPassword,
      });

      navigate("/login");
    } catch (requestError) {
      setError(
        requestError.response?.data?.message ||
          "The reset token is invalid or expired.",
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="auth-page">
      <div className="auth-card">
        <div className="auth-heading">
          <span className="eyebrow">Secure account</span>
          <h1>Create a new password</h1>
          <p>
            Enter your reset token and choose a strong new
            password.
          </p>
        </div>

        {error && (
          <div className="alert alert-error">{error}</div>
        )}

        <form
          className="auth-form"
          onSubmit={handleSubmit}
        >
          <label className="form-field">
            <span>Reset token</span>
            <div className="input-with-icon">
              <KeyRound size={18} />
              <input
                type="text"
                name="resetToken"
                value={form.resetToken}
                onChange={updateField}
                placeholder="Paste your reset token"
                required
              />
            </div>
          </label>

          <label className="form-field">
            <span>New password</span>
            <div className="input-with-icon">
              <LockKeyhole size={18} />
              <input
                type="password"
                name="newPassword"
                value={form.newPassword}
                onChange={updateField}
                placeholder="Minimum 8 characters"
                required
              />
            </div>
          </label>

          <label className="form-field">
            <span>Confirm password</span>
            <div className="input-with-icon">
              <LockKeyhole size={18} />
              <input
                type="password"
                name="confirmPassword"
                value={form.confirmPassword}
                onChange={updateField}
                placeholder="Repeat your password"
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
              ? "Updating..."
              : "Reset password"}
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