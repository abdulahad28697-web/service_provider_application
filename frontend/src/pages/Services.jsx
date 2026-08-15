import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  CalendarDays,
  Clock3,
  MapPin,
  Plus,
  RefreshCw,
  Search,
  SlidersHorizontal,
  Star,
  Store,
  Wrench,
  X,
  Heart,
  Settings,
  Phone,
  UserRound,
} from "lucide-react";

import api from "../api/api";


const WEEKDAYS = [
  "sunday",
  "monday",
  "tuesday",
  "wednesday",
  "thursday",
  "friday",
  "saturday",
];


function getLocalDateString(date = new Date()) {
  const year = date.getFullYear();
  const month = String(
    date.getMonth() + 1,
  ).padStart(2, "0");
  const day = String(
    date.getDate(),
  ).padStart(2, "0");

  return `${year}-${month}-${day}`;
}


function normalizeTime(value) {
  return String(value || "").slice(0, 5);
}


function timeToMinutes(value) {
  const [hours, minutes] = normalizeTime(value)
    .split(":")
    .map(Number);

  return hours * 60 + minutes;
}


function minutesToTime(value) {
  const hours = Math.floor(value / 60);
  const minutes = value % 60;

  return `${String(hours).padStart(2, "0")}:${String(
    minutes,
  ).padStart(2, "0")}`;
}


function formatSlotTime(value) {
  if (!value) {
    return "";
  }

  const [hours, minutes] = value.split(":");
  const date = new Date();

  date.setHours(Number(hours), Number(minutes), 0, 0);

  return date.toLocaleTimeString("en-PK", {
    hour: "numeric",
    minute: "2-digit",
  });
}


