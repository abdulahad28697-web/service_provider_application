import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  CalendarClock,
  CalendarDays,
  CheckCircle2,
  Clock,
  CreditCard,
  History,
  MapPin,
  MessageCircle,
  RefreshCw,
  Smartphone,
  Star,
  WalletCards,
  X,
  XCircle,
} from "lucide-react";

import api from "../../api/api";


const WEEKDAYS = [
  "sunday",
  "monday",
  "tuesday",
  "wednesday",
  "thursday",
  "friday",
  "saturday",
];


function normalizeTime(value) {
  return String(value || "").slice(0, 5);
}


function formatSlotTime(value) {
  if (!value) return "";

  const [hours, minutes] = normalizeTime(value).split(":");
  const date = new Date();

  date.setHours(Number(hours), Number(minutes), 0, 0);

  return date.toLocaleTimeString("en-PK", {
    hour: "numeric",
    minute: "2-digit",
  });
}


function extractBookings(response) {
  const data = response?.data?.data;

  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.items)) return data.items;
  if (Array.isArray(data?.results)) return data.results;

  return [];
}


function extractReviews(response) {
  const data = response?.data?.data;

  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.items)) return data.items;
  if (Array.isArray(data?.results)) return data.results;

  return [];
}


function extractPayments(response) {
  const data =
    response?.data?.data ??
    response?.data ??
    [];

  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.items)) return data.items;
  if (Array.isArray(data?.results)) return data.results;

  return [];
}


function formatPaymentMethod(value) {
  const method = String(value || "").toLowerCase();

  if (method === "jazzcash") return "JazzCash";
  if (method === "easypaisa") return "Easypaisa";
  if (method === "cash") return "Cash on service";

  return method || "Not selected";
}


function formatPaymentStatus(value) {
  const status = String(value || "").toLowerCase();

  if (!status) return "Unpaid";

  return (
    status.charAt(0).toUpperCase() +
    status.slice(1)
  );
}


