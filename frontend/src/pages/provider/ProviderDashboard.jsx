import { useCallback, useEffect, useState } from "react";
import {
  BarChart3,
  BriefcaseBusiness,
  CalendarDays,
  CalendarClock,
  CheckCircle2,
  Clock3,
  DollarSign,
  Edit3,
  ImagePlus,
  MapPin,
  RefreshCw,
  Save,
  Star,
  Trash2,
  X,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import api from "../../api/api";

const emptyProfileForm = {
  business_name: "",
  category: "",
  hourly_rate: "",
  city: "",
  address: "",
  description: "",
};

const emptyStatistics = {
  total_bookings: 0,
  completed_services: 0,
  total_earnings: 0,
  average_rating: 0,
};

function getErrorMessage(error, fallback) {
  return (
    error.response?.data?.message ||
    error.response?.data?.detail ||
    error.response?.data?.details?.[0]?.message ||
    fallback
  );
}

function getResponseData(response) {
  return response?.data?.data ?? response?.data ?? null;
}

function formatMoney(value) {
  return Number(value || 0).toLocaleString();
}

export default function ProviderDashboard() {
  const [activeTab, setActiveTab] = useState("overview");

  const [provider, setProvider] = useState(null);
  const [portfolio, setPortfolio] = useState([]);
  const [statistics, setStatistics] = useState(emptyStatistics);

  const [profileForm, setProfileForm] = useState(emptyProfileForm);
  const [portfolioForm, setPortfolioForm] = useState({
    image_url: "",
    caption: "",
  });
  const navigate = useNavigate();

  const [profileMissing, setProfileMissing] = useState(false);
  const [editingProfile, setEditingProfile] = useState(false);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [submittingProfile, setSubmittingProfile] = useState(false);
  const [submittingImage, setSubmittingImage] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const populateProfileForm = useCallback((profile) => {
    setProfileForm({
      business_name: profile?.business_name || "",
      category: profile?.category || "",
      hourly_rate: profile?.hourly_rate ?? "",
      city: profile?.city || "",
      address: profile?.address || "",
      description: profile?.description || "",
    });
  }, []);

  const loadProviderDetails = useCallback(async () => {
    const results = await Promise.allSettled([
      api.get("/providers/me/statistics"),
      api.get("/providers/me/portfolio"),
    ]);

    const statisticsResult = results[0];
    const portfolioResult = results[1];

    if (statisticsResult.status === "fulfilled") {
      const data = getResponseData(statisticsResult.value);

      setStatistics({
        total_bookings: data?.total_bookings || 0,
        completed_services:
          data?.completed_services ??
          data?.completed_bookings ??
          0,
        total_earnings: data?.total_earnings || 0,
        average_rating: data?.average_rating || 0,
      });
    } else {
      setStatistics(emptyStatistics);
    }

    if (portfolioResult.status === "fulfilled") {
      const data = getResponseData(portfolioResult.value);
      setPortfolio(Array.isArray(data) ? data : []);
    } else {
      setPortfolio([]);
    }
  }, []);

  const loadDashboard = useCallback(
    async (isRefresh = false) => {
      setError("");
      setSuccess("");

      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      try {
        const response = await api.get("/providers/me");
        const profile = getResponseData(response);

        setProvider(profile);
        setProfileMissing(false);
        populateProfileForm(profile);

        await loadProviderDetails();
      } catch (requestError) {
        if (requestError.response?.status === 404) {
          /*
           * A provider-role user can exist without a provider profile.
           * The first form submission must create that profile.
           */
          setProvider(null);
          setProfileMissing(true);
          setEditingProfile(true);
          setActiveTab("business");
          setPortfolio([]);
          setStatistics(emptyStatistics);
          setProfileForm(emptyProfileForm);
        } else {
          setError(
            getErrorMessage(
              requestError,
              "Unable to load the provider dashboard.",
            ),
          );
        }
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [loadProviderDetails, populateProfileForm],
  );

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  const updateProfileField = (event) => {
    const { name, value } = event.target;

    setProfileForm((current) => ({
      ...current,
      [name]: value,
    }));
  };

  const saveProfile = async (event) => {
    event.preventDefault();
    setError("");
    setSuccess("");

    if (!profileForm.business_name.trim()) {
      setError("Business name is required.");
      return;
    }

    if (!profileForm.category.trim()) {
      setError("Service category is required.");
      return;
    }

    if (
      profileForm.hourly_rate === "" ||
      Number(profileForm.hourly_rate) < 0
    ) {
      setError("Enter a valid hourly rate.");
      return;
    }

    const payload = {
      business_name: profileForm.business_name.trim(),
      category: profileForm.category.trim(),
      hourly_rate: Number(profileForm.hourly_rate),
      city: profileForm.city.trim(),
      address: profileForm.address.trim(),
      description: profileForm.description.trim(),
    };

    setSubmittingProfile(true);

    try {
      /*
       * No profile: create an application.
       * Existing profile: update it.
       */
      const response = profileMissing
        ? await api.post("/providers/become", payload)
        : await api.patch("/providers/me", payload);

      const savedProfile = getResponseData(response);

      setProvider(savedProfile);
      setProfileMissing(false);
      setEditingProfile(false);
      populateProfileForm(savedProfile);

      setSuccess(
        profileMissing
          ? "Provider application submitted successfully. It is waiting for administrator approval."
          : "Business profile updated successfully.",
      );

      await loadProviderDetails();
    } catch (requestError) {
      setError(
        getErrorMessage(
          requestError,
          profileMissing
            ? "Unable to submit your provider application."
            : "Unable to update the provider profile.",
        ),
      );
    } finally {
      setSubmittingProfile(false);
    }
  };

  const cancelProfileEditing = () => {
    if (profileMissing) {
      setProfileForm(emptyProfileForm);
      return;
    }

    populateProfileForm(provider);
    setEditingProfile(false);
    setError("");
  };

  const updatePortfolioField = (event) => {
    const { name, value } = event.target;

    setPortfolioForm((current) => ({
      ...current,
      [name]: value,
    }));
  };

  const addPortfolioImage = async (event) => {
    event.preventDefault();
    setError("");
    setSuccess("");

    if (!portfolioForm.image_url.trim()) {
      setError("Portfolio image URL is required.");
      return;
    }

    setSubmittingImage(true);

    try {
      const response = await api.post("/providers/me/portfolio", {
        image_url: portfolioForm.image_url.trim(),
        caption: portfolioForm.caption.trim(),
      });

      const image = getResponseData(response);

      setPortfolio((current) => [image, ...current]);
      setPortfolioForm({
        image_url: "",
        caption: "",
      });

      setSuccess("Portfolio image added successfully.");
    } catch (requestError) {
      setError(
        getErrorMessage(
          requestError,
          "Unable to add the portfolio image.",
        ),
      );
    } finally {
      setSubmittingImage(false);
    }
  };

  const deletePortfolioImage = async (imageId) => {
    const confirmed = window.confirm(
      "Do you want to remove this portfolio image?",
    );

    if (!confirmed) {
      return;
    }

    setError("");
    setSuccess("");

    try {
      await api.delete(`/providers/me/portfolio/${imageId}`);

      setPortfolio((current) =>
        current.filter((image) => image.id !== imageId),
      );

      setSuccess("Portfolio image removed.");
    } catch (requestError) {
      setError(
        getErrorMessage(
          requestError,
          "Unable to remove the portfolio image.",
        ),
      );
    }
  };

  if (loading) {
    return (
      <main className="provider-page">
        <div className="provider-container">
          <div className="page-loading">
            <RefreshCw className="spin" size={30} />
            <p>Loading provider dashboard...</p>
          </div>
        </div>
      </main>
    );
  }

  const isVerified = Boolean(provider?.is_verified);
  const rating =
    statistics.average_rating ||
    provider?.rating ||
    0;

  return (
    <main className="provider-page">
      <div className="provider-container">
        <section className="provider-dashboard-header">
          <div className="provider-dashboard-icon">
            <BriefcaseBusiness size={35} />
          </div>

          <div className="provider-dashboard-heading">
            <span className="eyebrow">
              Provider workspace
            </span>

            <h1>Provider dashboard</h1>

            <div className="provider-heading-meta">
              <span>
                <MapPin size={18} />
                {provider?.city || "Location not provided"}
              </span>

              <span>
                <Star size={18} />
                {Number(rating).toFixed(1)} rating
              </span>

              <span
                className={`status-badge ${
                  isVerified ? "verified" : "pending"
                }`}
              >
                {isVerified ? (
                  <CheckCircle2 size={16} />
                ) : (
                  <Clock3 size={16} />
                )}

                {isVerified
                  ? "Verified provider"
                  : "Verification pending"}
              </span>
            </div>
          </div>

          <button
            type="button"
            className="button button-outline"
            onClick={() => loadDashboard(true)}
            disabled={refreshing}
          >
            <RefreshCw
              size={18}
              className={refreshing ? "spin" : ""}
            />

            {refreshing ? "Refreshing..." : "Refresh"}
          </button>
        </section>

        {profileMissing && (
          <div className="alert alert-warning">
            Your provider profile has not been created yet.
            Complete the business profile below and submit your
            application.
          </div>
        )}

        {error && (
          <div className="alert alert-error">{error}</div>
        )}

        {success && (
          <div className="alert alert-success">{success}</div>
        )}

        <nav className="provider-tabs">
  <button
    type="button"
    className={activeTab === "overview" ? "active" : ""}
    onClick={() => setActiveTab("overview")}
    disabled={profileMissing}
  >
    <BarChart3 size={19} />
    Overview
  </button>

  <button
    type="button"
    className={activeTab === "business" ? "active" : ""}
    onClick={() => setActiveTab("business")}
  >
    <BriefcaseBusiness size={19} />
    Business profile
  </button>

  <button
    type="button"
    onClick={() => navigate("/provider/bookings")}
    disabled={profileMissing}
  >
    <CalendarDays size={19} />
    Bookings
  </button>


  <button
  type="button"
  onClick={() =>
    navigate("/provider/availability")
  }
  disabled={profileMissing}
>
  <CalendarClock size={19} />
  Availability
</button>

  <button
    type="button"
    className={activeTab === "portfolio" ? "active" : ""}
    onClick={() => setActiveTab("portfolio")}
    disabled={profileMissing}
  >
    <ImagePlus size={19} />
    Portfolio
  </button>
</nav>

        {activeTab === "overview" && !profileMissing && (
          <section className="provider-tab-content">
            <div className="provider-statistics-grid">
              <article className="provider-stat-card">
                <span className="provider-stat-icon purple">
                  <Clock3 size={25} />
                </span>

                <div>
                  <span>Total bookings</span>
                  <strong>
                    {statistics.total_bookings}
                  </strong>
                </div>
              </article>

              <article className="provider-stat-card">
                <span className="provider-stat-icon green">
                  <CheckCircle2 size={25} />
                </span>

                <div>
                  <span>Completed services</span>
                  <strong>
                    {statistics.completed_services}
                  </strong>
                </div>
              </article>

              <article className="provider-stat-card">
                <span className="provider-stat-icon orange">
                  <DollarSign size={25} />
                </span>

                <div>
                  <span>Total earnings</span>
                  <strong>
                    PKR{" "}
                    {formatMoney(
                      statistics.total_earnings,
                    )}
                  </strong>
                </div>
              </article>

              <article className="provider-stat-card">
                <span className="provider-stat-icon blue">
                  <Star size={25} />
                </span>

                <div>
                  <span>Average rating</span>
                  <strong>
                    {Number(rating).toFixed(1)}
                  </strong>
                </div>
              </article>
            </div>

            <div className="provider-dashboard-quick-actions">
              <button
                type="button"
                className="provider-booking-shortcut"
                onClick={() => navigate("/provider/bookings")}
              >
                <div className="provider-booking-shortcut-icon">
                  <CalendarDays size={24} />
                </div>

                <div>
                  <strong>Booking requests</strong>
                  <span>
                    Review customer requests, accept jobs and manage
                    completed bookings.
                  </span>
                </div>

                <span className="provider-booking-shortcut-arrow">
                  →
                </span>
              </button>
            </div>

            <div className="provider-summary-grid">
              <article className="provider-panel">
                <h2>Business summary</h2>
                <p>Your public provider information.</p>

                <dl className="provider-details-list">
                  <div>
                    <dt>Business name</dt>
                    <dd>
                      {provider?.business_name ||
                        "Not provided"}
                    </dd>
                  </div>

                  <div>
                    <dt>Category</dt>
                    <dd>
                      {provider?.category || "Not provided"}
                    </dd>
                  </div>

                  <div>
                    <dt>Hourly rate</dt>
                    <dd>
                      PKR{" "}
                      {formatMoney(provider?.hourly_rate)}
                    </dd>
                  </div>

                  <div>
                    <dt>City</dt>
                    <dd>
                      {provider?.city || "Not provided"}
                    </dd>
                  </div>

                  <div>
                    <dt>Address</dt>
                    <dd>
                      {provider?.address || "Not provided"}
                    </dd>
                  </div>
                </dl>
              </article>

              <article className="provider-panel">
                <h2>About your business</h2>

                <p>
                  {provider?.description ||
                    "Add a description to tell customers about your skills and experience."}
                </p>

                <button
                  type="button"
                  className="button"
                  onClick={() => {
                    setEditingProfile(true);
                    setActiveTab("business");
                  }}
                >
                  <Edit3 size={18} />
                  Edit business profile
                </button>
              </article>
            </div>
          </section>
        )}

        {activeTab === "business" && (
          <section className="provider-tab-content">
            <div className="provider-section-heading">
              <div>
                <h2>
                  {profileMissing
                    ? "Create your provider profile"
                    : "Business profile"}
                </h2>

                <p>
                  {profileMissing
                    ? "Provide your business information to submit your provider application."
                    : "Manage the information customers see about your business."}
                </p>
              </div>

              {!profileMissing && !editingProfile && (
                <button
                  type="button"
                  className="button"
                  onClick={() => setEditingProfile(true)}
                >
                  <Edit3 size={18} />
                  Edit profile
                </button>
              )}
            </div>

            {!editingProfile && !profileMissing ? (
              <div className="provider-details-grid">
                <div>
                  <span>Business name</span>
                  <strong>
                    {provider?.business_name ||
                      "Not provided"}
                  </strong>
                </div>

                <div>
                  <span>Category</span>
                  <strong>
                    {provider?.category || "Not provided"}
                  </strong>
                </div>

                <div>
                  <span>Hourly rate</span>
                  <strong>
                    PKR{" "}
                    {formatMoney(provider?.hourly_rate)}
                  </strong>
                </div>

                <div>
                  <span>City</span>
                  <strong>
                    {provider?.city || "Not provided"}
                  </strong>
                </div>

                <div>
                  <span>Business address</span>
                  <strong>
                    {provider?.address || "Not provided"}
                  </strong>
                </div>

                <div>
                  <span>Description</span>
                  <strong>
                    {provider?.description ||
                      "Not provided"}
                  </strong>
                </div>
              </div>
            ) : (
              <form
                className="provider-profile-form"
                onSubmit={saveProfile}
              >
                <div className="provider-form-grid">
                  <label className="form-field">
                    <span>Business name</span>
                    <input
                      type="text"
                      name="business_name"
                      value={profileForm.business_name}
                      onChange={updateProfileField}
                      placeholder="Example Home Services"
                      maxLength={255}
                      required
                    />
                  </label>

                  <label className="form-field">
                    <span>Category</span>
                    <input
                      type="text"
                      name="category"
                      value={profileForm.category}
                      onChange={updateProfileField}
                      placeholder="Cleaning, plumbing, electrical..."
                      maxLength={120}
                      required
                    />
                  </label>

                  <label className="form-field">
                    <span>Hourly rate (PKR)</span>
                    <input
                      type="number"
                      name="hourly_rate"
                      value={profileForm.hourly_rate}
                      onChange={updateProfileField}
                      placeholder="2000"
                      min="0"
                      step="0.01"
                      required
                    />
                  </label>

                  <label className="form-field">
                    <span>City</span>
                    <input
                      type="text"
                      name="city"
                      value={profileForm.city}
                      onChange={updateProfileField}
                      placeholder="Faisalabad"
                      maxLength={120}
                    />
                  </label>
                </div>

                <label className="form-field">
                  <span>Business address</span>
                  <input
                    type="text"
                    name="address"
                    value={profileForm.address}
                    onChange={updateProfileField}
                    placeholder="Complete business address"
                    maxLength={255}
                  />
                </label>

                <label className="form-field">
                  <span>Description</span>
                  <textarea
                    name="description"
                    value={profileForm.description}
                    onChange={updateProfileField}
                    placeholder="Tell customers about your experience and services..."
                    maxLength={1000}
                    rows={5}
                  />
                </label>

                <div className="provider-form-actions">
                  {!profileMissing && (
                    <button
                      type="button"
                      className="button button-outline"
                      onClick={cancelProfileEditing}
                      disabled={submittingProfile}
                    >
                      <X size={18} />
                      Cancel
                    </button>
                  )}

                  <button
                    type="submit"
                    className="button"
                    disabled={submittingProfile}
                  >
                    {submittingProfile ? (
                      <RefreshCw
                        className="spin"
                        size={18}
                      />
                    ) : (
                      <Save size={18} />
                    )}

                    {submittingProfile
                      ? "Saving..."
                      : profileMissing
                        ? "Submit provider application"
                        : "Save changes"}
                  </button>
                </div>
              </form>
            )}
          </section>
        )}

        {activeTab === "portfolio" && !profileMissing && (
          <section className="provider-tab-content">
            <div className="provider-section-heading">
              <div>
                <h2>Portfolio</h2>
                <p>
                  Show customers examples of your previous
                  work.
                </p>
              </div>
            </div>

            <form
              className="provider-portfolio-form"
              onSubmit={addPortfolioImage}
            >
              <label className="form-field">
                <span>Image URL</span>
                <input
                  type="url"
                  name="image_url"
                  value={portfolioForm.image_url}
                  onChange={updatePortfolioField}
                  placeholder="https://example.com/work-image.jpg"
                  required
                />
              </label>

              <label className="form-field">
                <span>Caption</span>
                <input
                  type="text"
                  name="caption"
                  value={portfolioForm.caption}
                  onChange={updatePortfolioField}
                  placeholder="Describe this project"
                  maxLength={255}
                />
              </label>

              <button
                type="submit"
                className="button"
                disabled={submittingImage}
              >
                {submittingImage ? (
                  <RefreshCw className="spin" size={18} />
                ) : (
                  <ImagePlus size={18} />
                )}

                {submittingImage
                  ? "Adding..."
                  : "Add image"}
              </button>
            </form>

            {portfolio.length === 0 ? (
              <div className="provider-empty-state">
                <ImagePlus size={42} />
                <h3>No portfolio images</h3>
                <p>
                  Add examples of your work to attract
                  customers.
                </p>
              </div>
            ) : (
              <div className="provider-portfolio-grid">
                {portfolio.map((image) => (
                  <article
                    className="provider-portfolio-card"
                    key={image.id}
                  >
                    <img
                      src={image.image_url}
                      alt={
                        image.caption ||
                        "Provider portfolio"
                      }
                    />

                    <div>
                      <p>
                        {image.caption ||
                          "Portfolio project"}
                      </p>

                      <button
                        type="button"
                        className="icon-button danger"
                        onClick={() =>
                          deletePortfolioImage(image.id)
                        }
                        aria-label="Delete portfolio image"
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
        )}
      </div>
    </main>
  );
}