import { useEffect, useState } from "react";
import {
  ArrowLeft,
  BadgeCheck,
  Ban,
  BriefcaseBusiness,
  Building2,
  CheckCircle2,
  CircleDollarSign,
  Clock3,
  Mail,
  MapPin,
  RefreshCw,
  ShieldCheck,
  Star,
  User,
  Wrench,
} from "lucide-react";
import { Link, useNavigate, useParams } from "react-router-dom";

import api from "../../api/api";

export default function ProviderDetails() {
  const { providerId } = useParams();
  const navigate = useNavigate();

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
      // First try dedicated admin provider details endpoint
      try {
        const directResponse = await api.get(`/admin/providers/${providerId}`);
        const data = directResponse.data?.data;
        if (data) {
          setProvider(data);
          setOwner(data.owner || null);
          return;
        }
      } catch (directError) {
        if (directError.response?.status === 404) {
          setError("Provider application not found or has been removed.");
          setProvider(null);
          setOwner(null);
          return;
        }
      }

      // Fallback lookup
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [providerId]);

  const updateVerification = async (isVerified) => {
    setSubmitting(true);
    setError("");
    setMessage("");

    const businessName = provider?.business_name || "Provider";

    try {
      const response = await api.put(
        `/admin/providers/${providerId}/verify`,
        {
          is_verified: isVerified,
        },
      );

      const updatedProvider = response.data?.data;

      if (!isVerified && !updatedProvider) {
        navigate("/admin/providers", {
          replace: true,
          state: {
            message: `Provider application for "${businessName}" was rejected and removed.`,
          },
        });
        return;
      }

      setProvider((current) => ({
        ...current,
        ...(updatedProvider || {}),
        is_verified: isVerified,
      }));

      setMessage(
        isVerified
          ? `Provider "${businessName}" approved successfully! The provider is now verified and active.`
          : `Provider application for "${businessName}" rejected.`,
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
        <div className="admin-container" style={{ textAlign: "center", padding: "4rem 0" }}>
          <RefreshCw size={28} className="spin" style={{ margin: "0 auto 1rem auto", color: "var(--primary)" }} />
          <p>Loading provider application details...</p>
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
            Back to provider applications
          </Link>

          <div className="alert alert-error" style={{ marginTop: "1rem" }}>
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
              Provider application review
            </span>

            <h1>{provider.business_name}</h1>

            <p>
              Review the account credentials and business information before
              confirming verification.
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
              <Clock3 size={18} />
            )}

            {provider.is_verified
              ? "Verified Provider"
              : "Verification Pending"}
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
          {/* ACCOUNT OWNER */}
          <article className="admin-panel provider-detail-card">
            <div className="admin-panel-heading">
              <User size={22} />

              <div>
                <h2>Account owner</h2>
                <p>Registered user details</p>
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
                <dd style={{ textTransform: "capitalize" }}>{owner?.role || "Customer"}</dd>
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

          {/* BUSINESS INFO */}
          <article className="admin-panel provider-detail-card">
            <div className="admin-panel-heading">
              <BriefcaseBusiness size={22} />

              <div>
                <h2>Business information</h2>
                <p>Provider public business profile</p>
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
                  PKR {Number(provider.hourly_rate || 0).toLocaleString()}/hr
                </dd>
              </div>

              <div>
                <dt>
                  <Star size={17} />
                  Rating
                </dt>
                <dd>{Number(provider.rating || 0).toFixed(1)} / 5.0</dd>
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

        {/* DESCRIPTION */}
        <section className="admin-panel provider-description-panel">
          <h2>Business description</h2>
          <p>
            {provider.description ||
              "The provider has not added a business description."}
          </p>
        </section>

        {/* DECISION PANEL */}
        <section className="admin-panel admin-action-panel">
          <div>
            <h2>Verification decision</h2>

            <p>
              Approving grants this provider verified badge status, elevates their
              role, and sends an approval notification. Rejecting revokes verification.
            </p>

            <div className="admin-security-note">
              <ShieldCheck size={19} />
              <span>
                Passwords and sensitive credentials are secure and never exposed.
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
              {submitting ? "Processing..." : "Reject application"}
            </button>

            <button
              type="button"
              className="button button-primary"
              onClick={() => updateVerification(true)}
              disabled={submitting}
            >
              <BadgeCheck size={18} />
              {submitting ? "Processing..." : "Approve provider"}
            </button>
          </div>
        </section>
      </div>
    </main>
  );
}