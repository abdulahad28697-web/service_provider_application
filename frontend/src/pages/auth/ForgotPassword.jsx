import { useState } from "react";
import { ArrowRight, CheckCircle2, Mail } from "lucide-react";
import { Link } from "react-router-dom";

import api from "../../api/api";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [submittedEmail, setSubmittedEmail] = useState("");
  const [directResetUrl, setDirectResetUrl] = useState("");
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setSubmitting(true);

    try {
      const cleanEmail = email.trim().toLowerCase();
      const response = await api.post("/auth/forgot-password", {
        email: cleanEmail,
      });

      const resetData = response.data?.data;
      setDirectResetUrl(resetData?.reset_url || "");
      setSubmittedEmail(cleanEmail);
      setIsSuccess(true);
    } catch (requestError) {
      setError(
        requestError.response?.data?.message ||
          "Unable to process password reset request. Please try again.",
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="auth-page">
      <div className="auth-card">
        {isSuccess ? (
          <div className="auth-success-box text-center" style={{ textAlign: "center" }}>
            <div
              style={{
                width: "56px",
                height: "56px",
                borderRadius: "50%",
                background: "rgba(16, 185, 129, 0.12)",
                color: "#10b981",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                margin: "0 auto 1.25rem",
              }}
            >
              <CheckCircle2 size={32} />
            </div>

            <span className="eyebrow">Password Reset</span>
            <h1 style={{ fontSize: "1.6rem", margin: "0.5rem 0" }}>Reset Instructions Ready</h1>

            <p style={{ color: "var(--text-secondary, #64748b)", lineHeight: "1.5", marginBottom: "1.5rem" }}>
              If an active account is registered with <strong>{submittedEmail}</strong>, your verification reset token has been created.
            </p>

            {directResetUrl ? (
              <div style={{ marginBottom: "1.5rem" }}>
                <Link
                  to={directResetUrl}
                  className="button button-primary button-full"
                  style={{ justifyContent: "center", gap: "0.5rem", marginBottom: "0.75rem" }}
                >
                  Proceed to Reset Password Now
                  <ArrowRight size={18} />
                </Link>
                <p style={{ fontSize: "0.85rem", color: "#64748b" }}>
                  An email has also been dispatched if SMTP is connected.
                </p>
              </div>
            ) : (
              <div
                className="alert alert-info"
                style={{ textAlign: "left", fontSize: "0.9rem", lineHeight: "1.5", marginBottom: "1.5rem" }}
              >
                Please open your email client, click the reset link, and follow the instructions to approve and complete your password change.
              </div>
            )}

            <button
              type="button"
              className="button button-outline button-full"
              onClick={() => {
                setIsSuccess(false);
                setEmail("");
                setDirectResetUrl("");
              }}
              style={{ marginBottom: "1rem" }}
            >
              Try another email address
            </button>

            <p className="auth-switch" style={{ marginTop: "1rem" }}>
              <Link to="/login">Return to sign in</Link>
            </p>
          </div>
        ) : (
          <>
            <div className="auth-heading">
              <span className="eyebrow">Account recovery</span>
              <h1>Forgot your password?</h1>
              <p>
                Enter your registered email address and we will email you a secure link to reset your password.
              </p>
            </div>

            {error && <div className="alert alert-error">{error}</div>}

            <form className="auth-form" onSubmit={handleSubmit}>
              <label className="form-field">
                <span>Email address</span>

                <div className="input-with-icon">
                  <Mail size={18} />
                  <input
                    type="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    placeholder="you@example.com"
                    autoComplete="email"
                    required
                  />
                </div>
              </label>

              <button
                type="submit"
                className="button button-full"
                disabled={submitting || !email.trim()}
              >
                {submitting ? "Sending verification email..." : "Send reset link"}
                {!submitting && <ArrowRight size={18} />}
              </button>
            </form>

            <p className="auth-switch">
              Remembered your password? <Link to="/login">Return to sign in</Link>
            </p>
          </>
        )}
      </div>
    </section>
  );
}