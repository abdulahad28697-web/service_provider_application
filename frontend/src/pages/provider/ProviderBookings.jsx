import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  CalendarDays,
  CalendarRange,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock3,
  CreditCard,
  List,
  MapPin,
  Mail,
  MessageCircle,
  Phone,
  RefreshCw,
  UserRound,
  WalletCards,
  X,
  XCircle,
} from "lucide-react";

import api from "../../api/api";

function getData(response) {
  return response?.data?.data ?? response?.data ?? {};
}

function getItems(response) {
  const data = getData(response);

  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.items)) return data.items;

  return [];
}


function formatPaymentMethod(value) {
  const method = String(value || "").toLowerCase();

  if (method === "cash") {
    return "Cash on service";
  }

  if (method === "jazzcash") {
    return "JazzCash";
  }

  if (method === "easypaisa") {
    return "Easypaisa";
  }

  return method || "Not selected";
}


function formatPaymentStatus(value) {
  const status = String(value || "").toLowerCase();

  if (!status) {
    return "Unpaid";
  }

  return (
    status.charAt(0).toUpperCase() +
    status.slice(1)
  );
}

export default function ProviderBookings() {
  const navigate = useNavigate();

  const [bookings, setBookings] = useState([]);

  const [paymentsByBooking, setPaymentsByBooking] =
    useState({});

  const [paymentActionId, setPaymentActionId] =
    useState(null);

  const [filter, setFilter] = useState("all");
  const [viewMode, setViewMode] = useState("list");
  const [calendarMonth, setCalendarMonth] = useState(
    () => new Date(),
  );
  const [selectedCalendarDate, setSelectedCalendarDate] =
    useState(null);

  const [loading, setLoading] = useState(true);
  const [actionId, setActionId] = useState(null);

  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const [confirmModal, setConfirmModal] = useState({
    show: false,
    type: null,
    bookingId: null,
    paymentId: null,
    title: "",
    message: "",
    needsReason: false,
    reason: "",
  });

  const loadBookings = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const [
        bookingsResponse,
        paymentsResponse,
      ] = await Promise.all([
        api.get("/bookings", {
          params: {
            as_provider: true,
            page_size: 100,
          },
        }),

        api.get("/payments/provider").catch(() => ({
          data: {
            data: [],
          },
        })),
      ]);

      setBookings(
        getItems(bookingsResponse),
      );

      const payments =
        getItems(paymentsResponse);

      const paymentMap = {};

      payments.forEach((payment) => {
        paymentMap[
          Number(payment.booking_id)
        ] = payment;
      });

      setPaymentsByBooking(
        paymentMap,
      );
    } catch (requestError) {
      setBookings([]);

      setError(
        requestError.response?.data?.message ||
          requestError.response?.data?.detail ||
          "Unable to load provider booking requests.",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadBookings();
  }, [loadBookings]);

  const filteredBookings = useMemo(() => {
    if (filter === "all") {
      return bookings;
    }

    return bookings.filter(
      (booking) =>
        String(booking.status || "").toLowerCase() ===
        filter,
    );
  }, [bookings, filter]);

  const bookingCounts = useMemo(() => {
    return bookings.reduce(
      (counts, booking) => {
        const status = String(
          booking.status || "",
        ).toLowerCase();

        counts.all += 1;

        if (counts[status] !== undefined) {
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

  const updateBooking = (updatedBooking) => {
    setBookings((current) =>
      current.map((booking) =>
        booking.id === updatedBooking.id
          ? {
              ...booking,
              ...updatedBooking,
            }
          : booking,
      ),
    );
  };

  const acceptBooking = async (bookingId) => {
    setActionId(bookingId);
    setError("");
    setMessage("");

    try {
      const response = await api.post(
        `/bookings/${bookingId}/accept`,
      );

      updateBooking(getData(response));

      setMessage("Booking accepted successfully.");
    } catch (requestError) {
      setError(
        requestError.response?.data?.message ||
          requestError.response?.data?.detail ||
          "Unable to accept this booking.",
      );
    } finally {
      setActionId(null);
    }
  };

  const rejectBooking = (bookingId) => {
    setConfirmModal({
      show: true,
      type: "reject",
      bookingId,
      paymentId: null,
      title: "Reject Booking",
      message: "Are you sure you want to reject this booking?",
      needsReason: true,
      reason: "",
    });
  };

  const completeBooking = (bookingId) => {
    setConfirmModal({
      show: true,
      type: "complete",
      bookingId,
      paymentId: null,
      title: "Complete Booking",
      message: "Mark this booking as completed?",
      needsReason: false,
      reason: "",
    });
  };

  const confirmCashPayment = (payment) => {
    if (!payment?.id) {
      return;
    }

    setConfirmModal({
      show: true,
      type: "cash-payment",
      bookingId: null,
      paymentId: payment.id,
      title: "Confirm Cash Payment",
      message: "Confirm that you received the cash payment from the customer?",
      needsReason: false,
      reason: "",
    });
  };

  const handleConfirmAction = async () => {
    const { type, bookingId, paymentId, reason } = confirmModal;
    setConfirmModal({
      show: false,
      type: null,
      bookingId: null,
      paymentId: null,
      title: "",
      message: "",
      needsReason: false,
      reason: "",
    });

    if (type === "reject") {
      setActionId(bookingId);
      setError("");
      setMessage("");

      try {
        const response = await api.post(
          `/bookings/${bookingId}/reject`,
          {
            reason: reason.trim() || null,
          },
        );

        updateBooking(getData(response));
        setMessage("Booking rejected.");
      } catch (requestError) {
        setError(
          requestError.response?.data?.message ||
            requestError.response?.data?.detail ||
            "Unable to reject this booking.",
        );
      } finally {
        setActionId(null);
      }
    } else if (type === "complete") {
      setActionId(bookingId);
      setError("");
      setMessage("");

      try {
        const response = await api.post(
          `/bookings/${bookingId}/complete`,
        );

        updateBooking(getData(response));
        setMessage("Booking marked as completed successfully.");
      } catch (requestError) {
        setError(
          requestError.response?.data?.message ||
            requestError.response?.data?.detail ||
            "Unable to complete this booking.",
        );
      } finally {
        setActionId(null);
      }
    } else if (type === "cash-payment") {
      try {
        setPaymentActionId(paymentId);
        setError("");
        setMessage("");

        const response = await api.post(
          `/payments/${paymentId}/cash-paid`,
        );

        const updatedPayment = getData(response);
        setPaymentsByBooking((current) => ({
          ...current,
          [Number(updatedPayment.booking_id)]: updatedPayment,
        }));
        setMessage("Cash payment confirmed successfully.");
      } catch (requestError) {
        setError(
          requestError.response?.data?.message ||
            requestError.response?.data?.detail ||
            "Unable to confirm the cash payment.",
        );
      } finally {
        setPaymentActionId(null);
      }
    }
  };


  const openMessages = (booking) => {
    navigate(
      `/messages?booking=${booking.id}`,
      {
        state: {
          bookingId: booking.id,
          referenceCode: booking.reference_code,
          serviceTitle:
            booking.service_title ||
            "Service booking",
          customerId: booking.customer_id,
          otherUserName:
            booking.customer_name ||
            "Customer",
        },
      },
    );
  };


  const formatStatus = (status) => {
    const value = String(status || "").toLowerCase();

    if (!value) return "Unknown";

    return (
      value.charAt(0).toUpperCase() +
      value.slice(1)
    );
  };

  const formatDate = (date) => {
    if (!date) return "Not available";

    return new Date(`${date}T00:00:00`).toLocaleDateString(
      "en-GB",
      {
        day: "2-digit",
        month: "short",
        year: "numeric",
      },
    );
  };

  const formatTime = (value) => {
    if (!value) return "--";

    const [hours, minutes] = value.split(":");

    const date = new Date();
    date.setHours(Number(hours), Number(minutes), 0, 0);

    return date.toLocaleTimeString([], {
      hour: "numeric",
      minute: "2-digit",
    });
  };

  const monthLabel = calendarMonth.toLocaleDateString(
    "en-GB",
    {
      month: "long",
      year: "numeric",
    },
  );

  const calendarCells = useMemo(() => {
    const year = calendarMonth.getFullYear();
    const month = calendarMonth.getMonth();

    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);

    // Monday = 0 ... Sunday = 6
    const mondayOffset = (firstDay.getDay() + 6) % 7;
    const totalCells = Math.ceil(
      (mondayOffset + lastDay.getDate()) / 7,
    ) * 7;

    return Array.from({ length: totalCells }, (_, index) => {
      const dayNumber = index - mondayOffset + 1;

      if (
        dayNumber < 1 ||
        dayNumber > lastDay.getDate()
      ) {
        return null;
      }

      const date = new Date(year, month, dayNumber);
      const isoDate = [
        date.getFullYear(),
        String(date.getMonth() + 1).padStart(2, "0"),
        String(date.getDate()).padStart(2, "0"),
      ].join("-");

      const dayBookings = filteredBookings
        .filter(
          (booking) =>
            booking.scheduled_date === isoDate,
        )
        .sort((a, b) =>
          String(a.scheduled_start || "").localeCompare(
            String(b.scheduled_start || ""),
          ),
        );

      return {
        dayNumber,
        isoDate,
        bookings: dayBookings,
      };
    });
  }, [calendarMonth, filteredBookings]);

  const selectedDateBookings = useMemo(() => {
    if (!selectedCalendarDate) {
      return [];
    }

    return filteredBookings
      .filter(
        (booking) =>
          booking.scheduled_date ===
          selectedCalendarDate,
      )
      .sort((a, b) =>
        String(a.scheduled_start || "").localeCompare(
          String(b.scheduled_start || ""),
        ),
      );
  }, [filteredBookings, selectedCalendarDate]);

  const goToPreviousMonth = () => {
    setCalendarMonth((current) => {
      return new Date(
        current.getFullYear(),
        current.getMonth() - 1,
        1,
      );
    });

    setSelectedCalendarDate(null);
  };

  const goToNextMonth = () => {
    setCalendarMonth((current) => {
      return new Date(
        current.getFullYear(),
        current.getMonth() + 1,
        1,
      );
    });

    setSelectedCalendarDate(null);
  };

  const goToCurrentMonth = () => {
    setCalendarMonth(new Date());
    setSelectedCalendarDate(null);
  };

  return (
    <main className="provider-bookings-page">
      <div className="provider-bookings-container">

        <div className="provider-bookings-header">
          <div>
            <span className="eyebrow">
              Provider workspace
            </span>

            <h1>Booking requests</h1>

            <p>
              Review customer requests and manage
              accepted jobs.
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
              className={loading ? "spin" : ""}
            />

            Refresh
          </button>
        </div>

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

        <div className="provider-booking-filters">
          {[
            ["all", "All"],
            ["pending", "Pending"],
            ["accepted", "Accepted"],
            ["completed", "Completed"],
            ["rejected", "Rejected"],
            ["cancelled", "Cancelled"],
          ].map(([value, label]) => (
            <button
              key={value}
              type="button"
              className={
                filter === value ? "active" : ""
              }
              onClick={() => setFilter(value)}
            >
              <span>{label}</span>

              <strong>
                {bookingCounts[value]}
              </strong>
            </button>
          ))}
        </div>

        <div className="provider-booking-view-switch">
          <button
            type="button"
            className={
              viewMode === "list" ? "active" : ""
            }
            onClick={() => setViewMode("list")}
          >
            <List size={18} />
            List view
          </button>

          <button
            type="button"
            className={
              viewMode === "calendar" ? "active" : ""
            }
            onClick={() => setViewMode("calendar")}
          >
            <CalendarRange size={18} />
            Calendar view
          </button>
        </div>

        {loading ? (
          <div className="provider-bookings-empty">
            <RefreshCw
              className="spin"
              size={34}
            />

            <h2>Loading booking requests...</h2>
          </div>
        ) : filteredBookings.length === 0 ? (
          <div className="provider-bookings-empty">
            <Clock3 size={42} />

            <h2>No booking requests found</h2>

            <p>
              Customer bookings for your services will
              appear here.
            </p>
          </div>
        ) : viewMode === "calendar" ? (
          <section className="provider-booking-calendar-panel">
            <div className="provider-booking-calendar-toolbar">
              <div>
                <span className="eyebrow">
                  Booking calendar
                </span>
                <h2>{monthLabel}</h2>
              </div>

              <div className="provider-booking-calendar-actions">
                <button
                  type="button"
                  className="button button-outline"
                  onClick={goToPreviousMonth}
                  aria-label="Previous month"
                >
                  <ChevronLeft size={18} />
                </button>

                <button
                  type="button"
                  className="button button-outline"
                  onClick={goToCurrentMonth}
                >
                  Today
                </button>

                <button
                  type="button"
                  className="button button-outline"
                  onClick={goToNextMonth}
                  aria-label="Next month"
                >
                  <ChevronRight size={18} />
                </button>
              </div>
            </div>

            <div className="provider-booking-calendar-weekdays">
              {[
                "Mon",
                "Tue",
                "Wed",
                "Thu",
                "Fri",
                "Sat",
                "Sun",
              ].map((day) => (
                <span key={day}>{day}</span>
              ))}
            </div>

            <div className="provider-booking-calendar-grid">
              {calendarCells.map((cell, index) => {
                if (!cell) {
                  return (
                    <div
                      className="provider-booking-calendar-cell empty"
                      key={`empty-${index}`}
                    />
                  );
                }

                const isSelected =
                  selectedCalendarDate === cell.isoDate;

                return (
                  <button
                    type="button"
                    className={`provider-booking-calendar-cell ${
                      isSelected ? "selected" : ""
                    }`}
                    key={cell.isoDate}
                    onClick={() =>
                      setSelectedCalendarDate(cell.isoDate)
                    }
                  >
                    <span className="provider-booking-calendar-date">
                      {cell.dayNumber}
                    </span>

                    <div className="provider-booking-calendar-events">
                      {cell.bookings
                        .slice(0, 3)
                        .map((booking) => {
                          const status = String(
                            booking.status || "",
                          ).toLowerCase();

                          return (
                            <span
                              className={`provider-calendar-event status-${status}`}
                              key={booking.id}
                            >
                              <strong>
                                {formatTime(
                                  booking.scheduled_start,
                                )}
                              </strong>
                              <span>
                                {booking.service_title ||
                                  "Service booking"}
                              </span>
                            </span>
                          );
                        })}

                      {cell.bookings.length > 3 && (
                        <small>
                          +{cell.bookings.length - 3} more
                        </small>
                      )}
                    </div>
                  </button>
                );
              })}
            </div>

            {selectedCalendarDate && (
              <div className="provider-calendar-day-details">
                <div className="provider-calendar-day-details-header">
                  <div>
                    <span>Selected date</span>
                    <h3>
                      {formatDate(selectedCalendarDate)}
                    </h3>
                  </div>

                  <strong>
                    {selectedDateBookings.length}{" "}
                    {selectedDateBookings.length === 1
                      ? "booking"
                      : "bookings"}
                  </strong>
                </div>

                {selectedDateBookings.length === 0 ? (
                  <div className="provider-calendar-no-bookings">
                    No bookings for this date.
                  </div>
                ) : (
                  <div className="provider-calendar-day-list">
                    {selectedDateBookings.map((booking) => {
                      const status = String(
                        booking.status || "",
                      ).toLowerCase();

                      const payment =
                        paymentsByBooking[
                          Number(booking.id)
                        ];

                      const paymentStatus =
                        String(
                          payment?.status || "",
                        ).toLowerCase();

                      return (
                        <article
                          className="provider-calendar-day-booking"
                          key={booking.id}
                        >
                          <div>
                            <strong>
                              {formatTime(
                                booking.scheduled_start,
                              )}{" "}
                              –{" "}
                              {formatTime(
                                booking.scheduled_end,
                              )}
                            </strong>

                            <span>
                              {booking.service_title ||
                                "Service booking"}
                            </span>
                          </div>

                          <div>
                            <span>
                              {booking.customer_name ||
                                "Customer"}
                            </span>

                            <small>
                              {booking.customer_phone ||
                                booking.customer_email ||
                                "Contact unavailable"}
                            </small>
                          </div>

                          <span
                            className={`provider-booking-status status-${status}`}
                          >
                            {formatStatus(status)}
                          </span>

                          <span
                            className={`provider-payment-mini-status ${
                              payment
                                ? `payment-${paymentStatus}`
                                : "payment-unpaid"
                            }`}
                          >
                            <CreditCard size={14} />

                            {payment
                              ? formatPaymentStatus(
                                  payment.status,
                                )
                              : "Unpaid"}
                          </span>

                          <button
                            type="button"
                            className="button button-outline provider-calendar-message-button"
                            onClick={() =>
                              openMessages(booking)
                            }
                          >
                            <MessageCircle size={16} />
                            Message
                          </button>
                        </article>
                      );
                    })}
                  </div>
                )}
              </div>
            )}
          </section>
        ) : (
          <div className="provider-bookings-grid">
            {filteredBookings.map((booking) => {
              const status = String(
                booking.status || "",
              ).toLowerCase();

              const payment =
                paymentsByBooking[
                  Number(booking.id)
                ];

              const paymentStatus =
                String(
                  payment?.status || "",
                ).toLowerCase();

              const canConfirmCash =
                status === "completed" &&
                payment?.payment_method === "cash" &&
                paymentStatus !== "paid";

              return (
                <article
                  className="provider-booking-card"
                  key={booking.id}
                >
                  <div className="provider-booking-card-header">
                    <div>
                      <span className="booking-reference">
                        {booking.reference_code}
                      </span>

                      <h2>
                        {booking.service_title ||
                          "Service booking"}
                      </h2>
                    </div>

                    <span
                      className={`provider-booking-status status-${status}`}
                    >
                      {formatStatus(status)}
                    </span>
                  </div>

                  <div className="provider-booking-customer">
                    <div className="provider-booking-customer-item">
                      <span className="provider-booking-customer-icon">
                        <UserRound size={18} />
                      </span>

                      <div>
                        <small>Customer name</small>
                        <strong>
                          {booking.customer_name ||
                            "Name not provided"}
                        </strong>
                      </div>
                    </div>

                    <div className="provider-booking-customer-item">
                      <span className="provider-booking-customer-icon">
                        <Phone size={18} />
                      </span>

                      <div>
                        <small>Phone number</small>
                        <strong>
                          {booking.customer_phone ||
                            "Phone not provided"}
                        </strong>
                      </div>
                    </div>

                    <div className="provider-booking-customer-item">
                      <span className="provider-booking-customer-icon">
                        <Mail size={18} />
                      </span>

                      <div>
                        <small>Email</small>
                        <strong>
                          {booking.customer_email ||
                            "Email not provided"}
                        </strong>
                      </div>
                    </div>
                  </div>

                  <div className="provider-booking-info-grid">
                    <div>
                      <CalendarDays size={18} />

                      <span>
                        <small>Date</small>
                        <strong>
                          {formatDate(
                            booking.scheduled_date,
                          )}
                        </strong>
                      </span>
                    </div>

                    <div>
                      <Clock3 size={18} />

                      <span>
                        <small>Time</small>

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
                      <MapPin size={18} />

                      <span>
                        <small>Location</small>

                        <strong>
                          {booking.location ||
                            "Not provided"}
                        </strong>
                      </span>
                    </div>
                  </div>

                  {booking.customer_notes && (
                    <div className="provider-booking-notes">
                      <span>Customer notes</span>

                      <p>
                        {booking.customer_notes}
                      </p>
                    </div>
                  )}

                  {/* PAYMENT */}

                  <div className="provider-payment-summary">
                    <div className="provider-payment-summary-main">
                      <span className="provider-payment-icon">
                        <CreditCard size={19} />
                      </span>

                      <div>
                        <small>Payment method</small>

                        <strong>
                          {payment
                            ? formatPaymentMethod(
                                payment.payment_method,
                              )
                            : "Not selected"}
                        </strong>
                      </div>
                    </div>

                    <div className="provider-payment-summary-status">
                      <small>Payment status</small>

                      <span
                        className={`provider-payment-status ${
                          payment
                            ? `payment-${paymentStatus}`
                            : "payment-unpaid"
                        }`}
                      >
                        {payment
                          ? formatPaymentStatus(
                              payment.status,
                            )
                          : "Unpaid"}
                      </span>
                    </div>

                    {payment?.transaction_reference && (
                      <div className="provider-payment-reference">
                        <small>
                          Transaction reference
                        </small>

                        <strong>
                          {
                            payment.transaction_reference
                          }
                        </strong>
                      </div>
                    )}
                  </div>


                  <div className="provider-booking-footer">
                    <div>
                      <span>Total price</span>

                      <strong>
                        PKR{" "}
                        {Number(
                          booking.total_price || 0,
                        ).toLocaleString()}
                      </strong>
                    </div>

                    <div className="provider-booking-actions">

                      {canConfirmCash && (
                        <button
                          type="button"
                          className="button provider-cash-confirm-button"
                          disabled={
                            paymentActionId ===
                            payment.id
                          }
                          onClick={() =>
                            confirmCashPayment(
                              payment,
                            )
                          }
                        >
                          <WalletCards size={18} />

                          {paymentActionId ===
                          payment.id
                            ? "Confirming..."
                            : "Confirm cash received"}
                        </button>
                      )}

                      <button
                        type="button"
                        className="button button-outline provider-message-button"
                        onClick={() =>
                          openMessages(booking)
                        }
                      >
                        <MessageCircle size={18} />
                        Message customer
                      </button>

                      {status === "pending" && (
                        <>
                          <button
                            type="button"
                            className="button booking-reject-button"
                            disabled={
                              actionId === booking.id
                            }
                            onClick={() =>
                              rejectBooking(booking.id)
                            }
                          >
                            <XCircle size={18} />
                            Reject
                          </button>

                          <button
                            type="button"
                            className="button"
                            disabled={
                              actionId === booking.id
                            }
                            onClick={() =>
                              acceptBooking(booking.id)
                            }
                          >
                            <CheckCircle2 size={18} />
                            Accept
                          </button>
                        </>
                      )}

                      {status === "accepted" && (
                        <button
                          type="button"
                          className="button"
                          disabled={
                            actionId === booking.id
                          }
                          onClick={() =>
                            completeBooking(booking.id)
                          }
                        >
                          <CheckCircle2 size={18} />
                          Mark completed
                        </button>
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
          CONFIRM MODAL
      ====================================================== */}

      {confirmModal.show && (
        <div
          className="modal-overlay"
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(15, 23, 42, 0.6)",
            backdropFilter: "blur(4px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 9999,
          }}
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) {
              setConfirmModal({
                show: false,
                type: null,
                bookingId: null,
                paymentId: null,
                title: "",
                message: "",
                needsReason: false,
                reason: "",
              });
            }
          }}
        >
          <div
            className="modal-container"
            style={{
              background: "#ffffff",
              padding: "24px",
              borderRadius: "16px",
              maxWidth: "440px",
              width: "90%",
              boxShadow:
                "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
            }}
          >
            <div
              className="modal-header"
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "16px",
              }}
            >
              <h2
                style={{
                  fontSize: "20px",
                  fontWeight: "700",
                  color: "#0f172a",
                  margin: 0,
                }}
              >
                {confirmModal.title}
              </h2>
              <button
                className="icon-button"
                onClick={() =>
                  setConfirmModal({
                    show: false,
                    type: null,
                    bookingId: null,
                    paymentId: null,
                    title: "",
                    message: "",
                    needsReason: false,
                    reason: "",
                  })
                }
                style={{
                  border: "none",
                  background: "none",
                  cursor: "pointer",
                  color: "#64748b",
                }}
              >
                <X size={20} />
              </button>
            </div>

            <div
              className="modal-body"
              style={{
                marginBottom: "24px",
                color: "#475569",
                fontSize: "15px",
                lineHeight: "1.5",
              }}
            >
              <p>{confirmModal.message}</p>
            </div>

            {confirmModal.needsReason && (
              <div style={{ marginBottom: "16px" }}>
                <label
                  style={{
                    display: "block",
                    fontSize: "14px",
                    fontWeight: "600",
                    color: "#374151",
                    marginBottom: "6px",
                  }}
                >
                  Reason (optional)
                </label>
                <textarea
                  className="text-input"
                  rows={3}
                  value={confirmModal.reason}
                  onChange={(event) =>
                    setConfirmModal((prev) => ({
                      ...prev,
                      reason: event.target.value,
                    }))
                  }
                  placeholder="Why are you rejecting this booking?"
                  style={{
                    width: "100%",
                    padding: "10px",
                    borderRadius: "8px",
                    border: "1px solid #e2e8f0",
                    fontSize: "14px",
                    resize: "vertical",
                  }}
                />
              </div>
            )}

            <div
              className="modal-footer"
              style={{
                display: "flex",
                justifyContent: "flex-end",
                gap: "12px",
              }}
            >
              <button
                className="button button-outline"
                onClick={() =>
                  setConfirmModal({
                    show: false,
                    type: null,
                    bookingId: null,
                    paymentId: null,
                    title: "",
                    message: "",
                    needsReason: false,
                    reason: "",
                  })
                }
                style={{
                  padding: "10px 16px",
                  borderRadius: "10px",
                  fontWeight: "600",
                  cursor: "pointer",
                }}
              >
                Cancel
              </button>
              <button
                className="button button-danger"
                onClick={handleConfirmAction}
                style={{
                  padding: "10px 16px",
                  borderRadius: "10px",
                  fontWeight: "600",
                  backgroundColor: "#dc2626",
                  color: "#ffffff",
                  border: "none",
                  cursor: "pointer",
                }}
              >
                Confirm
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}