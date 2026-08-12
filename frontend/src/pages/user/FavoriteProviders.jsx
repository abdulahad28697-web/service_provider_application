import { useCallback, useEffect, useState } from "react";
import {
  Heart,
  MapPin,
  RefreshCw,
  Search,
  Star,
  Trash2,
} from "lucide-react";
import { Link } from "react-router-dom";

import api from "../../api/api";

export default function FavoriteProviders() {
  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [removingId, setRemovingId] = useState(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const loadFavorites = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const response = await api.get("/users/me/favorites");
      setFavorites(response.data?.data ?? []);
    } catch (requestError) {
      setError(
        requestError.response?.data?.message ||
          requestError.response?.data?.detail ||
          "Unable to load favorite providers.",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadFavorites();
  }, [loadFavorites]);

  const removeFavorite = async (providerId) => {
    const confirmed = window.confirm(
      "Remove this provider from your favorites?",
    );

    if (!confirmed) {
      return;
    }

    setRemovingId(providerId);
    setError("");
    setMessage("");

    try {
      await api.delete(`/users/me/favorites/${providerId}`);

      setFavorites((current) =>
        current.filter((item) => {
          const provider = item.provider ?? item;
          const itemProviderId = item.provider_id ?? provider.id;

          return itemProviderId !== providerId;
        }),
      );

      setMessage("Provider removed from favorites.");
    } catch (requestError) {
      setError(
        requestError.response?.data?.message ||
          requestError.response?.data?.detail ||
          "Unable to remove this provider.",
      );
    } finally {
      setRemovingId(null);
    }
  };

  return (
    <section className="favorites-page">
      <div className="favorites-container">
        <header className="favorites-header">
          <div>
            <span className="eyebrow">Saved providers</span>
            <h1>Favorite providers</h1>
            <p>
              Quickly find and compare the professionals you saved.
            </p>
          </div>

          <button
            type="button"
            className="button button-outline favorites-refresh"
            onClick={loadFavorites}
            disabled={loading}
          >
            <RefreshCw
              size={18}
              className={loading ? "spin" : ""}
            />
            Refresh
          </button>
        </header>

        {error && (
          <div className="alert alert-error">{error}</div>
        )}

        {message && (
          <div className="alert alert-success">{message}</div>
        )}

        {loading ? (
          <div className="empty-state favorites-empty-state">
            <RefreshCw className="spin" size={34} />
            <h2>Loading favorites...</h2>
          </div>
        ) : favorites.length === 0 ? (
          <div className="empty-state favorites-empty-state">
            <div className="empty-state-icon">
              <Heart size={30} />
            </div>

            <h2>No favorite providers yet</h2>

            <p>
              Browse available services and save providers you may
              want to hire later.
            </p>

            <Link className="button" to="/services">
              <Search size={18} />
              Browse services
            </Link>
          </div>
        ) : (
          <div className="favorite-provider-grid">
            {favorites.map((item) => {
              const provider = item.provider ?? item;
              const providerId =
                item.provider_id ?? provider.id;

              const name =
                provider.business_name ||
                provider.full_name ||
                "Service provider";

              const rating = Number(provider.rating || 0);
              const hourlyRate = Number(
                provider.hourly_rate || 0,
              );

              return (
                <article
                  className="favorite-provider-card"
                  key={item.id ?? providerId}
                >
                  <div className="favorite-card-top">
                    <div className="provider-avatar">
                      {name.charAt(0).toUpperCase()}
                    </div>

                    <button
                      type="button"
                      className="favorite-remove-button"
                      aria-label={`Remove ${name} from favorites`}
                      title="Remove from favorites"
                      onClick={() =>
                        removeFavorite(providerId)
                      }
                      disabled={removingId === providerId}
                    >
                      {removingId === providerId ? (
                        <RefreshCw className="spin" size={18} />
                      ) : (
                        <Trash2 size={18} />
                      )}
                    </button>
                  </div>

                  <div className="favorite-card-content">
                    <span className="provider-category">
                      {provider.category ||
                        "Professional service"}
                    </span>

                    <h2>{name}</h2>

                    <div className="provider-card-meta">
                      <span>
                        <Star size={17} />
                        {rating.toFixed(1)}
                      </span>

                      <span>
                        <MapPin size={17} />
                        {provider.city ||
                          "Location not provided"}
                      </span>
                    </div>

                    <p className="provider-description">
                      {provider.description ||
                        "Trusted local professional ready to help with your service needs."}
                    </p>

                    <div className="favorite-card-footer">
                      <div className="favorite-rate">
                        <small>Hourly rate</small>
                        <strong>
                          PKR {hourlyRate.toLocaleString()}
                        </strong>
                      </div>

                      <Link
                        className="button button-small"
                        to={`/services?provider=${providerId}`}
                      >
                        View services
                      </Link>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}