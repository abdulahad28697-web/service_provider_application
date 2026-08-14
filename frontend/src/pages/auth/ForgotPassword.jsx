import { useState } from "react";
import { ArrowRight, Mail } from "lucide-react";
import { Link } from "react-router-dom";

import api from "../../api/api";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setMessage("");
    setResetToken("");
    setSubmitting(true);

    try {
      const response = await api.post(
        "/auth/forgot-password",
        {
          email: email.trim().toLowerCase(),
        },
      );

      setMessage(
        response.data.message ||
          "Password reset instructions generated.",
      );

      if (response.data.data?.reset_token) {
        setResetToken(response.data.data.reset_token);
      }
    } catch (requestError) {
      setError(
        requestError.response?.data?.message ||
          "Unable to request a password reset.",
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="auth-page">
      <div className="auth-card">
        <div className="auth-heading">
          <span className="eyebrow">Account recovery</span>
          <h1>Forgot your password?</h1>
          <p>
            Enter your registered email address to request a
            password-reset token.
          </p>
        </div>

        {error && (
          <div className="alert alert-error">{error}</div>
        )}

        {message && (
          <div className="alert alert-success">
            {message}
          </div>
        )}

        {resetToken && (
          <div className="token-box">
            <span>Development reset token</span>
            <code>{resetToken}</code>
            <Link to="/reset-password">
              Continue to reset password
            </Link>
          </div>
        )}

        <form
          className="auth-form"
          onSubmit={handleSubmit}
        >
          <label className="form-field">
            <span>Email address</span>

            <div className="input-with-icon">
              <Mail size={18} />
              <input
                type="email"
                value={email}
                onChange={(event) =>
                  setEmail(event.target.value)
                }
                placeholder="you@example.com"
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
              ? "Requesting..."
              : "Request reset token"}
            {!submitting && <ArrowRight size={18} />}
          </button>
        </form>

        <p className="auth-switch">
          Remembered your password?{" "}
          <Link to="/login">Return to sign in</Link>
        </p>
      </div>
    </section>
  );
}