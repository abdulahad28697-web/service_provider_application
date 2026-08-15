import { useCallback, useEffect, useState } from "react";
import {
  Heart,
  RefreshCw,
  Search,
  Star,
  Trash2,
  X,
  Clock3,
  Wrench,
} from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

import api from "../../api/api";

export default function FavoriteProviders() {
  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [removingId, setRemovingId] = useState(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const navigate = useNavigate();

  const [confirmModal, setConfirmModal] = useState({
    show: false,
    serviceId: null,
    title: "",
    message: "",
  });

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
          "Unable to load favorite services.",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadFavorites();
  }, [loadFavorites]);

  const triggerRemoveFavorite = (serviceId, serviceTitle) => {
    setConfirmModal({
      show: true,
      serviceId,
      title: "Remove Favorite",
      message: `Are you sure you want to remove "${serviceTitle}" from your favorites?`,
    });
  };

  const handleConfirmRemove = async () => {
    const serviceId = confirmModal.serviceId;
    if (!serviceId) return;

    setRemovingId(serviceId);
    setError("");
    setMessage("");
    setConfirmModal({ show: false, serviceId: null, title: "", message: "" });

    try {
      await api.delete(`/users/me/favorites/${serviceId}`);

      setFavorites((current) =>
        current.filter((item) => {
          const sId = item.service_id ?? item.id;
          return sId !== serviceId;
        }),
      );

      setMessage("Service removed from favorites.");
    } catch (requestError) {
      setError(
        requestError.response?.data?.message ||
          requestError.response?.data?.detail ||
          "Unable to remove this service from favorites.",
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
            <span className="eyebrow">Saved services</span>
            <h1>Favorite services</h1>
            <p>
              Quickly find and compare the offerings you saved.
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

            <h2>No favorite services yet</h2>

            <p>
              Browse available services and save the ones you may want to hire later.
            </p>

            <Link className="button" to="/services">
              <Search size={18} />
              Browse services
            </Link>
          </div>
        ) : (
          <div className="favorite-provider-grid">
            {favorites.map((item) => {
              const serviceId = item.service_id;
              const title = item.title || "Service offering";
              const price = Number(item.price || 0);
              const priceUnit = String(item.price_unit || "").replaceAll("_", " ");
              const duration = item.duration_minutes || 60;
              const categoryName = item.category_name || "Professional service";
              const providerName = item.provider_name || "Verified Provider";
              const rating = Number(item.provider_rating || 0);
              const reviewCount = Number(item.review_count || 0);
              const image = item.images?.[0];

              return (
                <article
                  className="favorite-provider-card"
                  key={item.id ?? serviceId}
                >
                  <div className="favorite-card-top" style={{ height: "140px", overflow: "hidden", position: "relative" }}>
                    {image ? (
                      <img
                        src={image.startsWith("http") ? image : `http://localhost:8000${image}`}
                        alt={title}
                        style={{ width: "100%", height: "100%", objectFit: "cover" }}
                      />
                    ) : (
                      <div style={{ display: "grid", width: "100%", height: "100%", placeItems: "center", background: "linear-gradient(145deg, #dbeafe, #eff6ff)", color: "#2563eb" }}>
                        <Wrench size={32} />
                      </div>
                    )}

                    <button
                      type="button"
                      className="favorite-remove-button"
                      aria-label={`Remove ${title} from favorites`}
                      title="Remove from favorites"
                      onClick={() =>
                        triggerRemoveFavorite(serviceId, title)
                      }
                      disabled={removingId === serviceId}
                      style={{ position: "absolute", top: "10px", right: "10px", zIndex: 10 }}
                    >
                      {removingId === serviceId ? (
                        <RefreshCw className="spin" size={18} />
                      ) : (
                        <Trash2 size={18} />
                      )}
                    </button>
                  </div>

                  <div className="favorite-card-content" style={{ padding: "20px" }}>
                    <span className="provider-category">
                      {categoryName}
                    </span>

                    <h2 style={{ fontSize: "18px", margin: "8px 0 4px", fontWeight: "700" }}>{title}</h2>

                    <div style={{ fontSize: "14px", color: "#64748b", marginBottom: "8px" }}>
                      Provided by: <strong>{providerName}</strong>
                    </div>

                    <div className="provider-card-meta" style={{ display: "flex", gap: "12px", fontSize: "13px", color: "#475569", marginBottom: "12px" }}>
                      <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                        <Star size={16} fill="currentColor" style={{ color: "#f59e0b" }} />
                        {rating.toFixed(1)} ({reviewCount} {reviewCount === 1 ? "review" : "reviews"})
                      </span>

                      <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                        <Clock3 size={16} />
                        {duration} min
                      </span>
                    </div>

                    <div className="favorite-card-footer" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingTop: "12px", borderTop: "1px solid #f1f5f9" }}>
                      <div className="favorite-rate">
                        <small style={{ display: "block", color: "#64748b", fontSize: "11px" }}>Price</small>
                        <strong style={{ fontSize: "16px", color: "#0f172a" }}>
                          PKR {price.toLocaleString()} <span style={{ fontSize: "12px", fontWeight: "normal", color: "#64748b" }}>/ {priceUnit}</span>
                        </strong>
                      </div>

                      <button
                        className="button button-small"
                        onClick={() => navigate(`/services?service=${serviceId}`)}
                      >
                        View & book
                      </button>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </div>

      {/* Modern Confirmation Modal Overlay */}
      {confirmModal.show && (
        <div className="modal-overlay" style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, backgroundColor: "rgba(15, 23, 42, 0.6)", backdropFilter: "blur(4px)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 9999 }}>
          <div className="modal-container" style={{ background: "#ffffff", padding: "24px", borderRadius: "16px", maxWidth: "440px", width: "90%", boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)" }}>
            <div className="modal-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <h2 style={{ fontSize: "20px", fontWeight: "700", color: "#0f172a", margin: 0 }}>{confirmModal.title}</h2>
              <button
                className="icon-button"
                onClick={() => setConfirmModal({ show: false, serviceId: null, title: "", message: "" })}
                style={{ border: "none", background: "none", cursor: "pointer", color: "#64748b" }}
              >
                <X size={20} />
              </button>
            </div>
            <div className="modal-body" style={{ marginBottom: "24px", color: "#475569", fontSize: "15px", lineHeight: "1.5" }}>
              <p>{confirmModal.message}</p>
            </div>
            <div className="modal-footer" style={{ display: "flex", justifyContent: "flex-end", gap: "12px" }}>
              <button
                className="button button-outline"
                onClick={() => setConfirmModal({ show: false, serviceId: null, title: "", message: "" })}
                style={{ padding: "10px 16px", borderRadius: "10px", fontWeight: "600", cursor: "pointer" }}
              >
                Cancel
              </button>
              <button
                className="button button-danger"
                onClick={handleConfirmRemove}
                style={{ padding: "10px 16px", borderRadius: "10px", fontWeight: "600", backgroundColor: "#dc2626", color: "#ffffff", border: "none", cursor: "pointer" }}
              >
                Remove
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}