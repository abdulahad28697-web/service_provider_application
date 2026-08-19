import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  ArrowRight,
  BadgeCheck,
  BriefcaseBusiness,
  Building2,
  CheckCircle2,
  Clock3,
  DollarSign,
  MapPin,
  RefreshCw,
  ShieldCheck,
  TrendingUp,
} from "lucide-react";

import api from "../../api/api";
import { useAuth } from "../../context/AuthContext";

const initialForm = {
  business_name: "",
  description: "",
  category: "",
  hourly_rate: "",
  city: "",
  address: "",
};

const categories = [
  "Cleaning",
  "Plumbing",
  "Electrical",
  "Carpentry",
  "Painting",
  "Home Repair",
  "IT and Technology",
  "Tutoring",
  "Beauty and Wellness",
  "Event Services",
  "Other",
];

function BecomeProvider() {
  const [form, setForm] = useState(initialForm);
  const [existingProvider, setExistingProvider] = useState(null);
  const [checkingStatus, setCheckingStatus] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const navigate = useNavigate();
  const { user, refreshUser } = useAuth();

  const checkExistingApplication = useCallback(async () => {
    setCheckingStatus(true);
    setError("");

    try {
      const response = await api.get("/providers/me");
      const data = response.data?.data;
      if (data) {
        setExistingProvider(data);
      }
    } catch (err) {
      // 404 means no application exists yet - user can apply
      if (err.response?.status !== 404) {
        // Other unexpected error
        console.error("Error checking provider status:", err);
      }
    } finally {
      setCheckingStatus(false);
    }
  }, []);

  useEffect(() => {
    checkExistingApplication();
  }, [checkExistingApplication]);

  const handleChange = (event) => {
    const { name, value } = event.target;

    setForm((current) => ({
      ...current,
      [name]: value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    try {
      setSubmitting(true);
      setError("");
      setSuccess("");

      const response = await api.post("/providers/become", {
        ...form,
        hourly_rate: Number(form.hourly_rate),
      });

      const newProvider = response.data?.data;
      setExistingProvider(newProvider || {
        ...form,
        hourly_rate: Number(form.hourly_rate),
        is_verified: false,
      });

      setSuccess("Your provider application was submitted successfully! It is now pending administrator review.");

      if (refreshUser) {
        await refreshUser();
      }
    } catch (err) {
      setError(
        err.response?.data?.message ||
          err.response?.data?.detail ||
          "Unable to submit your provider application."
      );
    } finally {
      setSubmitting(false);
    }
  };

  if (checkingStatus) {
    return (
      <main className="page-section provider-onboarding-page">
        <div className="container" style={{ textAlign: "center", padding: "4rem 0" }}>
          <RefreshCw size={28} className="spin" style={{ margin: "0 auto 1rem auto", color: "var(--primary)" }} />
          <p>Checking your provider status...</p>
        </div>
      </main>
    );
  }

  // User already has an application
  if (existingProvider) {
    const isVerified = existingProvider.is_verified;

    return (
      <main className="page-section provider-onboarding-page">
        <div className="container provider-status-view">
          <div className="panel provider-status-card">
            <div className={`provider-status-header-icon ${isVerified ? "verified" : "pending"}`}>
              {isVerified ? <BadgeCheck size={44} /> : <Clock3 size={44} />}
            </div>

            <span className={`status-badge ${isVerified ? "verified" : "pending"}`}>
              {isVerified ? "Verified Provider" : "Application Under Review"}
            </span>

            <h1>
              {isVerified
                ? "You are a Verified ServiceHub Provider!"
                : "Application Submitted & Under Review"}
            </h1>

            <p className="provider-status-description">
              {isVerified
                ? "Your provider profile is active and verified. You can list services, accept client bookings, and manage your business from the Provider Portal."
                : "Thank you for applying! Our administrator team is reviewing your business details. Once approved, you will receive a notification and full access to the Provider Portal."}
            </p>

            {success && <div className="alert alert-success">{success}</div>}

            <div className="provider-application-summary">
              <h3>Submitted Application Details</h3>
              <dl className="provider-summary-grid">
                <div>
                  <dt>Business Name</dt>
                  <dd>{existingProvider.business_name || "—"}</dd>
                </div>
                <div>
                  <dt>Category</dt>
                  <dd>{existingProvider.category || "—"}</dd>
                </div>
                <div>
                  <dt>Hourly Rate</dt>
                  <dd>PKR {Number(existingProvider.hourly_rate || 0).toLocaleString()}/hr</dd>
                </div>
                <div>
                  <dt>City</dt>
                  <dd>{existingProvider.city || "—"}</dd>
                </div>
                <div>
                  <dt>Address</dt>
                  <dd>{existingProvider.address || "—"}</dd>
                </div>
                <div>
                  <dt>Status</dt>
                  <dd>{isVerified ? "Approved & Active" : "Pending Administrator Approval"}</dd>
                </div>
              </dl>
            </div>

            <div className="provider-status-actions">
              {isVerified ? (
                <Link to="/provider" className="button button-primary button-large">
                  <BriefcaseBusiness size={18} />
                  Open Provider Dashboard
                  <ArrowRight size={18} />
                </Link>
              ) : (
                <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap", justifyContent: "center" }}>
                  <button
                    type="button"
                    className="button button-outline"
                    onClick={checkExistingApplication}
                  >
                    <RefreshCw size={16} />
                    Check Status
                  </button>
                  <Link to="/" className="button button-secondary">
                    Back to Home
                  </Link>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="page-section provider-onboarding-page">
      <div className="container provider-onboarding-layout">
        <aside className="provider-benefits">
          <span className="eyebrow">Grow your business</span>

          <h1>Become a trusted ServiceHub provider</h1>

          <p>
            Create your professional profile, offer your services and connect
            with customers looking for reliable help.
          </p>

          <div className="provider-benefit-list">
            <div className="provider-benefit">
              <span>
                <TrendingUp size={21} />
              </span>

              <div>
                <h3>Reach more customers</h3>
                <p>Show your services to customers searching in your area.</p>
              </div>
            </div>

            <div className="provider-benefit">
              <span>
                <BadgeCheck size={21} />
              </span>

              <div>
                <h3>Build your reputation</h3>
                <p>Grow through verified reviews and completed bookings.</p>
              </div>
            </div>

            <div className="provider-benefit">
              <span>
                <ShieldCheck size={21} />
              </span>

              <div>
                <h3>Manage everything</h3>
                <p>Track services, portfolio images, bookings and statistics.</p>
              </div>
            </div>
          </div>
        </aside>

        <section className="panel provider-onboarding-card">
          <div className="provider-form-heading">
            <div className="provider-heading-icon">
              <BriefcaseBusiness size={24} />
            </div>

            <div>
              <h2>Create your provider profile</h2>
              <p>Tell customers about your business and services.</p>
            </div>
          </div>

          {error && <div className="alert alert-error">{error}</div>}
          {success && <div className="alert alert-success">{success}</div>}

          <form className="settings-form" onSubmit={handleSubmit}>
            <label className="form-field">
              <span>Business name</span>

              <input
                type="text"
                name="business_name"
                className="text-input"
                placeholder="Ahmed Professional Services"
                value={form.business_name}
                onChange={handleChange}
                minLength={2}
                maxLength={255}
                required
              />
            </label>

            <label className="form-field">
              <span>Service category</span>

              <select
                name="category"
                className="text-input"
                value={form.category}
                onChange={handleChange}
                required
              >
                <option value="">Select a category</option>

                {categories.map((category) => (
                  <option value={category} key={category}>
                    {category}
                  </option>
                ))}
              </select>
            </label>

            <label className="form-field">
              <span>Business description</span>

              <textarea
                name="description"
                className="text-input textarea"
                placeholder="Describe your experience, skills and the services you provide..."
                value={form.description}
                onChange={handleChange}
                maxLength={1000}
                rows={5}
                required
              />
            </label>

            <div className="form-grid">
              <label className="form-field">
                <span>Hourly rate (PKR)</span>

                <div className="input-with-icon">
                  <DollarSign size={18} />

                  <input
                    type="number"
                    name="hourly_rate"
                    className="text-input"
                    placeholder="2000"
                    value={form.hourly_rate}
                    onChange={handleChange}
                    min="0"
                    step="1"
                    required
                  />
                </div>
              </label>

              <label className="form-field">
                <span>City</span>

                <div className="input-with-icon">
                  <MapPin size={18} />

                  <input
                    type="text"
                    name="city"
                    className="text-input"
                    placeholder="Faisalabad"
                    value={form.city}
                    onChange={handleChange}
                    maxLength={120}
                    required
                  />
                </div>
              </label>
            </div>

            <label className="form-field">
              <span>Business address</span>

              <input
                type="text"
                name="address"
                className="text-input"
                placeholder="House number, street and area"
                value={form.address}
                onChange={handleChange}
                maxLength={255}
                required
              />
            </label>

            <div className="provider-terms">
              <CheckCircle2 size={20} />

              <p>
                By creating a provider profile, you agree to provide accurate
                information and follow the ServiceHub provider guidelines.
              </p>
            </div>

            <button
              type="submit"
              className="button button-primary provider-submit-button"
              disabled={submitting}
            >
              <BriefcaseBusiness size={19} />

              {submitting
                ? "Submitting application..."
                : "Submit Provider Application"}
            </button>
          </form>
        </section>
      </div>
    </main>
  );
}

export default BecomeProvider;