export default function Services() {
  const navigate = useNavigate();

  // Use the browser's LOCAL date, not UTC.
  // This prevents timezone shifts from allowing yesterday.
  const today = getLocalDateString();

  const [services, setServices] = useState([]);
  const [search, setSearch] = useState("");

  const [categoryFilter, setCategoryFilter] = useState("all");
  const [minimumRating, setMinimumRating] = useState("0");
  const [minimumPrice, setMinimumPrice] = useState("");
  const [maximumPrice, setMaximumPrice] = useState("");
  const [sortBy, setSortBy] = useState("recommended");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [selectedService, setSelectedService] = useState(null);
  const [bookingError, setBookingError] = useState("");
  const [bookingSuccess, setBookingSuccess] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [providerAvailability, setProviderAvailability] = useState([]);
  const [availabilityLoading, setAvailabilityLoading] = useState(false);
  const [availabilityError, setAvailabilityError] = useState("");
  const [availableTimeSlots, setAvailableTimeSlots] = useState([]);
  const [slotsLoading, setSlotsLoading] = useState(false);

  const [bookingForm, setBookingForm] = useState({
    scheduled_date: "",
    scheduled_start: "",
    customer_name: "",
    phone_number: "",
    location: "",
    customer_notes: "",
  });

  const [favoriteServiceIds, setFavoriteServiceIds] =
    useState([]);
  const [searchParams] = useSearchParams();
  const [savedAddresses, setSavedAddresses] = useState([]);

  // ---------------------------------------------------------
  // CURRENT USER
  // ---------------------------------------------------------

  let currentUser = null;

  try {
    currentUser = JSON.parse(
      localStorage.getItem("current_user") || "null",
    );
  } catch {
    currentUser = null;
  }

  const isProvider = currentUser?.role === "provider";
  const isCustomer = currentUser?.role === "customer";

  // ---------------------------------------------------------
  // FAVORITES
  // ---------------------------------------------------------

  const toggleFavorite = async (serviceId) => {
    if (!localStorage.getItem("access_token")) {
      navigate("/login");
      return;
    }

    // Providers should not favorite services.
    if (isProvider) {
      return;
    }

    try {
      const isFavorite =
        favoriteServiceIds.includes(serviceId);

      if (isFavorite) {
        await api.delete(
          `/users/me/favorites/${serviceId}`,
        );

        setFavoriteServiceIds((current) =>
          current.filter((id) => id !== serviceId),
        );
      } else {
        await api.post(
          `/users/me/favorites/${serviceId}`,
        );

        setFavoriteServiceIds((current) => [
          ...current,
          serviceId,
        ]);
      }
    } catch (requestError) {
      setError(
        requestError.response?.data?.message ||
          requestError.response?.data?.detail ||
          "Unable to update favorites.",
      );
    }
  };

  // ---------------------------------------------------------
  // LOAD SERVICES
  // ---------------------------------------------------------

  const loadServices = async () => {
    setLoading(true);
    setError("");

    try {
      let requestParams = {
        page_size: 100,
      };

      let loggedInProviderId = null;

      /*
       * PROVIDER:
       * First get the logged-in provider profile.
       * Then request only services belonging to that provider.
       *
       * CUSTOMER / PUBLIC:
       * Do not provide provider_id, therefore all active
       * services are returned.
       */
      if (isProvider) {
        const profileResponse = await api.get(
          "/providers/me",
        );

        const provider =
          profileResponse?.data?.data ??
          profileResponse?.data;

        if (!provider?.id) {
          throw new Error(
            "Provider profile could not be identified.",
          );
        }

        loggedInProviderId = Number(provider.id);

        requestParams = {
          ...requestParams,
          provider_id: loggedInProviderId,
        };
      }

      const response = await api.get("/services", {
        params: requestParams,
      });

      const payload =
        response?.data?.data ??
        response?.data ??
        {};

      const items = Array.isArray(payload)
        ? payload
        : Array.isArray(payload?.items)
          ? payload.items
          : [];

      /*
       * Extra frontend protection.
       *
       * Even though the backend already receives provider_id,
       * providers are filtered again here so another provider's
       * service can never accidentally appear in this UI.
       */
      if (isProvider && loggedInProviderId) {
        const ownServices = items.filter(
          (service) =>
            Number(service.provider_id) ===
            loggedInProviderId,
        );

        setServices(ownServices);
      } else {
        setServices(items);
      }
    } catch (requestError) {
      setServices([]);

      setError(
        requestError.response?.data?.message ||
          requestError.response?.data?.detail ||
          requestError.message ||
          "Unable to load services.",
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadServices();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Load customer favorites (service IDs)
  useEffect(() => {
    if (!isCustomer) return;

    const loadFavorites = async () => {
      try {
        const response = await api.get("/users/me/favorites");
        const items =
          response?.data?.data ??
          response?.data ??
          [];
        const ids = (Array.isArray(items) ? items : []).map(
          (fav) => Number(fav.service_id ?? fav.id),
        );
        setFavoriteServiceIds(ids);
      } catch {
        // ignore – favorites are non-critical
      }
    };

    loadFavorites();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Auto-open a specific service from URL ?service=ID
  useEffect(() => {
    const serviceIdParam = searchParams.get("service");
    if (!serviceIdParam || services.length === 0 || !isCustomer) return;

    const targetId = Number(serviceIdParam);
    const targetService = services.find(
      (s) => Number(s.id) === targetId,
    );

    if (targetService) {
      openBookingForm(targetService);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [services, searchParams]);

  // ---------------------------------------------------------
  // SEARCH / FILTERS / SORTING
  // ---------------------------------------------------------

  const categoryOptions = useMemo(() => {
    const values = services
      .map(
        (service) =>
          service.category_name ||
          service.category?.name ||
          "",
      )
      .filter(Boolean)
      .map((value) => String(value).trim())
      .filter(Boolean);

    return Array.from(new Set(values)).sort(
      (a, b) => a.localeCompare(b),
    );
  }, [services]);


  const filteredServices = useMemo(() => {
    const keyword = search.trim().toLowerCase();

    const minRating = Number(minimumRating || 0);

    const minPrice =
      minimumPrice === ""
        ? null
        : Number(minimumPrice);

    const maxPrice =
      maximumPrice === ""
        ? null
        : Number(maximumPrice);

    const filtered = services.filter((service) => {
      const category =
        service.category_name ||
        service.category?.name ||
        "";

      const rating = Number(
        service.provider_rating ?? 0,
      );

      const price = Number(
        service.price ?? 0,
      );

      const matchesSearch =
        !keyword ||
        [
          service.title,
          service.description,
          category,
          service.provider_name,
        ]
          .filter(Boolean)
          .some((value) =>
            String(value)
              .toLowerCase()
              .includes(keyword),
          );

      const matchesCategory =
        categoryFilter === "all" ||
        String(category) === categoryFilter;

      const matchesRating =
        rating >= minRating;

      const matchesMinimumPrice =
        minPrice === null ||
        price >= minPrice;

      const matchesMaximumPrice =
        maxPrice === null ||
        price <= maxPrice;

      return (
        matchesSearch &&
        matchesCategory &&
        matchesRating &&
        matchesMinimumPrice &&
        matchesMaximumPrice
      );
    });

    return [...filtered].sort((a, b) => {
      const ratingA = Number(
        a.provider_rating ?? 0,
      );

      const ratingB = Number(
        b.provider_rating ?? 0,
      );

      const priceA = Number(
        a.price ?? 0,
      );

      const priceB = Number(
        b.price ?? 0,
      );

      const reviewsA = Number(
        a.review_count ?? 0,
      );

      const reviewsB = Number(
        b.review_count ?? 0,
      );

      if (sortBy === "rating_desc") {
        return (
          ratingB - ratingA ||
          reviewsB - reviewsA
        );
      }

      if (sortBy === "price_asc") {
        return priceA - priceB;
      }

      if (sortBy === "price_desc") {
        return priceB - priceA;
      }

      if (sortBy === "newest") {
        return (
          new Date(
            b.created_at || 0,
          ).getTime() -
          new Date(
            a.created_at || 0,
          ).getTime()
        );
      }

      /*
       * Recommended:
       * 1. Featured services
       * 2. Higher provider rating
       * 3. More reviews
       */
      return (
        Number(Boolean(b.is_featured)) -
          Number(Boolean(a.is_featured)) ||
        ratingB - ratingA ||
        reviewsB - reviewsA
      );
    });
  }, [
    services,
    search,
    categoryFilter,
    minimumRating,
    minimumPrice,
    maximumPrice,
    sortBy,
  ]);


  const filtersActive =
    search.trim() !== "" ||
    categoryFilter !== "all" ||
    minimumRating !== "0" ||
    minimumPrice !== "" ||
    maximumPrice !== "" ||
    sortBy !== "recommended";


  const clearFilters = () => {
    setSearch("");
    setCategoryFilter("all");
    setMinimumRating("0");
    setMinimumPrice("");
    setMaximumPrice("");
    setSortBy("recommended");
  };


  // ---------------------------------------------------------
  // BOOKING
  // ---------------------------------------------------------

  const openBookingForm = async (service) => {
    const token = localStorage.getItem("access_token");

    if (!token) {
      navigate("/login", {
        state: {
          message:
            "Please sign in before booking a service.",
        },
      });

      return;
    }

    if (!isCustomer) {
      setError(
        "Only customer accounts can create bookings.",
      );
      return;
    }

    setError("");
    setBookingError("");
    setBookingSuccess("");
    setAvailabilityError("");
    setAvailabilityLoading(true);
    setProviderAvailability([]);
    setAvailableTimeSlots([]);

    let customerName = currentUser?.full_name || "";
    let phoneNumber = "";

    try {
      const [
        profileResponse,
        availabilityResponse,
        addressesResponse,
      ] = await Promise.all([
        api.get("/users/me"),
        api.get(
          `/providers/${service.provider_id}/availability`,
        ),
        api.get("/users/me/addresses").catch(() => ({ data: [] })),
      ]);

      const profile =
        profileResponse?.data?.data ??
        profileResponse?.data ??
        {};

      customerName =
        profile?.full_name ||
        currentUser?.full_name ||
        "";

      phoneNumber =
        profile?.phone_number || "";

      const availabilityData =
        availabilityResponse?.data?.data ??
        availabilityResponse?.data ??
        [];

      const availabilityRows = Array.isArray(
        availabilityData,
      )
        ? availabilityData
        : Array.isArray(availabilityData?.items)
          ? availabilityData.items
          : [];

      setProviderAvailability(
        availabilityRows.map((slot) => ({
          ...slot,
          day_of_week: String(
            slot.day_of_week || "",
          ).toLowerCase(),
          start_time: normalizeTime(slot.start_time),
          end_time: normalizeTime(slot.end_time),
        })),
      );

      // Load saved addresses and pre-fill location
      const addressPayload =
        addressesResponse?.data?.data ??
        addressesResponse?.data ??
        [];

      const addresses = Array.isArray(addressPayload)
        ? addressPayload
        : Array.isArray(addressPayload?.items)
          ? addressPayload.items
          : [];

      setSavedAddresses(addresses);

      const defaultAddress = addresses.find(
        (a) => a.is_default,
      ) || addresses[0] || null;

      const defaultLocation = defaultAddress
        ? [
            defaultAddress.address_line_1 ||
              defaultAddress.address_line ||
              defaultAddress.address ||
              defaultAddress.street_address,
            defaultAddress.city,
            defaultAddress.state ||
              defaultAddress.state_or_province ||
              defaultAddress.province,
            defaultAddress.postal_code ||
              defaultAddress.zip_code,
            defaultAddress.country,
          ]
            .filter(Boolean)
            .join(", ")
        : "";

      setSelectedService(service);

      setBookingForm({
        scheduled_date: "",
        scheduled_start: "",
        customer_name: customerName,
        phone_number: phoneNumber,
        location: defaultLocation,
        customer_notes: "",
      });
    } catch (requestError) {
      const message =
        requestError.response?.data?.message ||
        requestError.response?.data?.detail ||
        "Unable to load booking information.";

      setError(message);
      setAvailabilityError(message);
    } finally {
      setAvailabilityLoading(false);
    }
  };

  const closeBookingForm = () => {
    if (submitting) {
      return;
    }

    setSelectedService(null);
    setBookingError("");
    setBookingSuccess("");
    setAvailabilityError("");
    setProviderAvailability([]);
    setAvailableTimeSlots([]);
  };

  const updateBookingField = (event) => {
    const { name, value } = event.target;

    setBookingForm((current) => ({
      ...current,
      [name]: value,
      ...(name === "scheduled_date"
        ? { scheduled_start: "" }
        : {}),
    }));

    if (name === "scheduled_date") {
      setBookingError("");
      setAvailabilityError("");
      setAvailableTimeSlots([]);
    }
  };

  const submitBooking = async (event) => {
    event.preventDefault();

    if (!selectedService) {
      return;
    }

    setBookingError("");
    setBookingSuccess("");

    if (
      !bookingForm.scheduled_date ||
      !bookingForm.scheduled_start
    ) {
      setBookingError(
        "Please select a booking date and start time.",
      );

      return;
    }

    if (bookingForm.scheduled_date < today) {
      setBookingError(
        "Past dates cannot be booked. Please choose today or a future date.",
      );

      return;
    }

    // Extra protection for bookings made for today:
    // a time that has already passed cannot be submitted.
    if (bookingForm.scheduled_date === today) {
      const now = new Date();
      const nowMinutes =
        now.getHours() * 60 +
        now.getMinutes();

      if (
        timeToMinutes(
          bookingForm.scheduled_start,
        ) <= nowMinutes
      ) {
        setBookingError(
          "That time has already passed. Please choose a later time.",
        );

        return;
      }
    }

    if (!bookingForm.customer_name.trim()) {
      setBookingError(
        "Please enter your full name.",
      );
      return;
    }

    if (
      !bookingForm.phone_number.trim() ||
      bookingForm.phone_number.trim().length < 7
    ) {
      setBookingError(
        "Please enter a valid phone number.",
      );
      return;
    }

    setSubmitting(true);

    try {
      // Keep the account/profile information up to date so
      // providers can see the customer's current name and phone.
      await api.patch("/users/me", {
        full_name: bookingForm.customer_name.trim(),
        phone_number: bookingForm.phone_number.trim(),
      });

      await api.post("/bookings", {
        service_id: selectedService.id,
        scheduled_date:
          bookingForm.scheduled_date,
        scheduled_start:
          bookingForm.scheduled_start,
        location: bookingForm.location.trim(),
        customer_notes:
          bookingForm.customer_notes.trim(),
      });

      setBookingSuccess(
        "Booking request sent successfully.",
      );

      setTimeout(() => {
        setSelectedService(null);
        navigate("/bookings");
      }, 900);
    } catch (requestError) {
      const responseData =
        requestError.response?.data;

      setBookingError(
        responseData?.message ||
          responseData?.detail ||
          "Unable to create the booking.",
      );
    } finally {
      setSubmitting(false);
    }
  };

  const selectedAvailability = useMemo(() => {
    if (!bookingForm.scheduled_date) {
      return null;
    }

    const selectedDate = new Date(
      `${bookingForm.scheduled_date}T00:00:00`,
    );

    const weekday = WEEKDAYS[selectedDate.getDay()];

    return (
      providerAvailability.find(
        (slot) =>
          slot.day_of_week === weekday &&
          slot.is_available !== false,
      ) || null
    );
  }, [
    bookingForm.scheduled_date,
    providerAvailability,
  ]);


  useEffect(() => {
    const loadAvailableSlots = async () => {
      if (
        !selectedService ||
        !bookingForm.scheduled_date
      ) {
        setAvailableTimeSlots([]);
        return;
      }

      // Never request slots for a past date.
      if (bookingForm.scheduled_date < today) {
        setAvailableTimeSlots([]);

        setAvailabilityError(
          "Past dates cannot be booked. Please choose today or a future date.",
        );

        setBookingForm((current) => ({
          ...current,
          scheduled_start: "",
        }));

        return;
      }

      if (!selectedAvailability) {
        setAvailableTimeSlots([]);
        return;
      }

      try {
        setSlotsLoading(true);
        setAvailabilityError("");

        const response = await api.get(
          `/providers/${selectedService.provider_id}/available-slots`,
          {
            params: {
              service_id: selectedService.id,
              date: bookingForm.scheduled_date,
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

        let normalizedSlots = slots
          .map((slot) => normalizeTime(slot))
          .filter(Boolean);

        // If the customer books for today, remove times that
        // have already passed even if the API returns them.
        if (bookingForm.scheduled_date === today) {
          const now = new Date();

          const nowMinutes =
            now.getHours() * 60 +
            now.getMinutes();

          normalizedSlots =
            normalizedSlots.filter(
              (slot) =>
                timeToMinutes(slot) >
                nowMinutes,
            );
        }

        setAvailableTimeSlots(
          normalizedSlots,
        );
      } catch (requestError) {
        setAvailableTimeSlots([]);

        setAvailabilityError(
          requestError.response?.data?.message ||
            requestError.response?.data?.detail ||
            "Unable to load available booking times.",
        );
      } finally {
        setSlotsLoading(false);
      }
    };

    loadAvailableSlots();
  }, [
    selectedService,
    bookingForm.scheduled_date,
    selectedAvailability,
    today,
  ]);


  // ---------------------------------------------------------
  // UI
  // ---------------------------------------------------------

  return (
    <section className="page-section services-page">
      <div className="page-container">
        <div className="page-heading-row">
          <div>
            <span className="eyebrow">
              {isProvider
                ? "Your services"
                : "Find professionals"}
            </span>

            <h1>
              {isProvider
                ? "Manage your available services"
                : "Explore available services"}
            </h1>

            <p>
              {isProvider
                ? "View the services you offer to customers and add new services."
                : "Compare active services and choose the right provider for your needs."}
            </p>
          </div>

          {/* -----------------------------------------------
              PAGE ACTIONS
              Add Service is INSIDE this page, not navbar.
          ------------------------------------------------ */}

          <div className="heading-actions">
            {isProvider && (
              <button
                type="button"
                className="button"
                onClick={() =>
                  navigate("/provider/services")
                }
              >
                <Plus size={18} />
                Add Service
              </button>
            )}

            <button
              type="button"
              className="button button-outline"
              onClick={loadServices}
              disabled={loading}
            >
              <RefreshCw
                size={17}
                className={
                  loading ? "spin" : ""
                }
              />

              Refresh
            </button>
          </div>
        </div>

        {/* Provider information */}

        {isProvider && (
          <div className="provider-services-notice">
            <Wrench size={18} />

            <span>
              Only your own services are shown here.
              Services created by other providers are
              hidden from your provider view.
            </span>
          </div>
        )}

        {/* Search */}

        <div className="search-panel">
          <Search size={20} />

          <input
            type="search"
            value={search}
            onChange={(event) =>
              setSearch(event.target.value)
            }
            placeholder={
              isProvider
                ? "Search your services..."
                : "Search cleaning, plumbing, repairs..."
            }
          />
        </div>

        {!isProvider && (
          <section className="service-filter-panel">
            <div className="service-filter-panel-header">
              <div>
                <SlidersHorizontal size={19} />

                <div>
                  <strong>Filter services</strong>
                  <span>
                    Narrow results by category, rating
                    and price.
                  </span>
                </div>
              </div>

              <div className="service-filter-results">
                <strong>
                  {filteredServices.length}
                </strong>
                <span>
                  {filteredServices.length === 1
                    ? "service"
                    : "services"}
                </span>
              </div>
            </div>

            <div className="service-filter-grid">
              <label>
                <span>Category</span>

                <select
                  value={categoryFilter}
                  onChange={(event) =>
                    setCategoryFilter(
                      event.target.value,
                    )
                  }
                >
                  <option value="all">
                    All categories
                  </option>

                  {categoryOptions.map(
                    (category) => (
                      <option
                        key={category}
                        value={category}
                      >
                        {category}
                      </option>
                    ),
                  )}
                </select>
              </label>

              <label>
                <span>Minimum rating</span>

                <select
                  value={minimumRating}
                  onChange={(event) =>
                    setMinimumRating(
                      event.target.value,
                    )
                  }
                >
                  <option value="0">
                    Any rating
                  </option>
                  <option value="3">
                    3.0+ stars
                  </option>
                  <option value="4">
                    4.0+ stars
                  </option>
                  <option value="4.5">
                    4.5+ stars
                  </option>
                </select>
              </label>

              <label>
                <span>Minimum price</span>

                <input
                  type="number"
                  min="0"
                  step="1"
                  value={minimumPrice}
                  onChange={(event) =>
                    setMinimumPrice(
                      event.target.value,
                    )
                  }
                  placeholder="PKR 0"
                />
              </label>

              <label>
                <span>Maximum price</span>

                <input
                  type="number"
                  min="0"
                  step="1"
                  value={maximumPrice}
                  onChange={(event) =>
                    setMaximumPrice(
                      event.target.value,
                    )
                  }
                  placeholder="No limit"
                />
              </label>

              <label>
                <span>Sort by</span>

                <select
                  value={sortBy}
                  onChange={(event) =>
                    setSortBy(
                      event.target.value,
                    )
                  }
                >
                  <option value="recommended">
                    Recommended
                  </option>
                  <option value="rating_desc">
                    Highest rated
                  </option>
                  <option value="price_asc">
                    Lowest price
                  </option>
                  <option value="price_desc">
                    Highest price
                  </option>
                  <option value="newest">
                    Newest
                  </option>
                </select>
              </label>

              <div className="service-filter-clear-wrap">
                <button
                  type="button"
                  className="button button-outline service-filter-clear"
                  onClick={clearFilters}
                  disabled={!filtersActive}
                >
                  Clear filters
                </button>
              </div>
            </div>
          </section>
        )}

        {error && (
          <div className="alert alert-error">
            {error}
          </div>
        )}

        {/* Services */}

        {loading ? (
          <div className="page-loader">
            <div className="loader-spinner" />
            <p>Loading services...</p>
          </div>
        ) : filteredServices.length === 0 ? (
          <div className="empty-state">
            <Wrench size={42} />

            <h2>
              {isProvider
                ? "You have no services yet"
                : "No services found"}
            </h2>

            <p>
              {isProvider
                ? "Create your first service so customers can find and book you."
                : "Try another search or check again after providers publish services."}
            </p>

            {isProvider && (
              <button
                type="button"
                className="button"
                onClick={() =>
                  navigate("/provider/services")
                }
              >
                <Plus size={18} />
                Add your first service
              </button>
            )}
          </div>
        ) : (
          <div className="service-grid">
            {filteredServices.map((service) => (
              <article
                className="service-card"
                key={service.id}
              >
                <div className="service-image">
                  {/* Favorite only for customers/public */}

                  {!isProvider && (
                    <button
                      type="button"
                      className={`favorite-button ${
                        favoriteServiceIds.includes(
                          service.id,
                        )
                          ? "favorite-button-active"
                          : ""
                      }`}
                      onClick={(event) => {
                        event.stopPropagation();

                        toggleFavorite(
                          service.id,
                        );
                      }}
                      aria-label="Save service to favorites"
                      title="Save service to favorites"
                    >
                      <Heart
                        size={22}
                        fill={
                          favoriteServiceIds.includes(
                            service.id,
                          )
                            ? "currentColor"
                            : "none"
                        }
                      />
                    </button>
                  )}

                  {service.images?.[0] ? (
                    <img
                      src={
                        service.images[0].startsWith(
                          "http",
                        )
                          ? service.images[0]
                          : `http://localhost:8000${service.images[0]}`
                      }
                      alt={service.title}
                    />
                  ) : (
                    <Wrench size={36} />
                  )}

                  {service.is_featured && (
                    <span className="featured-badge">
                      <Star
                        size={14}
                        fill="currentColor"
                      />
                      Featured
                    </span>
                  )}
                </div>

                <div className="service-card-content">
                  <span className="service-category">
                    {service.category_name ||
                      service.category?.name ||
                      "Professional service"}
                  </span>

                  <h2>{service.title}</h2>

                  {service.provider_name && (
                    <div className="service-provider-label">
                      <Store size={14} />
                      <span>Provided by <strong>{service.provider_name}</strong></span>
                    </div>
                  )}

<div className="service-rating">
  <Star
    size={17}
    fill="currentColor"
  />

  <strong>
    {Number(
      service.provider_rating ?? 0,
    ).toFixed(1)}
  </strong>

  <span>
    (
    {Number(
      service.review_count ?? 0,
    )}{" "}
    {Number(
      service.review_count ?? 0,
    ) === 1
      ? "review"
      : "reviews"}
    )
  </span>
</div>

<p>
  {service.description ||
    "Professional service available for booking."}
</p>

                  <div className="service-meta">
                    <span>
                      <Clock3 size={16} />

                      {service.duration_minutes || 60} min
                    </span>

                    <strong>
                      PKR{" "}
                      {Number(
                        service.price || 0,
                      ).toLocaleString()}

                      <small>
                        {" "}
                        {service.price_unit
                          ?.replaceAll("_", " ")}
                      </small>
                    </strong>
                  </div>

                  {/* Provider manages service.
                      Customer books service. */}

                  {isProvider ? (
                    <button
                      type="button"
                      className="button button-full"
                      onClick={() =>
                        navigate("/provider/services")
                      }
                    >
                      <Settings size={18} />
                      Manage service
                    </button>
                  ) : (
                    <button
                      type="button"
                      className="button button-full"
                      onClick={() =>
                        openBookingForm(service)
                      }
                    >
                      View and book
                    </button>
                  )}
                </div>
              </article>
            ))}
          </div>
        )}
      </div>

      {/* ---------------------------------------------------
          BOOKING MODAL — CUSTOMER ONLY
      ---------------------------------------------------- */}

      {selectedService && isCustomer && (
        <div
          className="modal-overlay"
          onMouseDown={(event) => {
            if (
              event.target === event.currentTarget
            ) {
              closeBookingForm();
            }
          }}
        >
          <div
            className="modal-card booking-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="booking-title"
          >
            <button
              type="button"
              className="modal-close"
              onClick={closeBookingForm}
              aria-label="Close booking form"
            >
              <X size={22} />
            </button>

            <div className="modal-heading">
              <span className="eyebrow">
                Book service
              </span>

              <h2 id="booking-title">
                {selectedService.title}
              </h2>

              <p>
                Choose your preferred date, time and
                location.
              </p>
            </div>

            {bookingError && (
              <div className="alert alert-error">
                {bookingError}
              </div>
            )}

            {bookingSuccess && (
              <div className="alert alert-success">
                {bookingSuccess}
              </div>
            )}

            <form
              className="auth-form"
              onSubmit={submitBooking}
            >
              <label className="form-field">
                <span>Booking date</span>

                <div className="input-with-icon">
                  <CalendarDays size={18} />

                  <input
                    type="date"
                    name="scheduled_date"
                    value={
                      bookingForm.scheduled_date
                    }
                    onChange={updateBookingField}
                    min={today}
                    required
                  />
                </div>

                {bookingForm.scheduled_date &&
                  bookingForm.scheduled_date < today && (
                    <small className="availability-help availability-help-error">
                      Past dates cannot be booked. Please choose
                      today or a future date.
                    </small>
                  )}
              </label>

              <label className="form-field">
                <span>Available start time</span>

                <div className="input-with-icon">
                  <Clock3 size={18} />

                  <select
                    name="scheduled_start"
                    value={
                      bookingForm.scheduled_start
                    }
                    onChange={updateBookingField}
                    disabled={
                      availabilityLoading ||
                      slotsLoading ||
                      !bookingForm.scheduled_date ||
                      bookingForm.scheduled_date < today ||
                      !selectedAvailability ||
                      availableTimeSlots.length === 0
                    }
                    required
                  >
                    <option value="">
                      {availabilityLoading || slotsLoading
                        ? "Loading available times..."
                        : !bookingForm.scheduled_date
                          ? "Choose a date first"
                          : !selectedAvailability
                            ? "Provider unavailable this day"
                            : availableTimeSlots.length === 0
                              ? "No free times available"
                              : "Select an available time"}
                    </option>

                    {availableTimeSlots.map((time) => (
                      <option
                        key={time}
                        value={time}
                      >
                        {formatSlotTime(time)}
                      </option>
                    ))}
                  </select>
                </div>

                {bookingForm.scheduled_date &&
                  !availabilityLoading &&
                  !selectedAvailability && (
                    <small className="availability-help availability-help-error">
                      This provider is not available on the
                      selected day. Please choose another date.
                    </small>
                  )}

                {selectedAvailability &&
                  availableTimeSlots.length > 0 &&
                  !slotsLoading && (
                    <small className="availability-help">
                      Showing only free times between{" "}
                      {formatSlotTime(
                        selectedAvailability.start_time,
                      )}{" "}
                      and{" "}
                      {formatSlotTime(
                        selectedAvailability.end_time,
                      )}. Already booked times are hidden.
                    </small>
                  )}

                {selectedAvailability &&
                  bookingForm.scheduled_date &&
                  !slotsLoading &&
                  availableTimeSlots.length === 0 &&
                  !availabilityError && (
                    <small className="availability-help availability-help-error">
                      No free booking times remain for this date.
                      Please choose another day.
                    </small>
                  )}

                {availabilityError && (
                  <small className="availability-help availability-help-error">
                    {availabilityError}
                  </small>
                )}
              </label>

              <label className="form-field">
                <span>Customer name</span>

                <div className="input-with-icon">
                  <UserRound size={18} />

                  <input
                    type="text"
                    name="customer_name"
                    value={bookingForm.customer_name}
                    onChange={updateBookingField}
                    placeholder="Enter your full name"
                    maxLength={255}
                    required
                  />
                </div>
              </label>

              <label className="form-field">
                <span>Phone number</span>

                <div className="input-with-icon">
                  <Phone size={18} />

                  <input
                    type="tel"
                    name="phone_number"
                    value={bookingForm.phone_number}
                    onChange={updateBookingField}
                    placeholder="03XX XXXXXXX"
                    minLength={7}
                    maxLength={30}
                    required
                  />
                </div>
              </label>

              <label className="form-field">
                <span>Service location</span>

                {savedAddresses.length > 0 && (
                  <div className="input-with-icon">
                    <MapPin size={18} />

                    <select
                      value=""
                      onChange={(event) => {
                        if (event.target.value) {
                          setBookingForm((current) => ({
                            ...current,
                            location: event.target.value,
                          }));
                        }
                      }}
                    >
                      <option value="">
                        Use a saved address
                      </option>

                      {savedAddresses.map((addr) => {
                        const full = [
                          addr.address_line_1 ||
                            addr.address_line ||
                            addr.address ||
                            addr.street_address,
                          addr.city,
                          addr.state ||
                            addr.state_or_province ||
                            addr.province,
                          addr.postal_code ||
                            addr.zip_code,
                          addr.country,
                        ]
                          .filter(Boolean)
                          .join(", ");

                        return (
                          <option
                            key={addr.id}
                            value={full}
                          >
                            {addr.label || "Address"}
                            {addr.is_default
                              ? " (Default)"
                              : ""}{" "}
                            — {full}
                          </option>
                        );
                      })}
                    </select>
                  </div>
                )}

                <div className="input-with-icon">
                  <MapPin size={18} />

                  <input
                    type="text"
                    name="location"
                    value={bookingForm.location}
                    onChange={updateBookingField}
                    placeholder="House number, street and city"
                    maxLength={255}
                  />
                </div>
              </label>

              <label className="form-field">
                <span>Additional notes</span>

                <textarea
                  name="customer_notes"
                  value={
                    bookingForm.customer_notes
                  }
                  onChange={updateBookingField}
                  placeholder="Describe your requirements..."
                  rows={4}
                  maxLength={2000}
                />
              </label>

              <div className="modal-actions">
                <button
                  type="button"
                  className="button button-outline"
                  onClick={closeBookingForm}
                  disabled={submitting}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="button"
                  disabled={submitting}
                >
                  {submitting
                    ? "Sending request..."
                    : "Confirm booking"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </section>
  );
}