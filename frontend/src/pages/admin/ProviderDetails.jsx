import { useEffect, useState } from "react";
import {
  ArrowLeft,
  BadgeCheck,
  Ban,
  BriefcaseBusiness,
  Building2,
  CheckCircle2,
  CircleDollarSign,
  Mail,
  MapPin,
  ShieldCheck,
  Star,
  User,
} from "lucide-react";
import { Link, useParams } from "react-router-dom";

import api from "../../api/api";

export default function ProviderDetails() {
  const { providerId } = useParams();

  const [provider, setProvider] = useState(null);
  const [owner, setOwner] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const loadProvider = async () => {
    setLoading(true);
    setError("");

    try {
      const [providersResponse, usersResponse] = await Promise.all([
        api.get("/admin/providers"),
        api.get("/admin/users"),
      ]);

      const providers = providersResponse.data?.data || [];
      const users = usersResponse.data?.data || [];

      const selectedProvider = providers.find(
        (item) => Number(item.id) === Number(providerId),
      );

      if (!selectedProvider) {
        setError("Provider application not found.");
        setProvider(null);
        setOwner(null);
        return;
      }

      const providerOwner = users.find(
        (item) =>
          Number(item.id) === Number(selectedProvider.user_id),
      );

      setProvider(selectedProvider);
      setOwner(providerOwner || null);
    } catch (requestError) {
      setError(
        requestError.response?.data?.message ||
          requestError.response?.data?.detail ||
          "Unable to load this provider application.",
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProvider();
  }, [providerId]);

  const updateVerification = async (isVerified) => {
    setSubmitting(true);
    setError("");
    setMessage("");

    try {
      const response = await api.put(
        `/admin/providers/${providerId}/verify`,
        {
          is_verified: isVerified,
        },
      );

      const updatedProvider = response.data?.data;

      setProvider((current) => ({
        ...current,
        ...updatedProvider,
        is_verified: isVerified,
      }));

      setMessage(
        isVerified
          ? "Provider approved successfully."
          : "Provider application rejected.",
      );
    } catch (requestError) {
      setError(
        requestError.response?.data?.message ||
          requestError.response?.data?.detail ||
          "Unable to update the provider application.",
      );
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <main className="admin-page">
        <div className="admin-container">
          <p>Loading provider application...</p>
        </div>
      </main>
    );
  }

  if (!provider) {
    return (
      <main className="admin-page">
        <div className="admin-container">
          <Link
            to="/admin/providers"
            className="admin-back-link"
          >
            <ArrowLeft size={18} />
            Provider applications
          </Link>

          <div className="alert alert-error">
            {error || "Provider application not found."}
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="admin-page">
      <div className="admin-container">
        <Link
          to="/admin/providers"
          className="admin-back-link"
        >
          <ArrowLeft size={18} />
          Back to provider applications
        </Link>

        <header className="admin-page-header provider-review-header">
          <div>
            <span className="eyebrow">
              Provider application
            </span>

            <h1>{provider.business_name}</h1>

            <p>
              Review the account and business information before
              approving this provider.
            </p>
          </div>

          <span
            className={`status-badge ${
              provider.is_verified
                ? "status-approved"
                : "status-pending"
            }`}
          >
            {provider.is_verified ? (
              <BadgeCheck size={18} />
            ) : (
              <ShieldCheck size={18} />
            )}

            {provider.is_verified
              ? "Verified"
              : "Verification pending"}
          </span>
        </header>

        {error && (
          <div className="alert alert-error">{error}</div>
        )}

        {message && (
          <div className="alert alert-success">
            {message}
          </div>
        )}

        <section className="provider-review-grid">
          <article className="admin-panel provider-detail-card">
            <div className="admin-panel-heading">
              <User size={22} />

              <div>
                <h2>Account owner</h2>
                <p>Registered user information</p>
              </div>
            </div>

            <dl className="provider-detail-list">
              <div>
                <dt>
                  <User size={17} />
                  Full name
                </dt>
                <dd>{owner?.full_name || "Not available"}</dd>
              </div>

              <div>
                <dt>
                  <Mail size={17} />
                  Email
                </dt>
                <dd>{owner?.email || "Not available"}</dd>
              </div>

              <div>
                <dt>
                  <ShieldCheck size={17} />
                  Account role
                </dt>
                <dd>{owner?.role || "provider"}</dd>
              </div>

              <div>
                <dt>
                  <CheckCircle2 size={17} />
                  Account status
                </dt>
                <dd>
                  {owner?.is_active === false
                    ? "Inactive"
                    : "Active"}
                </dd>
              </div>
            </dl>
          </article>

          <article className="admin-panel provider-detail-card">
            <div className="admin-panel-heading">
              <BriefcaseBusiness size={22} />

              <div>
                <h2>Business information</h2>
                <p>Provider’s public business details</p>
              </div>
            </div>

            <dl className="provider-detail-list">
              <div>
                <dt>
                  <Building2 size={17} />
                  Business name
                </dt>
                <dd>{provider.business_name}</dd>
              </div>

              <div>
                <dt>
                  <BriefcaseBusiness size={17} />
                  Category
                </dt>
                <dd>{provider.category || "Not provided"}</dd>
              </div>

              <div>
                <dt>
                  <CircleDollarSign size={17} />
                  Hourly rate
                </dt>
                <dd>
                  PKR {Number(provider.hourly_rate || 0).toLocaleString()}
                </dd>
              </div>

              <div>
                <dt>
                  <Star size={17} />
                  Rating
                </dt>
                <dd>{provider.rating || "0.0"}</dd>
              </div>

              <div>
                <dt>
                  <MapPin size={17} />
                  City
                </dt>
                <dd>{provider.city || "Not provided"}</dd>
              </div>

              <div>
                <dt>
                  <MapPin size={17} />
                  Address
                </dt>
                <dd>{provider.address || "Not provided"}</dd>
              </div>
            </dl>
          </article>
        </section>

        <section className="admin-panel provider-description-panel">
          <h2>Business description</h2>

          <p>
            {provider.description ||
              "The provider has not added a business description."}
          </p>
        </section>

        <section className="admin-panel admin-action-panel">
          <div>
            <h2>Verification decision</h2>

            <p>
              Approving allows this provider to use verified
              provider features. Rejecting removes verification.
            </p>

            <div className="admin-security-note">
              <ShieldCheck size={19} />

              <span>
                Passwords must never be displayed to administrators.
                They remain securely hashed.
              </span>
            </div>
          </div>

          <div className="admin-action-buttons">
            <button
              type="button"
              className="button button-danger-outline"
              onClick={() => updateVerification(false)}
              disabled={submitting}
            >
              <Ban size={18} />
              {submitting ? "Updating..." : "Reject"}
            </button>

            <button
              type="button"
              className="button"
              onClick={() => updateVerification(true)}
              disabled={submitting}
            >
              <BadgeCheck size={18} />
              {submitting ? "Updating..." : "Approve provider"}
            </button>
          </div>
        </section>
      </div>
    </main>
  );
}