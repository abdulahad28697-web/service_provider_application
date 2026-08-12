import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  ArrowLeft,
  CalendarDays,
  Clock3,
  MapPin,
  RefreshCw,
  Search,
  UserRound,
} from "lucide-react";

import { useNavigate } from "react-router-dom";

import api from "../../api/api";


function extractItems(response) {
  const data =
    response?.data?.data ??
    response?.data ??
    {};

  if (Array.isArray(data)) {
    return data;
  }

  if (Array.isArray(data?.items)) {
    return data.items;
  }

  return [];
}


function formatDate(value) {
  if (!value) {
    return "Not available";
  }

  return new Date(
    `${value}T00:00:00`,
  ).toLocaleDateString("en-PK", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}


function formatTime(value) {
  if (!value) {
    return "--";
  }

  const [hours, minutes] =
    value.split(":");

  const date = new Date();

  date.setHours(
    Number(hours),
    Number(minutes),
    0,
    0,
  );

  return date.toLocaleTimeString(
    "en-PK",
    {
      hour: "numeric",
      minute: "2-digit",
    },
  );
}


function formatStatus(value) {
  const status = String(
    value || "",
  ).toLowerCase();

  if (!status) {
    return "Unknown";
  }

  return (
    status.charAt(0).toUpperCase() +
    status.slice(1)
  );
}


export default function AdminBookings() {
  const navigate = useNavigate();

  const [bookings, setBookings] =
    useState([]);

  const [search, setSearch] =
    useState("");

  const [
    statusFilter,
    setStatusFilter,
  ] = useState("all");

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");


  const loadBookings =
    useCallback(async () => {
      try {
        setLoading(true);
        setError("");

        const response = await api.get(
          "/admin/bookings",
          {
            params: {
              page: 1,
              page_size: 100,
            },
          },
        );

        setBookings(
          extractItems(response),
        );
      } catch (requestError) {
        setError(
          requestError.response?.data?.message ||
            requestError.response?.data?.detail ||
            "Unable to load platform bookings.",
        );
      } finally {
        setLoading(false);
      }
    }, []);


  useEffect(() => {
    loadBookings();
  }, [loadBookings]);


  const bookingCounts = useMemo(() => {
    return bookings.reduce(
      (counts, booking) => {
        const status = String(
          booking.status || "",
        ).toLowerCase();

        counts.all += 1;

        if (
          counts[status] !== undefined
        ) {
          counts[status] += 1;
        }

        return counts;
      },
      {
        all: 0,
        pending: 0,
        accepted: 0,
        completed: 0,
        rejected: 0,
        cancelled: 0,
      },
    );
  }, [bookings]);


  const filteredBookings =
    useMemo(() => {
      const keyword =
        search.trim().toLowerCase();

      return bookings.filter(
        (booking) => {
          const status = String(
            booking.status || "",
          ).toLowerCase();

          const matchesStatus =
            statusFilter === "all" ||
            status === statusFilter;

          const matchesSearch =
            !keyword ||
            [
              booking.reference_code,
              booking.service_title,
              booking.customer_name,
              booking.customer_email,
              booking.customer_phone,
              booking.location,
              booking.provider_id,
            ]
              .filter(
                (value) =>
                  value !== null &&
                  value !== undefined,
              )
              .some((value) =>
                String(value)
                  .toLowerCase()
                  .includes(keyword),
              );

          return (
            matchesStatus &&
            matchesSearch
          );
        },
      );
    }, [
      bookings,
      search,
      statusFilter,
    ]);


  return (
    <main className="admin-page">
      <div className="admin-container">

        <button
          type="button"
          className="admin-back-button"
          onClick={() =>
            navigate("/admin")
          }
        >
          <ArrowLeft size={18} />
          Back to dashboard
        </button>


        <section className="admin-title-row">
          <div>
            <span className="eyebrow">
              Platform bookings
            </span>

            <h1>
              Booking management
            </h1>

            <p>
              Search and review bookings
              created across ServiceHub.
            </p>
          </div>

          <button
            type="button"
            className="button"
            onClick={loadBookings}
            disabled={loading}
          >
            <RefreshCw
              size={18}
              className={
                loading
                  ? "spin"
                  : ""
              }
            />

            Refresh
          </button>
        </section>


        {error && (
          <div className="alert alert-error">
            {error}
          </div>
        )}


        <section className="admin-booking-summary">
          {[
            ["all", "All"],
            ["pending", "Pending"],
            ["accepted", "Accepted"],
            ["completed", "Completed"],
            ["rejected", "Rejected"],
            ["cancelled", "Cancelled"],
          ].map(([value, label]) => (
            <button
              type="button"
              key={value}
              className={
                statusFilter === value
                  ? "active"
                  : ""
              }
              onClick={() =>
                setStatusFilter(value)
              }
            >
              <span>{label}</span>
              <strong>
                {bookingCounts[value]}
              </strong>
            </button>
          ))}
        </section>


        <section className="admin-booking-toolbar">
          <div className="admin-booking-search">
            <Search size={18} />

            <input
              type="search"
              value={search}
              onChange={(event) =>
                setSearch(
                  event.target.value,
                )
              }
              placeholder="Search reference, customer, service, location..."
            />
          </div>

          <select
            value={statusFilter}
            onChange={(event) =>
              setStatusFilter(
                event.target.value,
              )
            }
          >
            <option value="all">
              All statuses
            </option>

            <option value="pending">
              Pending
            </option>

            <option value="accepted">
              Accepted
            </option>

            <option value="completed">
              Completed
            </option>

            <option value="rejected">
              Rejected
            </option>

            <option value="cancelled">
              Cancelled
            </option>
          </select>
        </section>


        {loading ? (
          <div className="page-loading">
            <RefreshCw
              className="spin"
              size={30}
            />

            <p>
              Loading bookings...
            </p>
          </div>
        ) : filteredBookings.length ===
          0 ? (
          <div className="admin-empty-state">
            <CalendarDays size={42} />

            <h3>
              No bookings found
            </h3>

            <p>
              Try another search or
              status filter.
            </p>
          </div>
        ) : (
          <div className="admin-booking-list">

            {filteredBookings.map(
              (booking) => {
                const status =
                  String(
                    booking.status || "",
                  ).toLowerCase();

                return (
                  <article
                    className="admin-booking-card"
                    key={booking.id}
                  >

                    <div className="admin-booking-card-header">
                      <div>
                        <span className="booking-reference">
                          {booking.reference_code ||
                            `#${booking.id}`}
                        </span>

                        <h2>
                          {booking.service_title ||
                            "Service booking"}
                        </h2>
                      </div>

                      <span
                        className={`provider-booking-status status-${status}`}
                      >
                        {formatStatus(
                          status,
                        )}
                      </span>
                    </div>


                    <div className="admin-booking-customer">

                      <div>
                        <UserRound
                          size={18}
                        />

                        <span>
                          <small>
                            Customer
                          </small>

                          <strong>
                            {booking.customer_name ||
                              "Not provided"}
                          </strong>
                        </span>
                      </div>


                      <div>
                        <span>
                          <small>
                            Email
                          </small>

                          <strong>
                            {booking.customer_email ||
                              "Not provided"}
                          </strong>
                        </span>
                      </div>


                      <div>
                        <span>
                          <small>
                            Phone
                          </small>

                          <strong>
                            {booking.customer_phone ||
                              "Not provided"}
                          </strong>
                        </span>
                      </div>

                    </div>


                    <div className="admin-booking-info-grid">

                      <div>
                        <CalendarDays
                          size={18}
                        />

                        <span>
                          <small>
                            Date
                          </small>

                          <strong>
                            {formatDate(
                              booking.scheduled_date,
                            )}
                          </strong>
                        </span>
                      </div>


                      <div>
                        <Clock3
                          size={18}
                        />

                        <span>
                          <small>
                            Time
                          </small>

                          <strong>
                            {formatTime(
                              booking.scheduled_start,
                            )}{" "}
                            –{" "}
                            {formatTime(
                              booking.scheduled_end,
                            )}
                          </strong>
                        </span>
                      </div>


                      <div>
                        <MapPin
                          size={18}
                        />

                        <span>
                          <small>
                            Location
                          </small>

                          <strong>
                            {booking.location ||
                              "Not provided"}
                          </strong>
                        </span>
                      </div>

                    </div>


                    {booking.customer_notes && (
                      <div className="admin-booking-notes">
                        <span>
                          Customer notes
                        </span>

                        <p>
                          {booking.customer_notes}
                        </p>
                      </div>
                    )}


                    <div className="admin-booking-footer">

                      <div>
                        <span>
                          Total price
                        </span>

                        <strong>
                          PKR{" "}
                          {Number(
                            booking.total_price ||
                              0,
                          ).toLocaleString()}
                        </strong>
                      </div>


                      <div>
                        <span>
                          Provider ID
                        </span>

                        <strong>
                          #
                          {booking.provider_id}
                        </strong>
                      </div>


                      <div>
                        <span>
                          Booking ID
                        </span>

                        <strong>
                          #{booking.id}
                        </strong>
                      </div>

                    </div>

                  </article>
                );
              },
            )}

          </div>
        )}

      </div>
    </main>
  );
}