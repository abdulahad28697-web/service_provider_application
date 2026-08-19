import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ArrowLeft,
  BadgeCheck,
  Ban,
  BriefcaseBusiness,
  CheckCircle2,
  Clock3,
  Eye,
  Mail,
  RefreshCw,
  Search,
  ShieldCheck,
  Users,
  Wrench,
} from "lucide-react";
import { Link, useLocation } from "react-router-dom";

import api from "../../api/api";

export default function ProviderApplications() {
  const location = useLocation();

  const [providers, setProviders] = useState([]);
  const [users, setUsers] = useState([]);
  const [services, setServices] = useState([]);

  const [filter, setFilter] = useState("pending");
  const [search, setSearch] = useState("");

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [actionLoadingId, setActionLoadingId] = useState(null);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState(
    location.state?.message || "",
  );

  // ---------------------------------------------------------
  // LOAD PROVIDERS + USERS + CURRENT ACTIVE SERVICES
  // ---------------------------------------------------------

  const loadApplications = useCallback(async (isRefresh = false) => {
    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError("");

    try {
      const [
        providersResponse,
        usersResponse,
        servicesResponse,
      ] = await Promise.all([
        api.get("/admin/providers"),
        api.get("/admin/users"),
        api.get("/services", {
          params: {
            page_size: 100,
          },
        }),
      ]);

      const providersData =
        providersResponse.data?.data || [];

      const usersData =
        usersResponse.data?.data || [];

      const servicesPayload =
        servicesResponse.data?.data || {};

      const servicesData = Array.isArray(servicesPayload)
        ? servicesPayload
        : Array.isArray(servicesPayload?.items)
          ? servicesPayload.items
          : [];

      setProviders(providersData);
      setUsers(usersData);
      setServices(servicesData);
    } catch (requestError) {
      setError(
        requestError.response?.data?.message ||
          requestError.response?.data?.detail ||
          "Unable to load provider applications.",
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadApplications();
  }, [loadApplications]);

  // ---------------------------------------------------------
  // QUICK APPROVE / REJECT ACTIONS
  // ---------------------------------------------------------

  const handleQuickDecision = async (providerId, isApproved) => {
    const targetProvider = providers.find(
      (p) => Number(p.id) === Number(providerId),
    );
    const businessName = targetProvider?.business_name || "Provider";

    try {
      setActionLoadingId(providerId);
      setError("");
      setSuccessMessage("");

      await api.put(`/admin/providers/${providerId}/verify`, {
        is_verified: isApproved,
      });

      await loadApplications(true);

      setSuccessMessage(
        isApproved
          ? `Successfully approved "${businessName}"! The provider is now verified and active.`
          : `Application for "${businessName}" was rejected.`,
      );
    } catch (requestError) {
      setError(
        requestError.response?.data?.message ||
          requestError.response?.data?.detail ||
          "Unable to process provider application decision.",
      );
    } finally {
      setActionLoadingId(null);
    }
  };

  // ---------------------------------------------------------
  // BUILD PROVIDER APPLICATION DATA
  // ---------------------------------------------------------

  const applications = useMemo(() => {
    const searchValue = search.trim().toLowerCase();

    return providers
      .map((provider) => {
        const owner = users.find(
          (user) => Number(user.id) === Number(provider.user_id),
        );

        const providerServices = services.filter(
          (service) => Number(service.provider_id) === Number(provider.id),
        );

        return {
          ...provider,
          owner,
          services: providerServices,
          service_count: providerServices.length,
        };
      })
      .filter((provider) => {
        if (filter === "pending" && provider.is_verified) {
          return false;
        }

        if (filter === "verified" && !provider.is_verified) {
          return false;
        }

        if (!searchValue) {
          return true;
        }

        return [
          provider.business_name,
          provider.category,
          provider.city,
          provider.owner?.full_name,
          provider.owner?.email,
          ...provider.services.map((service) => service.title),
        ].some((value) =>
          String(value || "")
            .toLowerCase()
            .includes(searchValue),
        );
      });
  }, [providers, users, services, filter, search]);

  // ---------------------------------------------------------
  // COUNTS
  // ---------------------------------------------------------

  const pendingCount = providers.filter(
    (provider) => !provider.is_verified,
  ).length;

  const verifiedCount = providers.filter(
    (provider) => provider.is_verified,
  ).length;

  // ---------------------------------------------------------
  // UI
  // ---------------------------------------------------------

  return (
    <main className="admin-page">
      <div className="admin-container">
        {/* PAGE HEADER */}

        <div className="admin-page-header">
          <div>
            <Link className="admin-back-link" to="/admin">
              <ArrowLeft size={17} />
              Admin dashboard
            </Link>

            <span className="eyebrow">Provider management</span>

            <h1>Provider applications</h1>

            <p>
              Review professional details, verify credentials, and approve or reject
              pending applications with real-time status updates.
            </p>
          </div>

          <button
            type="button"
            className="button button-outline"
            onClick={() => loadApplications(true)}
            disabled={loading || refreshing}
          >
            <RefreshCw size={16} className={refreshing ? "spin" : ""} />
            {refreshing ? "Refreshing..." : "Refresh"}
          </button>
        </div>

        {/* NOTIFICATIONS / ALERTS */}
        {error && <div className="alert alert-error">{error}</div>}
        {successMessage && (
          <div className="alert alert-success">{successMessage}</div>
        )}

        {/* STATISTICS */}

        <section className="admin-stat-grid">
          <article className="admin-stat-card">
            <div className="admin-stat-icon blue">
              <Users size={22} />
            </div>

            <div>
              <span>Total applications</span>
              <strong>{providers.length}</strong>
            </div>
          </article>

          <article className="admin-stat-card">
            <div className="admin-stat-icon amber">
              <Clock3 size={22} />
            </div>

            <div>
              <span>Pending review</span>
              <strong>{pendingCount}</strong>
            </div>
          </article>

          <article className="admin-stat-card">
            <div className="admin-stat-icon green">
              <ShieldCheck size={22} />
            </div>

            <div>
              <span>Verified providers</span>
              <strong>{verifiedCount}</strong>
            </div>
          </article>
        </section>

        {/* APPLICATION PANEL */}

        <section className="admin-panel">
          {/* FILTERS */}

          <div className="admin-toolbar">
            <div className="admin-filter-tabs">
              <button
                type="button"
                className={filter === "pending" ? "active" : ""}
                onClick={() => setFilter("pending")}
              >
                Pending
                <span>{pendingCount}</span>
              </button>

              <button
                type="button"
                className={filter === "verified" ? "active" : ""}
                onClick={() => setFilter("verified")}
              >
                Verified
                <span>{verifiedCount}</span>
              </button>

              <button
                type="button"
                className={filter === "all" ? "active" : ""}
                onClick={() => setFilter("all")}
              >
                All
                <span>{providers.length}</span>
              </button>
            </div>

            <label className="admin-search">
              <Search size={18} />

              <input
                type="search"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search name, email, category or service"
              />
            </label>
          </div>

          {/* APPLICATIONS */}

          {loading ? (
            <div className="admin-empty-state">
              <Clock3 size={35} />

              <h2>Loading applications...</h2>
            </div>
          ) : applications.length === 0 ? (
            <div className="admin-empty-state">
              <CheckCircle2 size={38} />

              <h2>No applications found</h2>

              <p>There are no providers matching this filter.</p>
            </div>
          ) : (
            <div className="provider-application-grid">
              {applications.map((provider) => {
                const isActing = actionLoadingId === provider.id;

                return (
                  <article
                    className="provider-application-card"
                    key={provider.id}
                  >
                    {/* CARD HEADER */}

                    <div className="provider-card-header">
                      <div className="provider-card-icon">
                        <BriefcaseBusiness size={24} />
                      </div>

                      <span
                        className={
                          provider.is_verified
                            ? "status-badge verified"
                            : "status-badge pending"
                        }
                      >
                        {provider.is_verified ? "Verified" : "Pending"}
                      </span>
                    </div>

                    {/* CARD CONTENT */}

                    <div className="provider-card-content">
                      <h2>{provider.business_name || "Unnamed business"}</h2>

                      <p className="provider-owner-name">
                        {provider.owner?.full_name ||
                          "User information unavailable"}
                      </p>

                      {/* EMAIL */}

                      <div className="provider-detail-row">
                        <Mail size={16} />
                        <span>{provider.owner?.email || "Email unavailable"}</span>
                      </div>

                      {/* PROVIDER PROFILE CATEGORY */}

                      <div className="provider-detail-row">
                        <BriefcaseBusiness size={16} />
                        <span>{provider.category || "Category not provided"}</span>
                      </div>

                      {/* ACTIVE SERVICE COUNT */}

                      <div className="provider-detail-row">
                        <Wrench size={16} />
                        <span>
                          {provider.service_count > 0
                            ? `${provider.service_count} active service${
                                provider.service_count > 1 ? "s" : ""
                              }`
                            : "No active services"}
                        </span>
                      </div>

                      {/* SUMMARY */}

                      <dl className="provider-card-summary">
                        <div>
                          <dt>Hourly rate</dt>
                          <dd>
                            PKR{" "}
                            {Number(provider.hourly_rate || 0).toLocaleString()}
                          </dd>
                        </div>

                        <div>
                          <dt>City</dt>
                          <dd>{provider.city || "Not provided"}</dd>
                        </div>
                      </dl>
                    </div>

                    {/* ACTIONS */}

                    <div
                      className="provider-card-actions"
                      style={{
                        display: "flex",
                        flexDirection: "column",
                        gap: "0.5rem",
                        marginTop: "1rem",
                      }}
                    >
                      {!provider.is_verified ? (
                        <div style={{ display: "flex", gap: "0.5rem" }}>
                          <button
                            type="button"
                            className="button button-danger-outline"
                            style={{ flex: 1, padding: "0.55rem 0.75rem" }}
                            onClick={() =>
                              handleQuickDecision(provider.id, false)
                            }
                            disabled={isActing}
                          >
                            <Ban size={16} />
                            {isActing ? "..." : "Reject"}
                          </button>

                          <button
                            type="button"
                            className="button button-primary"
                            style={{ flex: 1, padding: "0.55rem 0.75rem" }}
                            onClick={() =>
                              handleQuickDecision(provider.id, true)
                            }
                            disabled={isActing}
                          >
                            <BadgeCheck size={16} />
                            {isActing ? "..." : "Approve"}
                          </button>
                        </div>
                      ) : (
                        <div style={{ display: "flex", gap: "0.5rem" }}>
                          <button
                            type="button"
                            className="button button-danger-outline"
                            style={{ flex: 1, padding: "0.45rem" }}
                            onClick={() =>
                              handleQuickDecision(provider.id, false)
                            }
                            disabled={isActing}
                            title="Revoke verification"
                          >
                            <Ban size={15} />
                            {isActing ? "..." : "Revoke"}
                          </button>
                        </div>
                      )}

                      <Link
                        className="button button-outline button-full"
                        to={`/admin/providers/${provider.id}`}
                      >
                        <Eye size={16} />
                        Review Details
                      </Link>
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </section>

        <p className="admin-security-note">
          Protected administrative portal. Provider status changes immediately update database records and trigger user notifications.
        </p>
      </div>
    </main>
  );
}