import { useEffect, useMemo, useState } from "react";

import {
  ArrowRight,
  BriefcaseBusiness,
  CalendarCheck2,
  CheckCircle2,
  CreditCard,
  Clock3,
  LogOut,
  MessageSquareText,
  RefreshCw,
  ShieldCheck,
  Star,
  Users,
} from "lucide-react";

import {
  Link,
  useNavigate,
} from "react-router-dom";

import api from "../../api/api";
import { useAuth } from "../../context/AuthContext";


export default function AdminDashboard() {
  const navigate = useNavigate();

  const {
    user,
    logout,
  } = useAuth();


  const [providers, setProviders] = useState([]);
  const [users, setUsers] = useState([]);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const [error, setError] = useState("");


  // =========================================================
  // LOAD DASHBOARD
  // =========================================================

  const loadDashboard = async (
    isRefresh = false,
  ) => {
    setError("");

    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    try {
      const [
        providersResponse,
        usersResponse,
      ] = await Promise.all([
        api.get("/admin/providers"),
        api.get("/admin/users"),
      ]);

      setProviders(
        providersResponse.data?.data || [],
      );

      setUsers(
        usersResponse.data?.data || [],
      );
    } catch (requestError) {
      setError(
        requestError.response?.data?.message ||
          requestError.response?.data?.detail ||
          "Unable to load the administrator dashboard.",
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };


  useEffect(() => {
    loadDashboard();
  }, []);


  // =========================================================
  // PROVIDER STATISTICS
  // =========================================================

  const pendingProviders = useMemo(
    () =>
      providers.filter(
        (provider) =>
          !provider.is_verified,
      ),
    [providers],
  );


  const verifiedProviders = useMemo(
    () =>
      providers.filter(
        (provider) =>
          provider.is_verified,
      ),
    [providers],
  );


  // =========================================================
  // USER STATISTICS
  // =========================================================

  const activeUsers = useMemo(
    () =>
      users.filter(
        (currentUser) =>
          currentUser.is_active !== false,
      ),
    [users],
  );


  const deactivatedUsers = useMemo(
    () =>
      users.filter(
        (currentUser) =>
          currentUser.is_active === false,
      ),
    [users],
  );


  const getProviderOwner = (
    provider,
  ) =>
    users.find(
      (currentUser) =>
        currentUser.id ===
        provider.user_id,
    );


  // =========================================================
  // LOGOUT
  // =========================================================

  const handleLogout = () => {
    logout();

    navigate(
      "/admin/login",
      {
        replace: true,
      },
    );
  };


  // =========================================================
  // LOADING
  // =========================================================

  if (loading) {
    return (
      <main className="admin-page">
        <div className="admin-container">

          <div className="page-loading">
            <RefreshCw
              className="spin"
              size={30}
            />

            <p>
              Loading administrator dashboard...
            </p>
          </div>

        </div>
      </main>
    );
  }


  return (
    <main className="admin-page">

      {/* =====================================================
          ADMIN HEADER
      ====================================================== */}

      <header className="admin-header">
        <div className="admin-header-content">

          <Link
            className="admin-brand"
            to="/admin"
          >
            <span className="admin-brand-icon">
              <ShieldCheck size={25} />
            </span>

            <span>
              Service<span>Hub</span> Admin
            </span>
          </Link>


          <div className="admin-header-actions">

            <div className="admin-user">
              <strong>
                {user?.full_name ||
                  "Administrator"}
              </strong>

              <span>
                {user?.email}
              </span>
            </div>


            <button
              type="button"
              className="button button-outline"
              onClick={handleLogout}
            >
              <LogOut size={18} />
              Logout
            </button>

          </div>

        </div>
      </header>


      <div className="admin-container">

        {/* ===================================================
            TITLE
        ==================================================== */}

        <section className="admin-title-row">

          <div>
            <span className="eyebrow">
              Administration workspace
            </span>

            <h1>
              Admin dashboard
            </h1>

            <p>
              Monitor platform activity,
              review provider applications,
              manage bookings and oversee
              customer reviews.
            </p>
          </div>


          <button
            type="button"
            className="button"
            onClick={() =>
              loadDashboard(true)
            }
            disabled={refreshing}
          >
            <RefreshCw
              size={18}
              className={
                refreshing
                  ? "spin"
                  : ""
              }
            />

            {refreshing
              ? "Refreshing..."
              : "Refresh"}
          </button>

        </section>


        {error && (
          <div className="alert alert-error">
            {error}
          </div>
        )}


        {/* ===================================================
            PLATFORM STATISTICS
        ==================================================== */}

        <section className="admin-stats">

          <article className="admin-stat-card">
            <span className="admin-stat-icon purple">
              <Users size={25} />
            </span>

            <div>
              <span>
                Active users
              </span>

              <strong>
                {activeUsers.length}
              </strong>

              <small className="admin-stat-subtext">
                {deactivatedUsers.length} deactivated
              </small>
            </div>
          </article>


          <article className="admin-stat-card">
            <span className="admin-stat-icon blue">
              <BriefcaseBusiness
                size={25}
              />
            </span>

            <div>
              <span>
                Total providers
              </span>

              <strong>
                {providers.length}
              </strong>
            </div>
          </article>


          <article className="admin-stat-card">
            <span className="admin-stat-icon orange">
              <Clock3 size={25} />
            </span>

            <div>
              <span>
                Pending approval
              </span>

              <strong>
                {pendingProviders.length}
              </strong>
            </div>
          </article>


          <article className="admin-stat-card">
            <span className="admin-stat-icon green">
              <CheckCircle2
                size={25}
              />
            </span>

            <div>
              <span>
                Verified providers
              </span>

              <strong>
                {verifiedProviders.length}
              </strong>
            </div>
          </article>

        </section>


        {/* ===================================================
            ADMIN MANAGEMENT
        ==================================================== */}

        <section className="admin-management-section">

          <div className="admin-section-heading">
            <span className="eyebrow">
              Platform management
            </span>

            <h2>
              Manage ServiceHub
            </h2>

            <p>
              Review provider accounts,
              inspect platform bookings and
              moderate customer reviews.
            </p>
          </div>


          <div className="admin-management-grid">

            {/* PROVIDERS */}

            <Link
              to="/admin/providers"
              className="admin-management-card"
            >
              <span className="admin-management-icon providers">
                <BriefcaseBusiness
                  size={26}
                />
              </span>

              <div>
                <h3>
                  Provider management
                </h3>

                <p>
                  Review provider
                  applications, inspect
                  business information and
                  manage verification.
                </p>

                <span className="admin-management-meta">
                  <Clock3 size={15} />

                  {pendingProviders.length}{" "}
                  pending{" "}
                  {pendingProviders.length ===
                  1
                    ? "application"
                    : "applications"}
                </span>
              </div>

              <ArrowRight
                className="admin-management-arrow"
                size={21}
              />
            </Link>


            {/* BOOKINGS */}

            <Link
              to="/admin/bookings"
              className="admin-management-card"
            >
              <span className="admin-management-icon bookings">
                <CalendarCheck2
                  size={26}
                />
              </span>

              <div>
                <h3>
                  Booking management
                </h3>

                <p>
                  View platform bookings,
                  inspect booking status and
                  investigate customer or
                  provider issues.
                </p>

                <span className="admin-management-meta">
                  <CalendarCheck2
                    size={15}
                  />

                  View all bookings
                </span>
              </div>

              <ArrowRight
                className="admin-management-arrow"
                size={21}
              />
            </Link>


            {/* REVIEWS */}

            <Link
              to="/admin/reviews"
              className="admin-management-card"
            >
              <span className="admin-management-icon reviews">
                <Star size={26} />
              </span>

              <div>
                <h3>
                  Review management
                </h3>

                <p>
                  Monitor ratings and
                  customer feedback across
                  ServiceHub providers.
                </p>

                <span className="admin-management-meta">
                  <MessageSquareText
                    size={15}
                  />

                  View customer reviews
                </span>
              </div>

              <ArrowRight
                className="admin-management-arrow"
                size={21}
              />
            </Link>


            {/* PAYMENTS */}

            <Link
              to="/admin/payments"
              className="admin-management-card"
            >
              <span className="admin-management-icon payments">
                <CreditCard size={26} />
              </span>

              <div>
                <h3>
                  Payment management
                </h3>

                <p>
                  Review Cash, JazzCash and
                  Easypaisa transactions,
                  payment statuses and refunds.
                </p>

                <span className="admin-management-meta">
                  <CreditCard size={15} />

                  Manage platform payments
                </span>
              </div>

              <ArrowRight
                className="admin-management-arrow"
                size={21}
              />
            </Link>

          </div>

        </section>


        {/* ===================================================
            PENDING PROVIDERS
        ==================================================== */}

        <section className="admin-panel">

          <div className="admin-panel-header">

            <div>
              <h2>
                Pending provider applications
              </h2>

              <p>
                Review business information
                before approving provider
                access.
              </p>
            </div>


            <Link
              className="button button-outline"
              to="/admin/providers"
            >
              View all applications
            </Link>

          </div>


          {pendingProviders.length === 0 ? (
            <div className="admin-empty-state">

              <CheckCircle2
                size={42}
              />

              <h3>
                No pending applications
              </h3>

              <p>
                Every provider application
                has been reviewed.
              </p>

            </div>
          ) : (
            <div className="admin-provider-list">

              {pendingProviders
                .slice(0, 5)
                .map((provider) => {
                  const owner =
                    getProviderOwner(
                      provider,
                    );

                  return (
                    <article
                      className="admin-provider-row"
                      key={provider.id}
                    >

                      <div className="admin-provider-avatar">
                        <BriefcaseBusiness
                          size={23}
                        />
                      </div>


                      <div className="admin-provider-info">

                        <h3>
                          {provider.business_name ||
                            "Unnamed business"}
                        </h3>


                        <p>
                          {owner?.full_name ||
                            "Provider account"}

                          {" • "}

                          {owner?.email ||
                            `User ID: ${provider.user_id}`}
                        </p>


                        <div className="admin-provider-meta">

                          <span>
                            {provider.category ||
                              "No category"}
                          </span>

                          <span>
                            {provider.city ||
                              "Location not provided"}
                          </span>

                          <span>
                            PKR{" "}
                            {Number(
                              provider.hourly_rate ||
                                0,
                            ).toLocaleString()}
                            /hour
                          </span>

                        </div>

                      </div>


                      <span className="status-badge pending">
                        <Clock3
                          size={15}
                        />

                        Pending
                      </span>


                      <Link
                        className="button"
                        to={`/admin/providers/${provider.id}`}
                      >
                        Review
                      </Link>

                    </article>
                  );
                })}

            </div>
          )}

        </section>

      </div>

    </main>
  );
}