import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ArrowLeft,
  CalendarDays,
  CheckCircle2,
  Clock3,
  MessageSquareText,
  RefreshCw,
  Search,
  Star,
  User,
} from "lucide-react";
import { Link } from "react-router-dom";

import api from "../../api/api";

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString("en-PK", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export default function AdminReviews() {
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [ratingFilter, setRatingFilter] = useState("all");

  const loadReviews = useCallback(async (isRefresh = false) => {
    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError("");

    try {
      const response = await api.get("/reviews", {
        params: {
          limit: 200,
        },
      });

      const data = response.data?.data || [];
      setReviews(Array.isArray(data) ? data : []);
    } catch (requestError) {
      setError(
        requestError.response?.data?.message ||
          requestError.response?.data?.detail ||
          "Unable to load customer reviews.",
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadReviews();
  }, [loadReviews]);

  const filteredReviews = useMemo(() => {
    const q = search.trim().toLowerCase();

    return reviews.filter((review) => {
      const ratingMatch =
        ratingFilter === "all"
          ? true
          : ratingFilter === "5"
            ? Number(review.rating) >= 5
            : ratingFilter === "4"
              ? Number(review.rating) >= 4 && Number(review.rating) < 5
              : ratingFilter === "3"
                ? Number(review.rating) >= 3 && Number(review.rating) < 4
                : Number(review.rating) < 3;

      if (!ratingMatch) return false;

      if (!q) return true;

      return (
        review.comment?.toLowerCase().includes(q) ||
        String(review.booking_id || "").includes(q) ||
        String(review.customer_id || "").includes(q)
      );
    });
  }, [reviews, search, ratingFilter]);

  const averageRating = useMemo(() => {
    if (!reviews.length) return "0.0";
    const sum = reviews.reduce(
      (acc, r) => acc + Number(r.rating || 0),
      0,
    );
    return (sum / reviews.length).toFixed(1);
  }, [reviews]);

  return (
    <main className="admin-page">
      <div className="admin-container">
        {/* HEADER */}
        <div className="admin-page-header">
          <div>
            <Link className="admin-back-link" to="/admin">
              <ArrowLeft size={17} />
              Admin dashboard
            </Link>

            <span className="eyebrow">Platform quality & trust</span>
            <h1>Review management</h1>
            <p>
              Inspect customer ratings and feedback across all completed service
              bookings.
            </p>
          </div>

          <button
            type="button"
            className="button button-outline"
            onClick={() => loadReviews(true)}
            disabled={loading || refreshing}
          >
            <RefreshCw
              size={16}
              className={refreshing ? "spin" : ""}
            />
            {refreshing ? "Refreshing..." : "Refresh"}
          </button>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        {/* STATS */}
        <section className="admin-stat-grid">
          <article className="admin-stat-card">
            <div className="admin-stat-icon blue">
              <MessageSquareText size={22} />
            </div>
            <div>
              <span>Total reviews</span>
              <strong>{reviews.length}</strong>
            </div>
          </article>

          <article className="admin-stat-card">
            <div className="admin-stat-icon amber">
              <Star size={22} />
            </div>
            <div>
              <span>Average rating</span>
              <strong>{averageRating} / 5.0</strong>
            </div>
          </article>

          <article className="admin-stat-card">
            <div className="admin-stat-icon green">
              <CheckCircle2 size={22} />
            </div>
            <div>
              <span>5-Star reviews</span>
              <strong>
                {reviews.filter((r) => Number(r.rating) >= 5).length}
              </strong>
            </div>
          </article>
        </section>

        {/* PANEL */}
        <section className="admin-panel">
          <div className="admin-toolbar">
            <div className="admin-filter-tabs">
              <button
                type="button"
                className={ratingFilter === "all" ? "active" : ""}
                onClick={() => setRatingFilter("all")}
              >
                All ratings
                <span>{reviews.length}</span>
              </button>

              <button
                type="button"
                className={ratingFilter === "5" ? "active" : ""}
                onClick={() => setRatingFilter("5")}
              >
                5 Stars
                <span>
                  {reviews.filter((r) => Number(r.rating) >= 5).length}
                </span>
              </button>

              <button
                type="button"
                className={ratingFilter === "4" ? "active" : ""}
                onClick={() => setRatingFilter("4")}
              >
                4 Stars
                <span>
                  {
                    reviews.filter(
                      (r) => Number(r.rating) >= 4 && Number(r.rating) < 5,
                    ).length
                  }
                </span>
              </button>

              <button
                type="button"
                className={ratingFilter === "low" ? "active" : ""}
                onClick={() => setRatingFilter("low")}
              >
                Below 4 Stars
                <span>
                  {reviews.filter((r) => Number(r.rating) < 4).length}
                </span>
              </button>
            </div>

            <label className="admin-search">
              <Search size={18} />
              <input
                type="search"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search reviews by comment or booking ID..."
              />
            </label>
          </div>

          {loading ? (
            <div className="admin-empty-state">
              <Clock3 size={35} />
              <h2>Loading reviews...</h2>
            </div>
          ) : filteredReviews.length === 0 ? (
            <div className="admin-empty-state">
              <CheckCircle2 size={38} />
              <h2>No reviews found</h2>
              <p>There are no customer reviews matching your filters.</p>
            </div>
          ) : (
            <div className="admin-review-grid">
              {filteredReviews.map((review) => (
                <article className="admin-review-card" key={review.id}>
                  <div className="admin-review-card-header">
                    <div className="admin-review-stars">
                      {[1, 2, 3, 4, 5].map((star) => (
                        <Star
                          key={star}
                          size={16}
                          className={
                            star <= Number(review.rating)
                              ? "star-filled"
                              : "star-empty"
                          }
                          fill={
                            star <= Number(review.rating)
                              ? "currentColor"
                              : "none"
                          }
                        />
                      ))}
                      <span className="admin-review-score">
                        {Number(review.rating).toFixed(1)}
                      </span>
                    </div>

                    <span className="admin-review-date">
                      <CalendarDays size={14} />
                      {formatDate(review.created_at)}
                    </span>
                  </div>

                  <p className="admin-review-comment">
                    "{review.comment || "No written comment provided."}"
                  </p>

                  <div className="admin-review-meta">
                    <span>
                      <User size={14} />
                      Customer ID: #{review.customer_id}
                    </span>
                    <span>Booking ID: #{review.booking_id}</span>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
