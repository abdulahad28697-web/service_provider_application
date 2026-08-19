import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  Banknote,
  CreditCard,
  RefreshCw,
  TrendingUp,
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


function formatPaymentMethod(value) {
  const method =
    String(value || "").toLowerCase();

  if (method === "cash") {
    return "Cash";
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


export default function ProviderEarnings() {
  const [payments, setPayments] =
    useState([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");


  // =========================================================
  // LOAD PROVIDER PAYMENTS
  // =========================================================

  const loadPayments =
    useCallback(async () => {
      try {
        setLoading(true);
        setError("");

        const response = await api.get(
          "/payments/provider",
        );

        setPayments(
          extractPayments(response),
        );
      } catch (requestError) {
        setPayments([]);

        setError(
          requestError.response?.data?.message ||
            requestError.response?.data?.detail ||
            "Unable to load provider earnings.",
        );
      } finally {
        setLoading(false);
      }
    }, []);


  useEffect(() => {
    loadPayments();
  }, [loadPayments]);


  // =========================================================
  // SUMMARY
  // =========================================================

  const summary = useMemo(() => {
    return payments.reduce(
      (current, payment) => {
        const amount =
          Number(payment.amount || 0);

        const status =
          String(
            payment.status || "",
          ).toLowerCase();

        const method =
          String(
            payment.payment_method || "",
          ).toLowerCase();

        current.totalTransactions += 1;

        if (status === "paid") {
          current.paidAmount += amount;
          current.paidTransactions += 1;

          if (method === "cash") {
            current.cash += amount;
          }

          if (method === "jazzcash") {
            current.jazzcash += amount;
          }

          if (method === "easypaisa") {
            current.easypaisa += amount;
          }
        }

        if (status === "pending") {
          current.pendingAmount += amount;
          current.pendingTransactions += 1;
        }

        if (status === "refunded") {
          current.refundedAmount += amount;
        }

        return current;
      },
      {
        totalTransactions: 0,
        paidTransactions: 0,
        pendingTransactions: 0,

        paidAmount: 0,
        pendingAmount: 0,
        refundedAmount: 0,

        cash: 0,
        jazzcash: 0,
        easypaisa: 0,
      },
    );
  }, [payments]);


  // =========================================================
  // MONTHLY EARNINGS
  // =========================================================

  const monthlyEarnings = useMemo(() => {
    const groups = {};

    payments.forEach((payment) => {
      if (
        String(
          payment.status || "",
        ).toLowerCase() !== "paid"
      ) {
        return;
      }

      const date = new Date(
        payment.created_at,
      );

      if (Number.isNaN(date.getTime())) {
        return;
      }

      const key = `${date.getFullYear()}-${String(
        date.getMonth() + 1,
      ).padStart(2, "0")}`;

      if (!groups[key]) {
        groups[key] = {
          key,
          label: date.toLocaleDateString(
            "en-PK",
            {
              month: "short",
              year: "numeric",
            },
          ),
          amount: 0,
          count: 0,
        };
      }

      groups[key].amount +=
        Number(payment.amount || 0);

      groups[key].count += 1;
    });

    return Object.values(groups)
      .sort((a, b) =>
        b.key.localeCompare(a.key),
      )
      .slice(0, 6);
  }, [payments]);


  // =========================================================
  // RECENT TRANSACTIONS
  // =========================================================

  const recentPayments = useMemo(() => {
    return [...payments]
      .sort(
        (a, b) =>
          new Date(
            b.created_at || 0,
          ).getTime() -
          new Date(
            a.created_at || 0,
          ).getTime(),
      )
      .slice(0, 10);
  }, [payments]);


  // =========================================================
  // UI
  // =========================================================

  return (
    <main className="provider-earnings-page">
      <div className="provider-earnings-container">

        {/* HEADER */}

        <section className="provider-earnings-header">
          <div>
            <span className="eyebrow">
              Provider finance
            </span>

            <h1>Earnings & revenue</h1>

            <p>
              Track paid bookings, pending
              payments and your recent
              ServiceHub transactions.
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


        {/* SUMMARY CARDS */}

        <section className="provider-earnings-stats">

          <article>
            <span className="provider-earnings-stat-icon">
              <TrendingUp size={24} />
            </span>

            <div>
              <span>
                Total paid earnings
              </span>

              <strong>
                {formatPrice(
                  summary.paidAmount,
                )}
              </strong>

              <small>
                {
                  summary.paidTransactions
                }{" "}
                paid transactions
              </small>
            </div>
          </article>


          <article>
            <span className="provider-earnings-stat-icon pending">
              <WalletCards size={24} />
            </span>

            <div>
              <span>
                Pending amount
              </span>

              <strong>
                {formatPrice(
                  summary.pendingAmount,
                )}
              </strong>

              <small>
                {
                  summary.pendingTransactions
                }{" "}
                pending transactions
              </small>
            </div>
          </article>


          <article>
            <span className="provider-earnings-stat-icon cash">
              <Banknote size={24} />
            </span>

            <div>
              <span>
                Cash earnings
              </span>

              <strong>
                {formatPrice(
                  summary.cash,
                )}
              </strong>
            </div>
          </article>


          <article>
            <span className="provider-earnings-stat-icon cash">
              <Banknote size={24} />
            </span>

            <div>
              <span>
                Total collected
              </span>

              <strong>
                {formatPrice(
                  summary.paidAmount,
                )}
              </strong>
            </div>
          </article>

        </section>


        {/* PAYMENT OVERVIEW */}

        <section className="provider-earnings-methods">

          <article>
            <span>
              Cash on Service
            </span>

            <strong>
              {formatPrice(
                summary.cash || summary.paidAmount,
              )}
            </strong>
          </article>

          <article>
            <span>
              Pending Collection
            </span>

            <strong>
              {formatPrice(
                summary.pendingAmount,
              )}
            </strong>
          </article>

          <article>
            <span>
              Completed Bookings
            </span>

            <strong>
              {summary.paidTransactions}
            </strong>
          </article>

          <article>
            <span>
              Total transactions
            </span>

            <strong>
              {
                summary.totalTransactions
              }
            </strong>
          </article>

        </section>


        {/* MONTHLY EARNINGS */}

        <section className="provider-earnings-panel">

          <div className="provider-earnings-panel-header">
            <div>
              <span className="eyebrow">
                Revenue history
              </span>

              <h2>
                Monthly earnings
              </h2>
            </div>
          </div>


          {monthlyEarnings.length === 0 ? (
            <div className="provider-earnings-empty">
              <TrendingUp size={38} />

              <h3>
                No paid earnings yet
              </h3>

              <p>
                Paid transactions will
                appear here.
              </p>
            </div>
          ) : (
            <div className="provider-monthly-earnings-list">

              {monthlyEarnings.map(
                (month) => (
                  <div
                    className="provider-monthly-earning-row"
                    key={month.key}
                  >
                    <div>
                      <strong>
                        {month.label}
                      </strong>

                      <span>
                        {month.count}{" "}
                        {month.count === 1
                          ? "transaction"
                          : "transactions"}
                      </span>
                    </div>

                    <strong>
                      {formatPrice(
                        month.amount,
                      )}
                    </strong>
                  </div>
                ),
              )}

            </div>
          )}

        </section>


        {/* RECENT TRANSACTIONS */}

        <section className="provider-earnings-panel">

          <div className="provider-earnings-panel-header">
            <div>
              <span className="eyebrow">
                Payment activity
              </span>

              <h2>
                Recent transactions
              </h2>
            </div>
          </div>


          {loading ? (
            <div className="provider-earnings-empty">
              <RefreshCw
                className="spin"
                size={32}
              />

              <p>
                Loading transactions...
              </p>
            </div>
          ) : recentPayments.length ===
            0 ? (
            <div className="provider-earnings-empty">
              <CreditCard size={38} />

              <h3>
                No transactions yet
              </h3>

              <p>
                Customer payments will
                appear here.
              </p>
            </div>
          ) : (
            <div className="provider-earnings-table-wrap">

              <table className="provider-earnings-table">

                <thead>
                  <tr>
                    <th>Transaction</th>
                    <th>Booking</th>
                    <th>Method</th>
                    <th>Amount</th>
                    <th>Status</th>
                    <th>Date</th>
                  </tr>
                </thead>

                <tbody>

                  {recentPayments.map(
                    (payment) => {
                      const status =
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
                          </td>

                          <td>
                            #
                            {
                              payment.booking_id
                            }
                          </td>

                          <td>
                            {formatPaymentMethod(
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
                              className={`provider-earning-status payment-${status}`}
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