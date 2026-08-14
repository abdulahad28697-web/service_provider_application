import { useCallback, useEffect, useState } from "react";
import {
  ArrowLeft,
  BriefcaseBusiness,
  CalendarDays,
  Clock3,
  Heart,
  MapPin,
  RefreshCw,
  Star,
  Wrench,
} from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";

import api from "../../api/api";


function getData(response) {
  return response?.data?.data ?? response?.data ?? null;
}


function formatMoney(value) {
  return Number(value || 0).toLocaleString("en-PK");
}


function ProviderPublicProfile() {
  const { providerId } = useParams();
  const navigate = useNavigate();

  const [provider, setProvider] = useState(null);
  const [loading, setLoading] = useState(true);
  const [favoriteLoading, setFavoriteLoading] = useState(false);
  const [isFavorite, setIsFavorite] = useState(false);
  const [error, setError] = useState("");

  let currentUser = null;

  try {
    currentUser = JSON.parse(
      localStorage.getItem("current_user") || "null",
    );
  } catch {
    currentUser = null;
  }

  const isCustomer = currentUser?.role === "customer";
  const canShowFavorite =
    !currentUser ||
    currentUser?.role === "customer";


  const loadProvider = useCallback(async () => {
    try {
      setLoading(true);
      setError("");

      const response = await api.get(
        `/providers/${providerId}`,
      );

      setProvider(getData(response));
    } catch (requestError) {
      setProvider(null);

      setError(
        requestError.response?.data?.message ||
          requestError.response?.data?.detail ||
          "Unable to load this provider profile.",
      );
    } finally {
      setLoading(false);
    }
  }, [providerId]);


  const loadFavoriteState = useCallback(async () => {
    const token = localStorage.getItem("access_token");

    if (!token || !isCustomer) {
      setIsFavorite(false);
      return;
    }

    try {
      const response = await api.get(
        "/users/me/favorites",
      );

      const data =
        response?.data?.data ??
        response?.data ??
        [];

      const favorites = Array.isArray(data)
        ? data
        : Array.isArray(data?.items)
          ? data.items
          : [];

      const providerIsFavorite = favorites.some(
        (favorite) =>
          Number(favorite.provider_id) ===
          Number(providerId),
      );

      setIsFavorite(providerIsFavorite);
    } catch (requestError) {
      /*
       * Do not block the provider page if favorites
       * cannot be loaded. The user can still browse.
       */
      setIsFavorite(false);
    }
  }, [providerId, isCustomer]);


  useEffect(() => {
    loadProvider();
    loadFavoriteState();
  }, [loadProvider, loadFavoriteState]);


  const toggleFavorite = async () => {
    const token = localStorage.getItem("access_token");

    if (!token) {
      navigate("/login", {
        state: {
          message:
            "Please sign in with a customer account to save providers.",
        },
      });
      return;
    }

    if (!isCustomer) {
      setError(
        "Only customer accounts can save providers to favorites.",
      );
      return;
    }

    try {
      setFavoriteLoading(true);
      setError("");

      if (isFavorite) {
        await api.delete(
          `/users/me/favorites/${providerId}`,
        );

        setIsFavorite(false);
      } else {
        await api.post(
          `/users/me/favorites/${providerId}`,
        );

        setIsFavorite(true);
      }
    } catch (requestError) {
      setError(
        requestError.response?.data?.message ||
          requestError.response?.data?.detail ||
          "Unable to update favorites.",
      );
    } finally {
      setFavoriteLoading(false);
    }
  };


  if (loading) {
    return (
      <main className="provider-public-page">
        <div className="provider-public-container">
          <div className="provider-public-state">
            <RefreshCw className="spin" size={34} />
            <h2>Loading provider profile...</h2>
          </div>
        </div>
      </main>
    );
  }


  if (!provider) {
    return (
      <main className="provider-public-page">
        <div className="provider-public-container">
          <div className="provider-public-state">
            <BriefcaseBusiness size={42} />
            <h2>Provider not found</h2>

            {error && (
              <p>{error}</p>
            )}

            <button
              type="button"
              className="button"
              onClick={() => navigate("/services")}
            >
              Back to services
            </button>
          </div>
        </div>
      </main>
    );
  }


  return (
    <main className="provider-public-page">
      <div className="provider-public-container">

        <button
          type="button"
          className="provider-public-back"
          onClick={() => navigate("/services")}
        >
          <ArrowLeft size={18} />
          Back to services
        </button>


        {error && (
          <div className="alert alert-error">
            {error}
          </div>
        )}


        {/* =================================================
            HERO
        ================================================= */}

        <section className="provider-public-hero">
          <div className="provider-public-avatar">
            <BriefcaseBusiness size={38} />
          </div>

          <div className="provider-public-hero-content">
            <span className="eyebrow">
              Verified professional
            </span>

            <h1>
              {provider.provider_name}
            </h1>

            <h2>
              {provider.business_name}
            </h2>

            <div className="provider-public-meta">
              <span>
                <Wrench size={17} />
                {provider.category}
              </span>

              <span>
                <MapPin size={17} />
                {provider.city || "Location not provided"}
              </span>
            </div>

            <div className="provider-public-rating">
              <Star
                size={20}
                fill="currentColor"
              />

              <strong>
                {Number(
                  provider.average_rating || 0,
                ).toFixed(1)}
              </strong>

              <span>
                ({provider.review_count || 0}{" "}
                {Number(provider.review_count || 0) === 1
                  ? "review"
                  : "reviews"})
              </span>
            </div>
          </div>

          {canShowFavorite && (
            <div className="provider-public-hero-actions">
              <button
                type="button"
                className={`provider-public-favorite ${
                  isFavorite ? "active" : ""
                }`}
                onClick={toggleFavorite}
                disabled={favoriteLoading}
              >
                <Heart
                  size={20}
                  fill={
                    isFavorite
                      ? "currentColor"
                      : "none"
                  }
                />

                {favoriteLoading
                  ? "Saving..."
                  : isFavorite
                    ? "Saved"
                    : "Favorite"}
              </button>
            </div>
          )}
        </section>


        {/* =================================================
            BUSINESS INFORMATION
        ================================================= */}

        <section className="provider-public-grid">
          <article className="provider-public-panel">
            <h2>About this provider</h2>

            <p className="provider-public-description">
              {provider.description ||
                "This provider has not added a business description yet."}
            </p>

            <dl className="provider-public-details">
              <div>
                <dt>Category</dt>
                <dd>{provider.category}</dd>
              </div>

              <div>
                <dt>Hourly rate</dt>
                <dd>
                  PKR{" "}
                  {formatMoney(provider.hourly_rate)}
                </dd>
              </div>

              <div>
                <dt>City</dt>
                <dd>
                  {provider.city || "Not provided"}
                </dd>
              </div>

              <div>
                <dt>Business address</dt>
                <dd>
                  {provider.address || "Not provided"}
                </dd>
              </div>
            </dl>
          </article>


          <article className="provider-public-panel">
            <h2>Rating overview</h2>

            <div className="provider-public-rating-large">
              <strong>
                {Number(
                  provider.average_rating || 0,
                ).toFixed(1)}
              </strong>

              <div>
                <div className="provider-public-stars">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <Star
                      key={star}
                      size={22}
                      fill={
                        star <=
                        Math.round(
                          Number(
                            provider.average_rating || 0,
                          ),
                        )
                          ? "currentColor"
                          : "none"
                      }
                    />
                  ))}
                </div>

                <span>
                  Based on {provider.review_count || 0}{" "}
                  customer reviews
                </span>
              </div>
            </div>
          </article>
        </section>


        {/* =================================================
            PORTFOLIO
        ================================================= */}

        <section className="provider-public-section">
          <div className="provider-public-section-heading">
            <div>
              <span className="eyebrow">
                Previous work
              </span>

              <h2>Portfolio</h2>
            </div>
          </div>

          {provider.portfolio?.length === 0 ? (
            <div className="provider-public-empty">
              <BriefcaseBusiness size={36} />
              <p>
                This provider has not added portfolio
                images yet.
              </p>
            </div>
          ) : (
            <div className="provider-public-portfolio-grid">
              {provider.portfolio?.map((image) => (
                <article
                  className="provider-public-portfolio-card"
                  key={image.id}
                >
                  <img
                    src={image.image_url}
                    alt={
                      image.caption ||
                      "Provider portfolio"
                    }
                  />

                  {image.caption && (
                    <p>{image.caption}</p>
                  )}
                </article>
              ))}
            </div>
          )}
        </section>


        {/* =================================================
            SERVICES
        ================================================= */}

        <section className="provider-public-section">
          <div className="provider-public-section-heading">
            <div>
              <span className="eyebrow">
                Available services
              </span>

              <h2>Services offered</h2>
            </div>
          </div>

          {provider.services?.length === 0 ? (
            <div className="provider-public-empty">
              <Wrench size={36} />
              <p>
                No active services are currently
                available.
              </p>
            </div>
          ) : (
            <div className="provider-public-services-grid">
              {provider.services?.map((service) => (
                <article
                  className="provider-public-service-card"
                  key={service.id}
                >
                  <div>
                    <span className="service-category">
                      {service.category_name ||
                        "Professional service"}
                    </span>

                    <h3>{service.title}</h3>

                    <p>
                      {service.description ||
                        "Professional service available for booking."}
                    </p>

                    <div className="provider-public-service-meta">
                      <span>
                        <Clock3 size={16} />
                        {service.duration_minutes || 60} min
                      </span>

                      <strong>
                        PKR{" "}
                        {formatMoney(service.price)}
                      </strong>
                    </div>
                  </div>

                  <button
  type="button"
  className="button button-full"
  onClick={() =>
    navigate(
      `/services?serviceId=${service.id}`,
    )
  }
>
  <CalendarDays size={18} />
  Book this service
</button>
                </article>
              ))}
            </div>
          )}
        </section>


        {/* =================================================
            REVIEWS
        ================================================= */}

        <section className="provider-public-section">
          <div className="provider-public-section-heading">
            <div>
              <span className="eyebrow">
                Customer feedback
              </span>

              <h2>
                Reviews ({provider.review_count || 0})
              </h2>
            </div>
          </div>

          {provider.reviews?.length === 0 ? (
            <div className="provider-public-empty">
              <Star size={36} />
              <p>
                This provider has not received reviews
                yet.
              </p>
            </div>
          ) : (
            <div className="provider-public-review-list">
              {provider.reviews?.map((review) => (
                <article
                  className="provider-public-review-card"
                  key={review.id}
                >
                  <div className="provider-public-review-header">
                    <strong>
                      {review.customer_name ||
                        "Verified customer"}
                    </strong>

                    <div className="provider-public-review-stars">
                      {[1, 2, 3, 4, 5].map(
                        (star) => (
                          <Star
                            key={star}
                            size={17}
                            fill={
                              star <=
                              Number(review.rating)
                                ? "currentColor"
                                : "none"
                            }
                          />
                        ),
                      )}
                    </div>
                  </div>

                  {review.comment && (
                    <p>{review.comment}</p>
                  )}
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}


export default ProviderPublicProfile;