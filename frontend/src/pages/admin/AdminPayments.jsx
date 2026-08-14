import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  CreditCard,
  RefreshCw,
  Search,
  WalletCards,
} from "lucide-react";

import api from "../../api/api";


function extractPayments(response) {
  const data =
    response?.data?.data ??
    response?.data ??
    [];

  if (Array.isArray(data)) {
    return data;
  }

  if (Array.isArray(data?.items)) {
    return data.items;
  }

  return [];
}


function formatPrice(value) {
  return new Intl.NumberFormat("en-PK", {
    style: "currency",
    currency: "PKR",
    maximumFractionDigits: 0,
  }).format(Number(value || 0));
}


function formatMethod(value) {
  const method =
    String(value || "").toLowerCase();

  if (method === "cash") {
    return "Cash on service";
  }

  if (method === "jazzcash") {
    return "JazzCash";
  }

  if (method === "easypaisa") {
    return "Easypaisa";
  }

  return method || "Unknown";
}


function formatStatus(value) {
  const status =
    String(value || "").toLowerCase();

  if (!status) {
    return "Unknown";
  }

  return (
    status.charAt(0).toUpperCase() +
    status.slice(1)
  );
}


function formatDate(value) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "—";
  }

  return date.toLocaleString("en-PK", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}


export default function AdminPayments() {
  const [payments, setPayments] =
    useState([]);

  const [loading, setLoading] =
    useState(true);

  const [updatingId, setUpdatingId] =
    useState(null);

  const [search, setSearch] =
    useState("");

  const [statusFilter, setStatusFilter] =
    useState("all");

  const [error, setError] =
    useState("");

  const [message, setMessage] =
    useState("");


  // =========================================================
  // LOAD PAYMENTS
  // =========================================================

  const loadPayments =
    useCallback(async () => {
      try {
        setLoading(true);
        setError("");

        const response = await api.get(
          "/payments/admin/all",
        );

        setPayments(
          extractPayments(response),
        );
      } catch (requestError) {
        setPayments([]);

        setError(
          requestError.response?.data?.message ||
            requestError.response?.data?.detail ||
            "Unable to load platform payments.",
        );
      } finally {
        setLoading(false);
      }
    }, []);


  useEffect(() => {
    loadPayments();
  }, [loadPayments]);


  // =========================================================
  // UPDATE STATUS
  // =========================================================

  const updatePaymentStatus = async (
    payment,
    newStatus,
  ) => {
    if (
      !payment ||
      !newStatus ||
      newStatus === payment.status
    ) {
      return;
    }

    const confirmed = window.confirm(
      `Change payment ${payment.transaction_reference} to ${newStatus}?`,
    );

    if (!confirmed) {
      return;
    }

    try {
      setUpdatingId(payment.id);
      setError("");
      setMessage("");

      const response = await api.patch(
        `/payments/admin/${payment.id}/status`,
        {
          status: newStatus,
          gateway_reference:
            payment.gateway_reference || null,
          failure_reason:
            newStatus === "failed"
              ? "Payment marked failed by administrator."
              : null,
        },
      );

      const updated =
        response?.data?.data ??
        response?.data;

      setPayments((current) =>
        current.map((item) =>
          item.id === updated.id
            ? updated
            : item,
        ),
      );

      setMessage(
        `Payment updated to ${formatStatus(
          updated.status,
        )}.`,
      );
    } catch (requestError) {
      setError(
        requestError.response?.data?.message ||
          requestError.response?.data?.detail ||
          "Unable to update payment status.",
      );
    } finally {
      setUpdatingId(null);
    }
  };


  // =========================================================
  // FILTER
  // =========================================================

  const filteredPayments = useMemo(() => {
    const keyword =
      search.trim().toLowerCase();

    return payments.filter((payment) => {
      const paymentStatus =
        String(
          payment.status || "",
        ).toLowerCase();

      const matchesStatus =
        statusFilter === "all" ||
        paymentStatus === statusFilter;

      const matchesSearch =
        !keyword ||
        [
          payment.transaction_reference,
          payment.gateway_reference,
          payment.booking_id,
          payment.customer_id,
          payment.provider_id,
          payment.payment_method,
          payment.status,
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
    });
  }, [
    payments,
    search,
    statusFilter,
  ]);


  // =========================================================
  // STATS
  // =========================================================

  const stats = useMemo(() => {
    return payments.reduce(
      (current, payment) => {
        const status =
          String(
            payment.status || "",
          ).toLowerCase();

        current.total += 1;

        if (current[status] !== undefined) {
          current[status] += 1;
        }

        if (status === "paid") {
          current.revenue +=
            Number(payment.amount || 0);
        }

        return current;
      },
      {
        total: 0,
        pending: 0,
        paid: 0,
        failed: 0,
        refunded: 0,
        revenue: 0,
      },
    );
  }, [payments]);


  // =========================================================
  // UI
  // =========================================================

  return (
    <main className="admin-page">
      <div className="admin-container">

        <section className="admin-title-row">
          <div>
            <span className="eyebrow">
              Financial management
            </span>

            <h1>Payments</h1>

            <p>
              Review customer payments and manage
              transaction statuses.
            </p>
          </div>

          <button
            type="button"
            className="button button-outline"
            onClick={loadPayments}
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
        </section>


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


        {/* STATS */}

        <section className="admin-payment-stats">

          <article>
            <CreditCard size={22} />

            <div>
              <span>Total payments</span>
              <strong>{stats.total}</strong>
            </div>
          </article>

          <article>
            <WalletCards size={22} />

            <div>
              <span>Paid</span>
              <strong>{stats.paid}</strong>
            </div>
          </article>

          <article>
            <CreditCard size={22} />

            <div>
              <span>Pending</span>
              <strong>{stats.pending}</strong>
            </div>
          </article>

          <article>
            <WalletCards size={22} />

            <div>
              <span>Paid value</span>

              <strong>
                {formatPrice(
                  stats.revenue,
                )}
              </strong>
            </div>
          </article>

        </section>


        {/* FILTER */}

        <section className="admin-payment-toolbar">

          <div className="admin-payment-search">
            <Search size={18} />

            <input
              type="search"
              value={search}
              onChange={(event) =>
                setSearch(
                  event.target.value,
                )
              }
              placeholder="Search transaction, booking or user ID..."
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

            <option value="paid">
              Paid
            </option>

            <option value="failed">
              Failed
            </option>

            <option value="refunded">
              Refunded
            </option>
          </select>

        </section>


        {/* TABLE */}

        <section className="admin-payment-panel">

          {loading ? (
            <div className="page-loading">
              <RefreshCw
                className="spin"
                size={28}
              />

              Loading payments...
            </div>
          ) : filteredPayments.length ===
            0 ? (
            <div className="admin-empty-state">
              <CreditCard size={42} />

              <h3>No payments found</h3>

              <p>
                No transactions match the
                current filters.
              </p>
            </div>
          ) : (
            <div className="admin-payment-table-wrap">

              <table className="admin-payment-table">

                <thead>
                  <tr>
                    <th>Transaction</th>
                    <th>Booking</th>
                    <th>Method</th>
                    <th>Amount</th>
                    <th>Status</th>
                    <th>Created</th>
                    <th>Manage</th>
                  </tr>
                </thead>

                <tbody>
                  {filteredPayments.map(
                    (payment) => {
                      const paymentStatus =
                        String(
                          payment.status ||
                            "",
                        ).toLowerCase();

                      return (
                        <tr key={payment.id}>

                          <td>
                            <strong>
                              {payment.transaction_reference ||
                                `PAY-${payment.id}`}
                            </strong>

                            {payment.gateway_reference && (
                              <small>
                                {
                                  payment.gateway_reference
                                }
                              </small>
                            )}
                          </td>


                          <td>
                            <strong>
                              #
                              {
                                payment.booking_id
                              }
                            </strong>

                            <small>
                              Customer #
                              {
                                payment.customer_id
                              }
                            </small>
                          </td>


                          <td>
                            {formatMethod(
                              payment.payment_method,
                            )}
                          </td>


                          <td>
                            <strong>
                              {formatPrice(
                                payment.amount,
                              )}
                            </strong>
                          </td>


                          <td>
                            <span
                              className={`admin-payment-status payment-${paymentStatus}`}
                            >
                              {formatStatus(
                                payment.status,
                              )}
                            </span>
                          </td>


                          <td>
                            {formatDate(
                              payment.created_at,
                            )}
                          </td>


                          <td>
                            <select
                              value={
                                payment.status
                              }
                              disabled={
                                updatingId ===
                                payment.id
                              }
                              onChange={(event) =>
                                updatePaymentStatus(
                                  payment,
                                  event.target
                                    .value,
                                )
                              }
                            >
                              <option value="pending">
                                Pending
                              </option>

                              <option value="paid">
                                Paid
                              </option>

                              <option value="failed">
                                Failed
                              </option>

                              <option value="refunded">
                                Refunded
                              </option>
                            </select>
                          </td>

                        </tr>
                      );
                    },
                  )}
                </tbody>

              </table>

            </div>
          )}

        </section>

      </div>
    </main>
  );
}