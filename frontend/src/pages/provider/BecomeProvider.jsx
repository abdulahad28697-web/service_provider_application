import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  BadgeCheck,
  BriefcaseBusiness,
  CheckCircle2,
  DollarSign,
  MapPin,
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
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const navigate = useNavigate();
  const { fetchCurrentUser } = useAuth();

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

      await api.post("/providers/become", {
        ...form,
        hourly_rate: Number(form.hourly_rate),
      });

      if (fetchCurrentUser) {
        await fetchCurrentUser();
      }

      navigate("/provider", {
        replace: true,
        state: {
          message: "Your provider profile was created successfully.",
        },
      });
    } catch (err) {
      setError(
        err.response?.data?.message ||
          err.response?.data?.detail ||
          "Unable to create your provider profile."
      );
    } finally {
      setSubmitting(false);
    }
  };

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
                ? "Creating your profile..."
                : "Become a provider"}
            </button>
          </form>
        </section>
      </div>
    </main>
  );
}

export default BecomeProvider;