function formatDate(value) {
  if (!value) return "Date unavailable";

  return new Date(
    `${value}T00:00:00`,
  ).toLocaleDateString("en-PK", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}


function formatTime(value) {
  if (!value) return "Time unavailable";

  const [hours, minutes] = value.split(":");

  const date = new Date();

  date.setHours(
    Number(hours),
    Number(minutes),
  );

  return date.toLocaleTimeString("en-PK", {
    hour: "numeric",
    minute: "2-digit",
  });
}


function formatPrice(value) {
  const price = Number(value ?? 0);

  return new Intl.NumberFormat("en-PK", {
    style: "currency",
    currency: "PKR",
    maximumFractionDigits: 0,
  }).format(price);
}


function BookingHistory() {
  const [bookings, setBookings] = useState([]);

  const [reviewsByBooking, setReviewsByBooking] =
    useState({});

  const [statusFilter, setStatusFilter] =
    useState("");

  const [loading, setLoading] = useState(true);

  const [cancellingId, setCancellingId] =
    useState(null);

  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  // ---------------------------------------------------------
  // PAYMENTS
  // ---------------------------------------------------------

  const [paymentsByBooking, setPaymentsByBooking] =
    useState({});

  const [paymentBooking, setPaymentBooking] =
    useState(null);

  const [paymentMethod, setPaymentMethod] =
    useState("cash");

  const [paymentCheckout, setPaymentCheckout] =
    useState(null);

  const [paymentError, setPaymentError] =
    useState("");

  const [paymentSubmitting, setPaymentSubmitting] =
    useState(false);

  const [paymentCompleting, setPaymentCompleting] =
    useState(false);

  // ---------------------------------------------------------
  // RESCHEDULE MODAL
  // ---------------------------------------------------------

  const [rescheduleBooking, setRescheduleBooking] =
    useState(null);

  const [rescheduleForm, setRescheduleForm] =
    useState({
      scheduled_date: "",
      scheduled_start: "",
    });

  const [
    rescheduleProviderAvailability,
    setRescheduleProviderAvailability,
  ] = useState([]);

  const [
    rescheduleAvailableTimeSlots,
    setRescheduleAvailableTimeSlots,
  ] = useState([]);

  const [
    rescheduleAvailabilityLoading,
    setRescheduleAvailabilityLoading,
  ] = useState(false);

  const [rescheduleSlotsLoading, setRescheduleSlotsLoading] =
    useState(false);

  const [rescheduleError, setRescheduleError] =
    useState("");

  const [rescheduling, setRescheduling] =
    useState(false);

  // ---------------------------------------------------------
  // REVIEW MODAL
  // ---------------------------------------------------------

  const [reviewBooking, setReviewBooking] =
    useState(null);

  const [reviewRating, setReviewRating] =
    useState(0);

  const [hoverRating, setHoverRating] =
    useState(0);

  const [reviewComment, setReviewComment] =
    useState("");

  const [submittingReview, setSubmittingReview] =
    useState(false);

  // ---------------------------------------------------------
  // CANCEL MODAL
  // ---------------------------------------------------------

  const [cancelModal, setCancelModal] = useState({
    show: false,
    bookingId: null,
    reason: "",
  });

  // ---------------------------------------------------------
  // LOAD BOOKINGS + REVIEWS
  // ---------------------------------------------------------

  const loadBookings = useCallback(async () => {
    try {
      setLoading(true);
      setError("");

      const params = {};

      if (statusFilter) {
        params.status = statusFilter;
      }

      const [
        bookingsResponse,
        reviewsResponse,
        paymentsResponse,
      ] = await Promise.all([
        api.get("/bookings", {
          params,
        }),

        api.get("/reviews", {
          params: {
            limit: 500,
          },
        }),

        api.get("/payments/me").catch(() => ({
          data: {
            data: [],
          },
        })),
      ]);

      const bookingItems =
        extractBookings(bookingsResponse);

      const reviewItems =
        extractReviews(reviewsResponse);

      const paymentItems =
        extractPayments(paymentsResponse);

      setBookings(bookingItems);

      /*
       * Keep reviews indexed by booking ID.
       *
       * This allows us to know whether a completed
       * booking has already been reviewed.
       */
      const reviewMap = {};

      reviewItems.forEach((review) => {
        reviewMap[
          Number(review.booking_id)
        ] = review;
      });

      setReviewsByBooking(reviewMap);

      const paymentMap = {};

      paymentItems.forEach((payment) => {
        paymentMap[
          Number(payment.booking_id)
        ] = payment;
      });

      setPaymentsByBooking(paymentMap);
    } catch (err) {
      setError(
        err.response?.data?.message ||
          err.response?.data?.detail ||
          "Unable to load your booking history.",
      );
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);


  useEffect(() => {
    loadBookings();
  }, [loadBookings]);


  // ---------------------------------------------------------
  // PAYMENT
  // ---------------------------------------------------------

  const canCreatePayment = (booking) => {
    const status = String(
      booking?.status || "",
    ).toLowerCase();

    return ![
      "cancelled",
      "rejected",
    ].includes(status);
  };


  const openPayment = (booking) => {
    setPaymentBooking(booking);
    setPaymentMethod("cash");
    setPaymentCheckout(null);
    setPaymentError("");
    setError("");
    setMessage("");
  };


  const closePayment = () => {
    if (
      paymentSubmitting ||
      paymentCompleting
    ) {
      return;
    }

    setPaymentBooking(null);
    setPaymentMethod("cash");
    setPaymentCheckout(null);
    setPaymentError("");
  };


  const createPayment = async (event) => {
    event.preventDefault();

    if (!paymentBooking) {
      return;
    }

    try {
      setPaymentSubmitting(true);
      setPaymentError("");
      setError("");
      setMessage("");

      const response = await api.post(
        "/payments/checkout",
        {
          booking_id: paymentBooking.id,
          payment_method: paymentMethod,
        },
      );

      const checkout =
        response?.data?.data ??
        response?.data;

      setPaymentCheckout(checkout);

      if (paymentMethod === "cash") {
        setMessage(
          "Cash on service selected successfully.",
        );

        setPaymentBooking(null);
        setPaymentCheckout(null);

        await loadBookings();
      }
    } catch (requestError) {
      setPaymentError(
        requestError.response?.data?.message ||
          requestError.response?.data?.detail ||
          "Unable to create payment checkout.",
      );
    } finally {
      setPaymentSubmitting(false);
    }
  };


  const completeDigitalPayment = async () => {
    if (!paymentCheckout?.payment_id) {
      return;
    }

    try {
      setPaymentCompleting(true);
      setPaymentError("");
      setError("");
      setMessage("");

      const response = await api.post(
        `/payments/${paymentCheckout.payment_id}/simulate-success`,
      );

      const payment =
        response?.data?.data ??
        response?.data;

      setPaymentsByBooking((current) => ({
        ...current,
        [Number(payment.booking_id)]:
          payment,
      }));

      setMessage(
        `${formatPaymentMethod(
          payment.payment_method,
        )} payment completed successfully.`,
      );

      setPaymentBooking(null);
      setPaymentCheckout(null);
      setPaymentMethod("cash");

      await loadBookings();
    } catch (requestError) {
      setPaymentError(
        requestError.response?.data?.message ||
          requestError.response?.data?.detail ||
          "Unable to complete digital payment.",
      );
    } finally {
      setPaymentCompleting(false);
    }
  };


  // ---------------------------------------------------------
  // CANCELLATION
  // ---------------------------------------------------------

  const cancelBooking = (bookingId) => {
    setCancelModal({
      show: true,
      bookingId,
      reason: "",
    });
  };

  const handleConfirmCancel = async () => {
    const { bookingId, reason } = cancelModal;
    if (!bookingId) return;

    setCancelModal({
      show: false,
      bookingId: null,
      reason: "",
    });

    try {
      setCancellingId(bookingId);
      setError("");
      setMessage("");

      await api.post(
        `/bookings/${bookingId}/cancel`,
        {
          reason:
            reason.trim() || null,
        },
      );

      setMessage(
        "Booking cancelled successfully.",
      );

      await loadBookings();
    } catch (err) {
      setError(
        err.response?.data?.message ||
          err.response?.data?.detail ||
          "Unable to cancel this booking.",
      );
    } finally {
      setCancellingId(null);
    }
  };


  const canCancel = (status) =>
    ["pending", "accepted"].includes(
      String(status).toLowerCase(),
    );


  // ---------------------------------------------------------
  // RESCHEDULE
  // ---------------------------------------------------------

  const canReschedule = (status) =>
    ["pending", "accepted"].includes(
      String(status || "").toLowerCase(),
    );


  const openReschedule = async (booking) => {
    setRescheduleBooking(booking);

    setRescheduleForm({
      scheduled_date: booking.scheduled_date || "",
      scheduled_start: normalizeTime(
        booking.scheduled_start,
      ),
    });

    setRescheduleError("");
    setMessage("");
    setError("");
    setRescheduleAvailableTimeSlots([]);
    setRescheduleProviderAvailability([]);
    setRescheduleAvailabilityLoading(true);

    try {
      const response = await api.get(
        `/providers/${booking.provider_id}/availability`,
      );

      const data =
        response?.data?.data ??
        response?.data ??
        [];

      const rows = Array.isArray(data)
        ? data
        : Array.isArray(data?.items)
          ? data.items
          : [];

      setRescheduleProviderAvailability(
        rows.map((slot) => ({
          ...slot,
          day_of_week: String(
            slot.day_of_week || "",
          ).toLowerCase(),
          start_time: normalizeTime(slot.start_time),
          end_time: normalizeTime(slot.end_time),
        })),
      );
    } catch (requestError) {
      setRescheduleError(
        requestError.response?.data?.message ||
          requestError.response?.data?.detail ||
          "Unable to load provider availability.",
      );
    } finally {
      setRescheduleAvailabilityLoading(false);
    }
  };


  const closeReschedule = () => {
    if (rescheduling) {
      return;
    }

    setRescheduleBooking(null);
    setRescheduleForm({
      scheduled_date: "",
      scheduled_start: "",
    });
    setRescheduleProviderAvailability([]);
    setRescheduleAvailableTimeSlots([]);
    setRescheduleError("");
  };


  const updateRescheduleField = (event) => {
    const { name, value } = event.target;

    setRescheduleForm((current) => ({
      ...current,
      [name]: value,
      ...(name === "scheduled_date"
        ? { scheduled_start: "" }
        : {}),
    }));

    if (name === "scheduled_date") {
      setRescheduleAvailableTimeSlots([]);
      setRescheduleError("");
    }
  };


  const selectedRescheduleAvailability = (() => {
    if (!rescheduleForm.scheduled_date) {
      return null;
    }

    const selectedDate = new Date(
      `${rescheduleForm.scheduled_date}T00:00:00`,
    );

    const weekday =
      WEEKDAYS[selectedDate.getDay()];

    return (
      rescheduleProviderAvailability.find(
        (slot) =>
          slot.day_of_week === weekday &&
          slot.is_available !== false,
      ) || null
    );
  })();


  useEffect(() => {
    const loadRescheduleSlots = async () => {
      if (
        !rescheduleBooking ||
        !rescheduleForm.scheduled_date ||
        !selectedRescheduleAvailability
      ) {
        setRescheduleAvailableTimeSlots([]);
        return;
      }

      try {
        setRescheduleSlotsLoading(true);
        setRescheduleError("");

        const response = await api.get(
          `/providers/${rescheduleBooking.provider_id}/available-slots`,
          {
            params: {
              service_id:
                rescheduleBooking.service_id,
              date:
                rescheduleForm.scheduled_date,
            },
          },
        );

        const payload =
          response?.data?.data ??
          response?.data ??
          {};

        const slots = Array.isArray(payload)
          ? payload
          : Array.isArray(payload?.slots)
            ? payload.slots
            : [];

        const normalizedSlots = slots.map(
          (slot) => normalizeTime(slot),
        );

        /*
         * The public free-slot endpoint may hide the booking's
         * current slot because that booking already occupies it.
         * The reschedule API itself excludes the current booking,
         * so keep the existing start time selectable when the
         * customer stays on the same date.
         */
        const currentSlot = normalizeTime(
          rescheduleBooking.scheduled_start,
        );

        if (
          rescheduleForm.scheduled_date ===
            rescheduleBooking.scheduled_date &&
          currentSlot &&
          !normalizedSlots.includes(currentSlot)
        ) {
          normalizedSlots.push(currentSlot);
        }

        normalizedSlots.sort();

        setRescheduleAvailableTimeSlots(
          normalizedSlots,
        );
      } catch (requestError) {
        setRescheduleAvailableTimeSlots([]);

        setRescheduleError(
          requestError.response?.data?.message ||
            requestError.response?.data?.detail ||
            "Unable to load available booking times.",
        );
      } finally {
        setRescheduleSlotsLoading(false);
      }
    };

    loadRescheduleSlots();
  }, [
    rescheduleBooking,
    rescheduleForm.scheduled_date,
    selectedRescheduleAvailability,
  ]);


  const submitReschedule = async (event) => {
    event.preventDefault();

    if (!rescheduleBooking) {
      return;
    }

    if (
      !rescheduleForm.scheduled_date ||
      !rescheduleForm.scheduled_start
    ) {
      setRescheduleError(
        "Please select a new date and available start time.",
      );
      return;
    }

    try {
      setRescheduling(true);
      setRescheduleError("");
      setError("");
      setMessage("");

      await api.patch(
        `/bookings/${rescheduleBooking.id}/reschedule`,
        {
          scheduled_date:
            rescheduleForm.scheduled_date,
          scheduled_start:
            rescheduleForm.scheduled_start,
        },
      );

      setMessage(
        "Booking rescheduled successfully. The provider has been notified.",
      );

      setRescheduleBooking(null);
      setRescheduleForm({
        scheduled_date: "",
        scheduled_start: "",
      });
      setRescheduleProviderAvailability([]);
      setRescheduleAvailableTimeSlots([]);

      await loadBookings();
    } catch (requestError) {
      setRescheduleError(
        requestError.response?.data?.message ||
          requestError.response?.data?.detail ||
          "Unable to reschedule this booking.",
      );
    } finally {
      setRescheduling(false);
    }
  };


  // ---------------------------------------------------------
  // REVIEW
  // ---------------------------------------------------------

  const openReview = (booking) => {
    setReviewBooking(booking);
    setReviewRating(0);
    setHoverRating(0);
    setReviewComment("");
    setError("");
    setMessage("");
  };


  const closeReview = () => {
    if (submittingReview) {
      return;
    }

    setReviewBooking(null);
    setReviewRating(0);
    setHoverRating(0);
    setReviewComment("");
  };


  const submitReview = async (event) => {
    event.preventDefault();

    if (!reviewBooking) {
      return;
    }

    if (
      reviewRating < 1 ||
      reviewRating > 5
    ) {
      setError(
        "Please select a rating from 1 to 5 stars.",
      );

      return;
    }

    try {
      setSubmittingReview(true);
      setError("");
      setMessage("");

      const response = await api.post(
        "/reviews",
        {
          booking_id: reviewBooking.id,
          rating: reviewRating,
          comment:
            reviewComment.trim(),
        },
      );

      const review =
        response?.data?.data ??
        response?.data;

      setReviewsByBooking((current) => ({
        ...current,
        [Number(reviewBooking.id)]:
          review,
      }));

      setMessage(
        "Thank you. Your review was submitted successfully.",
      );

      setReviewBooking(null);
      setReviewRating(0);
      setHoverRating(0);
      setReviewComment("");
    } catch (err) {
      setError(
        err.response?.data?.message ||
          err.response?.data?.detail ||
          "Unable to submit your review.",
      );
    } finally {
      setSubmittingReview(false);
    }
  };


  const today = new Date()
    .toISOString()
    .split("T")[0];


  // ---------------------------------------------------------
  // UI
  // ---------------------------------------------------------

  return (
    <main className="page-section">
      <div className="container dashboard-container">

        {/* HEADER */}

        <div className="booking-page-header">
          <div>
            <span className="eyebrow">
              My reservations
            </span>

            <h1>Booking history</h1>

            <p>
              View and manage all your service
              bookings.
            </p>
          </div>

          <button
            type="button"
            className="button button-secondary"
            onClick={loadBookings}
            disabled={loading}
          >
            <RefreshCw
              size={18}
              className={
                loading ? "spin" : ""
              }
            />

            Refresh
          </button>
        </div>


        {/* MESSAGES */}

        {error && (
          <div className="alert alert-error">
            {error}
          </div>
        )}

        {message && (
          <div className="alert alert-success">
            {message}
          </div>
        )}


        {/* FILTER */}

        <section className="panel booking-filter-panel">
          <label htmlFor="booking-status">
            Filter by status
          </label>

          <select
            id="booking-status"
            className="text-input booking-status-filter"
            value={statusFilter}
            onChange={(event) =>
              setStatusFilter(
                event.target.value,
              )
            }
          >
            <option value="">
              All bookings
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

            <option value="cancelled">
              Cancelled
            </option>

            <option value="rejected">
              Rejected
            </option>
          </select>
        </section>


        {/* BOOKINGS */}

        {loading ? (
          <div className="state-card">
            <div className="spinner" />

            <p>Loading your bookings...</p>
          </div>
        ) : bookings.length === 0 ? (
          <div className="state-card">
            <History size={48} />

            <h2>No bookings found</h2>

            <p>
              Your service bookings will
              appear here.
            </p>
          </div>
        ) : (
          <div className="booking-list">

            {bookings.map((booking) => {
              const status = String(
                booking.status || "",
              ).toLowerCase();

              const existingReview =
                reviewsByBooking[
                  Number(booking.id)
                ];

              const existingPayment =
                paymentsByBooking[
                  Number(booking.id)
                ];

              const paymentStatus =
                String(
                  existingPayment?.status || "",
                ).toLowerCase();

              return (
                <article
                  className="panel booking-card"
                  key={booking.id}
                >

                  {/* CARD HEADER */}

                  <div className="booking-card-header">
                    <div>
                      <p className="booking-reference">
                        Reference:{" "}
                        {booking.reference_code ||
                          `#${booking.id}`}
                      </p>

                      <h2>
                        {booking.service_title ||
                          booking.service?.title ||
                          "Booked service"}
                      </h2>
                    </div>

                    <span
                      className={`status-badge status-${status}`}
                    >
                      {booking.status}
                    </span>
                  </div>


                  {/* BOOKING DETAILS */}

                  <div className="booking-details-grid">

                    <div className="booking-detail">
                      <CalendarDays
                        size={19}
                      />

                      <div>
                        <span>Date</span>

                        <strong>
                          {formatDate(
                            booking.scheduled_date,
                          )}
                        </strong>
                      </div>
                    </div>


                    <div className="booking-detail">
                      <Clock size={19} />

                      <div>
                        <span>Time</span>

                        <strong>
                          {formatTime(
                            booking.scheduled_start,
                          )}

                          {booking.scheduled_end
                            ? ` – ${formatTime(
                                booking.scheduled_end,
                              )}`
                            : ""}
                        </strong>
                      </div>
                    </div>


                    <div className="booking-detail">
                      <MapPin size={19} />

                      <div>
                        <span>
                          Location
                        </span>

                        <strong>
                          {booking.location ||
                            "Not provided"}
                        </strong>
                      </div>
                    </div>
                  </div>


                  {/* PAYMENT STATUS */}

                  <div className="booking-payment-summary">
                    <div className="booking-payment-summary-main">
                      <span className="booking-payment-icon">
                        <CreditCard size={18} />
                      </span>

                      <div>
                        <small>Payment</small>

                        <strong>
                          {existingPayment
                            ? formatPaymentMethod(
                                existingPayment.payment_method,
                              )
                            : "Not selected"}
                        </strong>
                      </div>
                    </div>

                    <span
                      className={`booking-payment-status ${
                        existingPayment
                          ? `payment-${paymentStatus}`
                          : "payment-unpaid"
                      }`}
                    >
                      {existingPayment
                        ? formatPaymentStatus(
                            existingPayment.status,
                          )
                        : "Unpaid"}
                    </span>

                    {existingPayment?.transaction_reference && (
                      <small className="booking-payment-reference">
                        {
                          existingPayment.transaction_reference
                        }
                      </small>
                    )}
                  </div>


                  {/* EXISTING REVIEW */}

                  {status === "completed" &&
                    existingReview && (
                      <div className="booking-review-summary">
                        <div>
                          <CheckCircle2
                            size={19}
                          />

                          <strong>
                            Your review
                          </strong>
                        </div>

                        <div className="booking-review-stars">
                          {[1, 2, 3, 4, 5].map(
                            (star) => (
                              <Star
                                key={star}
                                size={19}
                                className={
                                  star <=
                                  Number(
                                    existingReview.rating,
                                  )
                                    ? "filled"
                                    : ""
                                }
                                fill={
                                  star <=
                                  Number(
                                    existingReview.rating,
                                  )
                                    ? "currentColor"
                                    : "none"
                                }
                              />
                            ),
                          )}
                        </div>

                        {existingReview.comment && (
                          <p>
                            {
                              existingReview.comment
                            }
                          </p>
                        )}
                      </div>
                    )}


                  {/* FOOTER */}

                  <div className="booking-card-footer">
                    <div>
                      <span className="price-label">
                        Total price
                      </span>

                      <strong className="booking-price">
                        {formatPrice(
                          booking.total_price,
                        )}
                      </strong>
                    </div>


                    <div className="booking-footer-actions">

                      {/* PAYMENT */}

                      {!existingPayment &&
                        canCreatePayment(
                          booking,
                        ) && (
                          <button
                            type="button"
                            className="button booking-pay-button"
                            onClick={() =>
                              openPayment(
                                booking,
                              )
                            }
                          >
                            <WalletCards size={18} />
                            Pay now
                          </button>
                        )}


                      {existingPayment &&
                        paymentStatus === "pending" &&
                        existingPayment.payment_method !==
                          "cash" && (
                          <button
                            type="button"
                            className="button booking-pay-button"
                            onClick={() => {
                              setPaymentBooking(
                                booking,
                              );

                              setPaymentMethod(
                                existingPayment.payment_method,
                              );

                              setPaymentCheckout({
                                payment_id:
                                  existingPayment.id,
                                booking_id:
                                  existingPayment.booking_id,
                                transaction_reference:
                                  existingPayment.transaction_reference,
                                payment_method:
                                  existingPayment.payment_method,
                                amount:
                                  existingPayment.amount,
                                status:
                                  existingPayment.status,
                              });

                              setPaymentError("");
                            }}
                          >
                            <CreditCard size={18} />
                            Complete payment
                          </button>
                        )}


                      {/* MESSAGE PROVIDER */}

                      <Link
                        className="button button-outline booking-message-button"
                        to={`/messages?booking=${booking.id}`}
                        state={{
                          bookingId: booking.id,
                          referenceCode: booking.reference_code,
                          serviceTitle:
                            booking.service_title ||
                            booking.service?.title ||
                            "Booked service",
                          providerId: booking.provider_id,
                        }}
                      >
                        <MessageCircle size={18} />
                        Message provider
                      </Link>


                      {/* RESCHEDULE */}

                      {canReschedule(
                        booking.status,
                      ) && (
                        <button
                          type="button"
                          className="button button-outline booking-reschedule-button"
                          onClick={() =>
                            openReschedule(
                              booking,
                            )
                          }
                        >
                          <CalendarClock size={18} />
                          Reschedule
                        </button>
                      )}


                      {/* CANCEL */}

                      {canCancel(
                        booking.status,
                      ) && (
                        <button
                          type="button"
                          className="danger-button"
                          onClick={() =>
                            cancelBooking(
                              booking.id,
                            )
                          }
                          disabled={
                            cancellingId ===
                            booking.id
                          }
                        >
                          <XCircle size={18} />

                          {cancellingId ===
                          booking.id
                            ? "Cancelling..."
                            : "Cancel booking"}
                        </button>
                      )}


                      {/* REVIEW */}

                      {status === "completed" &&
                        !existingReview && (
                          <button
                            type="button"
                            className="button booking-review-button"
                            onClick={() =>
                              openReview(
                                booking,
                              )
                            }
                          >
                            <Star size={18} />

                            Leave a review
                          </button>
                        )}


                      {/* ALREADY REVIEWED */}

                      {status === "completed" &&
                        existingReview && (
                          <span className="booking-reviewed-badge">
                            <CheckCircle2
                              size={17}
                            />
                            Reviewed
                          </span>
                        )}
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </div>


      {/* =====================================================
          PAYMENT MODAL
      ====================================================== */}

      {paymentBooking && (
        <div
          className="modal-overlay"
          onMouseDown={(event) => {
            if (
              event.target ===
              event.currentTarget
            ) {
              closePayment();
            }
          }}
        >
          <div
            className="modal-card booking-payment-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="payment-title"
          >
            <button
              type="button"
              className="modal-close"
              onClick={closePayment}
              disabled={
                paymentSubmitting ||
                paymentCompleting
              }
              aria-label="Close payment"
            >
              <X size={22} />
            </button>


            <div className="modal-heading">
              <span className="eyebrow">
                Secure checkout
              </span>

              <h2 id="payment-title">
                {paymentCheckout
                  ? "Complete payment"
                  : "Choose payment method"}
              </h2>

              <p>
                Payment for{" "}
                <strong>
                  {paymentBooking.service_title ||
                    "your booking"}
                </strong>
                .
              </p>
            </div>


            {paymentError && (
              <div className="alert alert-error">
                {paymentError}
              </div>
            )}


            <div className="booking-payment-amount">
              <span>Total amount</span>

              <strong>
                {formatPrice(
                  paymentBooking.total_price,
                )}
              </strong>
            </div>


            {!paymentCheckout ? (
              <form
                className="booking-payment-form"
                onSubmit={createPayment}
              >
                <div className="payment-method-grid">

                  <label
                    className={`payment-method-card ${
                      paymentMethod === "cash"
                        ? "selected"
                        : ""
                    }`}
                  >
                    <input
                      type="radio"
                      name="payment_method"
                      value="cash"
                      checked={
                        paymentMethod === "cash"
                      }
                      onChange={(event) =>
                        setPaymentMethod(
                          event.target.value,
                        )
                      }
                    />

                    <span className="payment-method-icon">
                      <WalletCards size={23} />
                    </span>

                    <strong>
                      Cash on service
                    </strong>

                    <small>
                      Pay the provider after the
                      service is completed.
                    </small>
                  </label>


                  <label
                    className={`payment-method-card ${
                      paymentMethod === "jazzcash"
                        ? "selected"
                        : ""
                    }`}
                  >
                    <input
                      type="radio"
                      name="payment_method"
                      value="jazzcash"
                      checked={
                        paymentMethod ===
                        "jazzcash"
                      }
                      onChange={(event) =>
                        setPaymentMethod(
                          event.target.value,
                        )
                      }
                    />

                    <span className="payment-method-icon">
                      <Smartphone size={23} />
                    </span>

                    <strong>JazzCash</strong>

                    <small>
                      Digital wallet checkout.
                    </small>
                  </label>


                  <label
                    className={`payment-method-card ${
                      paymentMethod === "easypaisa"
                        ? "selected"
                        : ""
                    }`}
                  >
                    <input
                      type="radio"
                      name="payment_method"
                      value="easypaisa"
                      checked={
                        paymentMethod ===
                        "easypaisa"
                      }
                      onChange={(event) =>
                        setPaymentMethod(
                          event.target.value,
                        )
                      }
                    />

                    <span className="payment-method-icon">
                      <Smartphone size={23} />
                    </span>

                    <strong>Easypaisa</strong>

                    <small>
                      Digital wallet checkout.
                    </small>
                  </label>

                </div>


                <div className="modal-actions">
                  <button
                    type="button"
                    className="button button-outline"
                    onClick={closePayment}
                    disabled={paymentSubmitting}
                  >
                    Cancel
                  </button>

                  <button
                    type="submit"
                    className="button"
                    disabled={paymentSubmitting}
                  >
                    <CreditCard size={18} />

                    {paymentSubmitting
                      ? "Creating checkout..."
                      : paymentMethod === "cash"
                        ? "Confirm cash payment"
                        : `Continue with ${formatPaymentMethod(
                            paymentMethod,
                          )}`}
                  </button>
                </div>
              </form>
            ) : (
              <div className="digital-payment-checkout">

                <div className="digital-payment-provider">
                  <Smartphone size={30} />

                  <div>
                    <span>
                      Payment method
                    </span>

                    <strong>
                      {formatPaymentMethod(
                        paymentCheckout.payment_method,
                      )}
                    </strong>
                  </div>
                </div>


                <div className="digital-payment-details">
                  <div>
                    <span>
                      Transaction reference
                    </span>

                    <strong>
                      {
                        paymentCheckout.transaction_reference
                      }
                    </strong>
                  </div>

                  <div>
                    <span>Status</span>

                    <strong>
                      {formatPaymentStatus(
                        paymentCheckout.status,
                      )}
                    </strong>
                  </div>
                </div>


                <div className="payment-simulation-note">
                  <strong>
                    Development checkout
                  </strong>

                  <p>
                    JazzCash/Easypaisa is currently
                    simulated. Use the button below to
                    confirm a successful test payment.
                  </p>
                </div>


                <div className="modal-actions">
                  <button
                    type="button"
                    className="button button-outline"
                    onClick={closePayment}
                    disabled={paymentCompleting}
                  >
                    Pay later
                  </button>

                  <button
                    type="button"
                    className="button"
                    onClick={
                      completeDigitalPayment
                    }
                    disabled={paymentCompleting}
                  >
                    <CheckCircle2 size={18} />

                    {paymentCompleting
                      ? "Processing..."
                      : "Complete test payment"}
                  </button>
                </div>

              </div>
            )}
          </div>
        </div>
      )}


      {/* =====================================================
          RESCHEDULE MODAL
      ====================================================== */}

      {rescheduleBooking && (
        <div
          className="modal-overlay"
          onMouseDown={(event) => {
            if (
              event.target ===
              event.currentTarget
            ) {
              closeReschedule();
            }
          }}
        >
          <div
            className="modal-card booking-reschedule-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="reschedule-title"
          >
            <button
              type="button"
              className="modal-close"
              onClick={closeReschedule}
              disabled={rescheduling}
              aria-label="Close reschedule form"
            >
              <X size={22} />
            </button>


            <div className="modal-heading">
              <span className="eyebrow">
                Change booking time
              </span>

              <h2 id="reschedule-title">
                Reschedule booking
              </h2>

              <p>
                Choose another available date and time for{" "}
                <strong>
                  {rescheduleBooking.service_title ||
                    "this service"}
                </strong>
                .
              </p>
            </div>


            {rescheduleError && (
              <div className="alert alert-error">
                {rescheduleError}
              </div>
            )}


            <div className="reschedule-current-booking">
              <span>Current booking</span>

              <strong>
                {formatDate(
                  rescheduleBooking.scheduled_date,
                )}{" "}
                at{" "}
                {formatTime(
                  rescheduleBooking.scheduled_start,
                )}
              </strong>
            </div>


            <form
              className="auth-form booking-reschedule-form"
              onSubmit={submitReschedule}
            >
              <label className="form-field">
                <span>New booking date</span>

                <div className="input-with-icon">
                  <CalendarDays size={18} />

                  <input
                    type="date"
                    name="scheduled_date"
                    value={
                      rescheduleForm.scheduled_date
                    }
                    onChange={
                      updateRescheduleField
                    }
                    min={today}
                    required
                  />
                </div>
              </label>


              <label className="form-field">
                <span>Available start time</span>

                <div className="input-with-icon">
                  <Clock size={18} />

                  <select
                    name="scheduled_start"
                    value={
                      rescheduleForm.scheduled_start
                    }
                    onChange={
                      updateRescheduleField
                    }
                    disabled={
                      rescheduleAvailabilityLoading ||
                      rescheduleSlotsLoading ||
                      !rescheduleForm.scheduled_date ||
                      !selectedRescheduleAvailability ||
                      rescheduleAvailableTimeSlots.length ===
                        0
                    }
                    required
                  >
                    <option value="">
                      {rescheduleAvailabilityLoading ||
                      rescheduleSlotsLoading
                        ? "Loading available times..."
                        : !rescheduleForm.scheduled_date
                          ? "Choose a date first"
                          : !selectedRescheduleAvailability
                            ? "Provider unavailable this day"
                            : rescheduleAvailableTimeSlots.length ===
                                0
                              ? "No free times available"
                              : "Select an available time"}
                    </option>

                    {rescheduleAvailableTimeSlots.map(
                      (time) => (
                        <option
                          key={time}
                          value={time}
                        >
                          {formatSlotTime(time)}
                        </option>
                      ),
                    )}
                  </select>
                </div>


                {rescheduleForm.scheduled_date &&
                  !rescheduleAvailabilityLoading &&
                  !selectedRescheduleAvailability && (
                    <small className="availability-help availability-help-error">
                      The provider is unavailable on this
                      day. Please choose another date.
                    </small>
                  )}


                {selectedRescheduleAvailability &&
                  rescheduleAvailableTimeSlots.length >
                    0 &&
                  !rescheduleSlotsLoading && (
                    <small className="availability-help">
                      Showing available times between{" "}
                      {formatSlotTime(
                        selectedRescheduleAvailability.start_time,
                      )}{" "}
                      and{" "}
                      {formatSlotTime(
                        selectedRescheduleAvailability.end_time,
                      )}
                      .
                    </small>
                  )}
              </label>


              <div className="modal-actions">
                <button
                  type="button"
                  className="button button-outline"
                  onClick={closeReschedule}
                  disabled={rescheduling}
                >
                  Keep current time
                </button>

                <button
                  type="submit"
                  className="button"
                  disabled={
                    rescheduling ||
                    !rescheduleForm.scheduled_date ||
                    !rescheduleForm.scheduled_start
                  }
                >
                  <CalendarClock size={18} />

                  {rescheduling
                    ? "Rescheduling..."
                    : "Confirm reschedule"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}


      {/* =====================================================
          REVIEW MODAL
      ====================================================== */}

      {reviewBooking && (
        <div
          className="modal-overlay"
          onMouseDown={(event) => {
            if (
              event.target ===
              event.currentTarget
            ) {
              closeReview();
            }
          }}
        >
          <div
            className="modal-card booking-review-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="review-title"
          >
            <button
              type="button"
              className="modal-close"
              onClick={closeReview}
              disabled={submittingReview}
              aria-label="Close review form"
            >
              <X size={22} />
            </button>


            <div className="modal-heading">
              <span className="eyebrow">
                Rate your experience
              </span>

              <h2 id="review-title">
                Leave a review
              </h2>

              <p>
                How was your experience with{" "}
                <strong>
                  {reviewBooking.service_title}
                </strong>
                ?
              </p>
            </div>


            <form
              className="booking-review-form"
              onSubmit={submitReview}
            >

              {/* STAR RATING */}

              <div className="review-rating-section">
                <span>
                  Your rating
                </span>

                <div className="review-star-picker">
                  {[1, 2, 3, 4, 5].map(
                    (star) => {
                      const activeRating =
                        hoverRating ||
                        reviewRating;

                      return (
                        <button
                          key={star}
                          type="button"
                          className={
                            star <=
                            activeRating
                              ? "active"
                              : ""
                          }
                          onMouseEnter={() =>
                            setHoverRating(
                              star,
                            )
                          }
                          onMouseLeave={() =>
                            setHoverRating(
                              0,
                            )
                          }
                          onClick={() =>
                            setReviewRating(
                              star,
                            )
                          }
                          aria-label={`Rate ${star} star${
                            star > 1
                              ? "s"
                              : ""
                          }`}
                        >
                          <Star
                            size={34}
                            fill={
                              star <=
                              activeRating
                                ? "currentColor"
                                : "none"
                            }
                          />
                        </button>
                      );
                    },
                  )}
                </div>

                <strong className="review-rating-label">
                  {reviewRating === 0
                    ? "Select 1–5 stars"
                    : `${reviewRating} out of 5`}
                </strong>
              </div>


              {/* COMMENT */}

              <label className="form-field">
                <span>
                  Your review
                </span>

                <textarea
                  value={reviewComment}
                  onChange={(event) =>
                    setReviewComment(
                      event.target.value,
                    )
                  }
                  rows={5}
                  maxLength={1000}
                  placeholder="Tell us about the quality of the service, communication and overall experience..."
                />

                <small className="review-character-count">
                  {reviewComment.length}
                  /1000
                </small>
              </label>


              {/* ACTIONS */}

              <div className="modal-actions">
                <button
                  type="button"
                  className="button button-outline"
                  onClick={closeReview}
                  disabled={submittingReview}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="button"
                  disabled={
                    submittingReview ||
                    reviewRating === 0
                  }
                >
                  <Star size={18} />

                  {submittingReview
                    ? "Submitting..."
                    : "Submit review"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* =====================================================
          CANCEL MODAL
      ====================================================== */}

      {cancelModal.show && (
        <div
          className="modal-overlay"
          onMouseDown={(event) => {
            if (
              event.target ===
              event.currentTarget
            ) {
              setCancelModal((prev) => ({
                ...prev,
                show: false,
              }));
            }
          }}
        >
          <div
            className="modal-card booking-cancel-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="cancel-title"
          >
            <button
              type="button"
              className="modal-close"
              onClick={() =>
                setCancelModal((prev) => ({
                  ...prev,
                  show: false,
                }))
              }
              aria-label="Close cancel dialog"
            >
              <X size={22} />
            </button>

            <div className="modal-heading">
              <span className="eyebrow">
                Cancel booking
              </span>
              <h2 id="cancel-title">
                Cancel this booking?
              </h2>
              <p>
                This action cannot be undone.
                You may need to contact the
                provider for a refund.
              </p>
            </div>

            <div className="booking-cancel-reason">
              <label className="form-field">
                <span>Cancellation reason (optional)</span>
                <textarea
                  className="text-input"
                  rows={4}
                  value={cancelModal.reason}
                  onChange={(event) =>
                    setCancelModal((prev) => ({
                      ...prev,
                      reason:
                        event.target.value,
                    }))
                  }
                  placeholder="Tell us why you're cancelling..."
                  maxLength={1000}
                />
                <small className="review-character-count">
                  {cancelModal.reason.length}/1000
                </small>
              </label>
            </div>

            <div className="modal-actions">
              <button
                type="button"
                className="button button-outline"
                onClick={() =>
                  setCancelModal({
                    show: false,
                    bookingId: null,
                    reason: "",
                  })
                }
              >
                Keep booking
              </button>
              <button
                type="button"
                className="button button-danger"
                onClick={handleConfirmCancel}
              >
                Cancel booking
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}


export default BookingHistory;