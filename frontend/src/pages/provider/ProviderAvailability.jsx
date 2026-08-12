import { useCallback, useEffect, useMemo, useState } from "react";
import {
  CalendarClock,
  CheckCircle2,
  Clock3,
  RefreshCw,
  Save,
} from "lucide-react";

import api from "../../api/api";


const DAYS = [
  "monday",
  "tuesday",
  "wednesday",
  "thursday",
  "friday",
  "saturday",
  "sunday",
];


function getData(response) {
  return response?.data?.data ?? response?.data ?? [];
}


function createDefaultDay(day) {
  return {
    id: null,
    day_of_week: day,
    start_time: "09:00",
    end_time: "17:00",
    is_available: false,
  };
}


export default function ProviderAvailability() {
  const [schedule, setSchedule] = useState(
    DAYS.map(createDefaultDay),
  );

  const [loading, setLoading] = useState(true);
  const [savingDay, setSavingDay] = useState(null);

  const [error, setError] = useState("");
  const [message, setMessage] = useState("");


  const loadSchedule = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const response = await api.get(
        "/bookings/schedules",
      );

      const data = getData(response);

      const rows = Array.isArray(data)
        ? data
        : Array.isArray(data?.items)
          ? data.items
          : [];

      const hydrated = DAYS.map((day) => {
        const existing = rows.find(
          (row) =>
            String(
              row.day_of_week,
            ).toLowerCase() === day,
        );

        if (!existing) {
          return createDefaultDay(day);
        }

        return {
          id: existing.id,
          day_of_week: day,
          start_time:
            String(
              existing.start_time || "09:00",
            ).slice(0, 5),
          end_time:
            String(
              existing.end_time || "17:00",
            ).slice(0, 5),
          is_available:
            Boolean(existing.is_available),
        };
      });

      setSchedule(hydrated);
    } catch (requestError) {
      setError(
        requestError.response?.data?.message ||
          requestError.response?.data?.detail ||
          "Unable to load availability.",
      );
    } finally {
      setLoading(false);
    }
  }, []);


  useEffect(() => {
    loadSchedule();
  }, [loadSchedule]);


  const activeDays = useMemo(
    () =>
      schedule.filter(
        (slot) => slot.is_available,
      ).length,
    [schedule],
  );


  const updateDay = (
    day,
    field,
    value,
  ) => {
    setSchedule((current) =>
      current.map((slot) =>
        slot.day_of_week === day
          ? {
              ...slot,
              [field]: value,
            }
          : slot,
      ),
    );
  };


  const saveDay = async (slot) => {
    if (
      slot.is_available &&
      slot.start_time >= slot.end_time
    ) {
      setError(
        `${formatDay(slot.day_of_week)}: start time must be before end time.`,
      );

      return;
    }

    setSavingDay(slot.day_of_week);
    setError("");
    setMessage("");

    try {
      /*
       * Your backend PUT /bookings/schedules
       * already creates OR updates a provider's
       * weekly slot for a given day.
       */
      const response = await api.put(
        "/bookings/schedules",
        {
          day_of_week:
            slot.day_of_week,
          start_time:
            slot.start_time,
          end_time:
            slot.end_time,
          is_available:
            slot.is_available,
        },
      );

      const saved =
        getData(response);

      setSchedule((current) =>
        current.map((item) =>
          item.day_of_week ===
          slot.day_of_week
            ? {
                ...item,
                id:
                  saved?.id ??
                  item.id,
                start_time:
                  String(
                    saved?.start_time ??
                    item.start_time,
                  ).slice(0, 5),
                end_time:
                  String(
                    saved?.end_time ??
                    item.end_time,
                  ).slice(0, 5),
                is_available:
                  saved?.is_available ??
                  item.is_available,
              }
            : item,
        ),
      );

      setMessage(
        `${formatDay(
          slot.day_of_week,
        )} availability saved.`,
      );
    } catch (requestError) {
      setError(
        requestError.response?.data?.message ||
          requestError.response?.data?.detail ||
          "Unable to save availability.",
      );
    } finally {
      setSavingDay(null);
    }
  };


  function formatDay(day) {
    return (
      day.charAt(0).toUpperCase() +
      day.slice(1)
    );
  }


  return (
    <main className="provider-availability-page">
      <div className="provider-availability-container">

        <section className="provider-availability-header">
          <div>
            <span className="eyebrow">
              Provider schedule
            </span>

            <h1>
              Weekly availability
            </h1>

            <p>
              Choose the days and working hours
              customers can request your services.
            </p>
          </div>

          <button
            type="button"
            className="button"
            onClick={loadSchedule}
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


        <section className="provider-availability-summary">
          <div>
            <CalendarClock size={23} />

            <span>
              <small>Available days</small>
              <strong>
                {activeDays} / 7
              </strong>
            </span>
          </div>

          <p>
            Customers will eventually see only
            these available hours when booking.
          </p>
        </section>


        {error && (
          <div className="alert alert-error">
            {error}
          </div>
        )}

        {message && (
          <div className="alert alert-success">
            <CheckCircle2 size={18} />
            {message}
          </div>
        )}


        {loading ? (
          <div className="provider-availability-empty">
            <RefreshCw
              className="spin"
              size={34}
            />

            <h2>
              Loading your schedule...
            </h2>
          </div>
        ) : (
          <div className="provider-availability-list">

            {schedule.map((slot) => (
              <article
                className={`provider-availability-card ${
                  slot.is_available
                    ? "active"
                    : ""
                }`}
                key={slot.day_of_week}
              >
                <div className="provider-availability-day">
                  <div>
                    <strong>
                      {formatDay(
                        slot.day_of_week,
                      )}
                    </strong>

                    <span>
                      {slot.is_available
                        ? "Available"
                        : "Unavailable"}
                    </span>
                  </div>

                  <label className="availability-switch">
                    <input
                      type="checkbox"
                      checked={
                        slot.is_available
                      }
                      onChange={(event) =>
                        updateDay(
                          slot.day_of_week,
                          "is_available",
                          event.target.checked,
                        )
                      }
                    />

                    <span />
                  </label>
                </div>


                <div className="provider-availability-times">

                  <label>
                    <span>
                      <Clock3 size={16} />
                      Start time
                    </span>

                    <input
                      type="time"
                      value={
                        slot.start_time
                      }
                      disabled={
                        !slot.is_available
                      }
                      onChange={(event) =>
                        updateDay(
                          slot.day_of_week,
                          "start_time",
                          event.target.value,
                        )
                      }
                    />
                  </label>


                  <label>
                    <span>
                      <Clock3 size={16} />
                      End time
                    </span>

                    <input
                      type="time"
                      value={
                        slot.end_time
                      }
                      disabled={
                        !slot.is_available
                      }
                      onChange={(event) =>
                        updateDay(
                          slot.day_of_week,
                          "end_time",
                          event.target.value,
                        )
                      }
                    />
                  </label>
                </div>


                <button
                  type="button"
                  className="button button-full"
                  onClick={() =>
                    saveDay(slot)
                  }
                  disabled={
                    savingDay ===
                    slot.day_of_week
                  }
                >
                  <Save size={18} />

                  {savingDay ===
                  slot.day_of_week
                    ? "Saving..."
                    : "Save day"}
                </button>
              </article>
            ))}

          </div>
        )}
      </div>
    </main>
  );
}