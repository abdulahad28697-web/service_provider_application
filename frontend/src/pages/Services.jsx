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
  CheckCircle2,
  AlertCircle,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  ChevronRight,
  DollarSign,
  Sun,
  Sunset,
  Moon,
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
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function normalizeTime(value) {
  return String(value || "").slice(0, 5);
}

function timeToMinutes(value) {
  const [hours, minutes] = normalizeTime(value).split(":").map(Number);
  return hours * 60 + (minutes || 0);
}

function formatSlotTime(value) {
  if (!value) return "";
  const [hours, minutes] = value.split(":");
  const date = new Date();
  date.setHours(Number(hours), Number(minutes), 0, 0);
  return date.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
}

function formatDateDisplay(dateStr) {
  if (!dateStr) return "";
  const d = new Date(`${dateStr}T00:00:00`);
  return d.toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
}

export default function Services() {
  const navigate = useNavigate();
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

  // Booking Modal State
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

  const [favoriteServiceIds, setFavoriteServiceIds] = useState([]);
  const [searchParams] = useSearchParams();
  const [savedAddresses, setSavedAddresses] = useState([]);

  // Auth User
  let currentUser = null;
  try {
    currentUser = JSON.parse(localStorage.getItem("current_user") || "null");
  } catch {
    currentUser = null;
  }

  const isProvider = currentUser?.role === "provider";
  const isCustomer = currentUser?.role === "customer";

  // Favorites
  const toggleFavorite = async (serviceId) => {
    if (!localStorage.getItem("access_token")) {
      navigate("/login");
      return;
    }
    if (isProvider) return;

    try {
      const isFavorite = favoriteServiceIds.includes(serviceId);
      if (isFavorite) {
        await api.delete(`/users/me/favorites/${serviceId}`);
        setFavoriteServiceIds((current) => current.filter((id) => id !== serviceId));
      } else {
        await api.post(`/users/me/favorites/${serviceId}`);
        setFavoriteServiceIds((current) => [...current, serviceId]);
      }
    } catch (requestError) {
      setError(
        requestError.response?.data?.message ||
          requestError.response?.data?.detail ||
          "Unable to update favorites."
      );
    }
  };

  // Load Services
  const loadServices = async () => {
    setLoading(true);
    setError("");

    try {
      let requestParams = { page_size: 100 };
      let loggedInProviderId = null;

      if (isProvider) {
        const profileResponse = await api.get("/providers/me");
        const provider = profileResponse?.data?.data ?? profileResponse?.data;
        if (provider?.id) {
          loggedInProviderId = Number(provider.id);
          requestParams.provider_id = loggedInProviderId;
        }
      }

      const response = await api.get("/services", { params: requestParams });
      const payload = response?.data?.data ?? response?.data ?? {};
      const items = Array.isArray(payload)
        ? payload
        : Array.isArray(payload?.items)
        ? payload.items
        : [];

      if (isProvider && loggedInProviderId) {
        setServices(items.filter((s) => Number(s.provider_id) === loggedInProviderId));
      } else {
        setServices(items);
      }
    } catch (requestError) {
      setServices([]);
      setError(
        requestError.response?.data?.message ||
          requestError.response?.data?.detail ||
          requestError.message ||
          "Unable to load services."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadServices();
  }, []);

  // Load customer favorites
  useEffect(() => {
    if (!isCustomer) return;
    const loadFavorites = async () => {
      try {
        const response = await api.get("/users/me/favorites");
        const items = response?.data?.data ?? response?.data ?? [];
        const ids = (Array.isArray(items) ? items : []).map((fav) =>
          Number(fav.service_id ?? fav.id)
        );
        setFavoriteServiceIds(ids);
      } catch {
        // ignore
      }
    };
    loadFavorites();
  }, [isCustomer]);

  // Deep-link from query param ?service=ID
  useEffect(() => {
    const serviceIdParam = searchParams.get("service");
    if (!serviceIdParam || services.length === 0 || !isCustomer) return;
    const targetId = Number(serviceIdParam);
    const targetService = services.find((s) => Number(s.id) === targetId);
    if (targetService) {
      openBookingForm(targetService);
    }
  }, [services, searchParams]);

  // Filter Categories
  const categoryOptions = useMemo(() => {
    const values = services
      .map((service) => service.category_name || service.category?.name || "")
      .filter(Boolean)
      .map((value) => String(value).trim())
      .filter(Boolean);
    return Array.from(new Set(values)).sort((a, b) => a.localeCompare(b));
  }, [services]);

  // Filtered Services List
  const filteredServices = useMemo(() => {
    const keyword = search.trim().toLowerCase();
    const minRating = Number(minimumRating || 0);
    const minPrice = minimumPrice === "" ? null : Number(minimumPrice);
    const maxPrice = maximumPrice === "" ? null : Number(maximumPrice);

    const filtered = services.filter((service) => {
      const category = service.category_name || service.category?.name || "";
      const rating = Number(service.provider_rating ?? 0);
      const price = Number(service.price ?? 0);

      const matchesSearch =
        !keyword ||
        [service.title, service.description, category, service.provider_name]
          .filter(Boolean)
          .some((value) => String(value).toLowerCase().includes(keyword));

      const matchesCategory =
        categoryFilter === "all" || String(category) === categoryFilter;
      const matchesRating = rating >= minRating;
      const matchesMinimumPrice = minPrice === null || price >= minPrice;
      const matchesMaximumPrice = maxPrice === null || price <= maxPrice;

      return (
        matchesSearch &&
        matchesCategory &&
        matchesRating &&
        matchesMinimumPrice &&
        matchesMaximumPrice
      );
    });

    return [...filtered].sort((a, b) => {
      const ratingA = Number(a.provider_rating ?? 0);
      const ratingB = Number(b.provider_rating ?? 0);
      const priceA = Number(a.price ?? 0);
      const priceB = Number(b.price ?? 0);
      const reviewsA = Number(a.review_count ?? 0);
      const reviewsB = Number(b.review_count ?? 0);

      if (sortBy === "rating_desc") return ratingB - ratingA || reviewsB - reviewsA;
      if (sortBy === "price_asc") return priceA - priceB;
      if (sortBy === "price_desc") return priceB - priceA;
      if (sortBy === "newest") {
        return new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime();
      }
      return (
        Number(Boolean(b.is_featured)) - Number(Boolean(a.is_featured)) ||
        ratingB - ratingA ||
        reviewsB - reviewsA
      );
    });
  }, [services, search, categoryFilter, minimumRating, minimumPrice, maximumPrice, sortBy]);

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

  // Quick date helpers for modal
  const quickDates = useMemo(() => {
    const dates = [];
    const base = new Date();
    for (let i = 0; i < 4; i++) {
      const d = new Date(base);
      d.setDate(base.getDate() + i);
      const dateStr = getLocalDateString(d);
      let label = "";
      if (i === 0) label = "Today";
      else if (i === 1) label = "Tomorrow";
      else label = d.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
      dates.push({ dateStr, label });
    }
    return dates;
  }, []);

  // Open Booking Modal
  async function openBookingForm(service) {
    const token = localStorage.getItem("access_token");
    if (!token) {
      navigate("/login", {
        state: { message: "Please sign in before booking a service." },
      });
      return;
    }

    if (!isCustomer) {
      setError("Only customer accounts can create bookings.");
      return;
    }

    setError("");
    setBookingError("");
    setBookingSuccess("");
    setAvailabilityError("");
    setAvailabilityLoading(true);
    setProviderAvailability([]);
    setAvailableTimeSlots([]);

    // Default to tomorrow or today
    const defaultDate = quickDates[1]?.dateStr || today;

    let customerName = currentUser?.full_name || "";
    let phoneNumber = "";

    try {
      const [profileResponse, availabilityResponse, addressesResponse] =
        await Promise.all([
          api.get("/users/me").catch(() => ({ data: {} })),
          api.get(`/providers/${service.provider_id}/availability`).catch(() => ({ data: [] })),
          api.get("/users/me/addresses").catch(() => ({ data: [] })),
        ]);

      const profile = profileResponse?.data?.data ?? profileResponse?.data ?? {};
      customerName = profile?.full_name || currentUser?.full_name || "";
      phoneNumber = profile?.phone_number || "";

      const availabilityData =
        availabilityResponse?.data?.data ?? availabilityResponse?.data ?? [];
      const availabilityRows = Array.isArray(availabilityData)
        ? availabilityData
        : Array.isArray(availabilityData?.items)
        ? availabilityData.items
        : [];

      setProviderAvailability(
        availabilityRows.map((slot) => ({
          ...slot,
          day_of_week: String(slot.day_of_week || "").toLowerCase(),
          start_time: normalizeTime(slot.start_time),
          end_time: normalizeTime(slot.end_time),
        }))
      );

      const addressPayload =
        addressesResponse?.data?.data ?? addressesResponse?.data ?? [];
      const addresses = Array.isArray(addressPayload)
        ? addressPayload
        : Array.isArray(addressPayload?.items)
        ? addressPayload.items
        : [];

      setSavedAddresses(addresses);

      const defaultAddress = addresses.find((a) => a.is_default) || addresses[0] || null;
      const defaultLocation = defaultAddress
        ? [
            defaultAddress.address_line_1 ||
              defaultAddress.address_line ||
              defaultAddress.address ||
              defaultAddress.street_address,
            defaultAddress.city,
            defaultAddress.state || defaultAddress.state_or_province || defaultAddress.province,
            defaultAddress.postal_code || defaultAddress.zip_code,
            defaultAddress.country,
          ]
            .filter(Boolean)
            .join(", ")
        : "";

      setSelectedService(service);
      setBookingForm({
        scheduled_date: defaultDate,
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
        "Unable to initialize booking.";
      setError(message);
      setAvailabilityError(message);
    } finally {
      setAvailabilityLoading(false);
    }
  }

  const closeBookingForm = () => {
    if (submitting) return;
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
      ...(name === "scheduled_date" ? { scheduled_start: "" } : {}),
    }));

    if (name === "scheduled_date") {
      setBookingError("");
      setAvailabilityError("");
      setAvailableTimeSlots([]);
    }
  };

  const selectQuickDate = (dateStr) => {
    setBookingForm((current) => ({
      ...current,
      scheduled_date: dateStr,
      scheduled_start: "",
    }));
    setBookingError("");
    setAvailabilityError("");
    setAvailableTimeSlots([]);
  };

  const selectTimeSlot = (time) => {
    setBookingForm((current) => ({
      ...current,
      scheduled_start: time,
    }));
    setBookingError("");
  };

  // Determine current day availability
  const selectedAvailability = useMemo(() => {
    if (!bookingForm.scheduled_date) return null;
    const selectedDate = new Date(`${bookingForm.scheduled_date}T00:00:00`);
    const weekday = WEEKDAYS[selectedDate.getDay()];

    const match = providerAvailability.find(
      (slot) => slot.day_of_week === weekday && slot.is_available !== false
    );

    // Fallback: If provider has no explicit availability records, default to available 08:00 - 20:00
    if (!match && providerAvailability.length === 0) {
      return {
        day_of_week: weekday,
        start_time: "08:00",
        end_time: "20:00",
        is_available: true,
      };
    }
    return match || null;
  }, [bookingForm.scheduled_date, providerAvailability]);

  // Load available time slots when date changes
  useEffect(() => {
    const loadAvailableSlots = async () => {
      if (!selectedService || !bookingForm.scheduled_date) {
        setAvailableTimeSlots([]);
        return;
      }

      if (bookingForm.scheduled_date < today) {
        setAvailableTimeSlots([]);
        setAvailabilityError("Past dates cannot be booked. Please choose today or a future date.");
        setBookingForm((current) => ({ ...current, scheduled_start: "" }));
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
          }
        );

        const payload = response?.data?.data ?? response?.data ?? {};
        const slots = Array.isArray(payload)
          ? payload
          : Array.isArray(payload?.slots)
          ? payload.slots
          : [];

        let normalizedSlots = slots.map((s) => normalizeTime(s)).filter(Boolean);

        // If today, filter out passed times
        if (bookingForm.scheduled_date === today) {
          const now = new Date();
          const nowMinutes = now.getHours() * 60 + now.getMinutes();
          normalizedSlots = normalizedSlots.filter((s) => timeToMinutes(s) > nowMinutes);
        }

        setAvailableTimeSlots(normalizedSlots);
      } catch (requestError) {
        setAvailableTimeSlots([]);
        setAvailabilityError(
          requestError.response?.data?.message ||
            requestError.response?.data?.detail ||
            "Unable to load available time slots."
        );
      } finally {
        setSlotsLoading(false);
      }
    };

    loadAvailableSlots();
  }, [selectedService, bookingForm.scheduled_date, today]);

  // Group slots by period
  const groupedSlots = useMemo(() => {
    const morning = [];
    const afternoon = [];
    const evening = [];

    availableTimeSlots.forEach((slot) => {
      const minutes = timeToMinutes(slot);
      if (minutes < 12 * 60) {
        morning.push(slot);
      } else if (minutes < 17 * 60) {
        afternoon.push(slot);
      } else {
        evening.push(slot);
      }
    });

    return { morning, afternoon, evening };
  }, [availableTimeSlots]);

  // Submit Booking
  const submitBooking = async (event) => {
    event.preventDefault();
    if (!selectedService) return;

    setBookingError("");
    setBookingSuccess("");

    if (!bookingForm.scheduled_date || !bookingForm.scheduled_start) {
      setBookingError("Please select both a booking date and a time slot.");
      return;
    }

    if (bookingForm.scheduled_date < today) {
      setBookingError("Past dates cannot be booked. Please choose today or a future date.");
      return;
    }

    if (bookingForm.scheduled_date === today) {
      const now = new Date();
      const nowMinutes = now.getHours() * 60 + now.getMinutes();
      if (timeToMinutes(bookingForm.scheduled_start) <= nowMinutes) {
        setBookingError("That time has already passed. Please choose a later time.");
        return;
      }
    }

    if (!bookingForm.customer_name.trim()) {
      setBookingError("Please enter your full name.");
      return;
    }

    if (!bookingForm.phone_number.trim() || bookingForm.phone_number.trim().length < 7) {
      setBookingError("Please enter a valid phone number.");
      return;
    }

    if (!bookingForm.location.trim()) {
      setBookingError("Please provide the service location address.");
      return;
    }

    setSubmitting(true);

    try {
      await api.patch("/users/me", {
        full_name: bookingForm.customer_name.trim(),
        phone_number: bookingForm.phone_number.trim(),
      }).catch(() => {});

      await api.post("/bookings", {
        service_id: selectedService.id,
        scheduled_date: bookingForm.scheduled_date,
        scheduled_start: bookingForm.scheduled_start,
        location: bookingForm.location.trim(),
        customer_notes: bookingForm.customer_notes.trim(),
      });

      setBookingSuccess("Booking request sent successfully! Redirecting...");

      setTimeout(() => {
        setSelectedService(null);
        navigate("/bookings");
      }, 900);
    } catch (requestError) {
      const responseData = requestError.response?.data;
      setBookingError(
        responseData?.message || responseData?.detail || "Unable to create booking request."
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="page-section services-page">
      <div className="page-container">
        {/* Header Title Section */}
        <div className="page-heading-row">
          <div>
            <div className="badge-pill">
              <Sparkles size={14} className="text-primary" />
              <span>{isProvider ? "Provider Portal" : "Verified Services"}</span>
            </div>

            <h1 className="page-title">
              {isProvider ? "Manage your services" : "Explore & Book Services"}
            </h1>

            <p className="page-subtitle">
              {isProvider
                ? "Review and manage your listed services or publish new offerings for clients."
                : "Find trusted local experts, check transparent pricing, and book appointments instantly."}
            </p>
          </div>

          <div className="heading-actions">
            {isProvider && (
              <button
                type="button"
                className="button button-primary"
                onClick={() => navigate("/provider/services")}
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
              <RefreshCw size={17} className={loading ? "spin" : ""} />
              Refresh
            </button>
          </div>
        </div>

        {/* Provider view notice */}
        {isProvider && (
          <div className="notice-banner">
            <Wrench size={18} />
            <span>Showing only your published services. Clients view these in the public catalog.</span>
          </div>
        )}

        {/* Search & Category Filter Section */}
        <div className="filter-wrapper">
          <div className="search-bar">
            <Search size={19} className="search-icon" />
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder={
                isProvider
                  ? "Search your services by name or description..."
                  : "Search home cleaning, AC repair, plumbing, painting..."
              }
            />
            {search && (
              <button type="button" className="search-clear" onClick={() => setSearch("")}>
                <X size={16} />
              </button>
            )}
          </div>

          {!isProvider && (
            <div className="category-pills">
              <button
                type="button"
                className={`category-pill ${categoryFilter === "all" ? "active" : ""}`}
                onClick={() => setCategoryFilter("all")}
              >
                All Services
              </button>
              {categoryOptions.map((cat) => (
                <button
                  key={cat}
                  type="button"
                  className={`category-pill ${categoryFilter === cat ? "active" : ""}`}
                  onClick={() => setCategoryFilter(cat)}
                >
                  {cat}
                </button>
              ))}
            </div>
          )}

          {/* Advanced Filter Toolbar */}
          {!isProvider && (
            <div className="filter-toolbar">
              <div className="filter-controls-row">
                <div className="control-group">
                  <label htmlFor="min-rating-select">Rating</label>
                  <select
                    id="min-rating-select"
                    value={minimumRating}
                    onChange={(e) => setMinimumRating(e.target.value)}
                  >
                    <option value="0">Any rating</option>
                    <option value="3">★ 3.0+</option>
                    <option value="4">★ 4.0+</option>
                    <option value="4.5">★ 4.5+ Top Rated</option>
                  </select>
                </div>

                <div className="control-group">
                  <label htmlFor="sort-by-select">Sort By</label>
                  <select
                    id="sort-by-select"
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value)}
                  >
                    <option value="recommended">Recommended</option>
                    <option value="rating_desc">Highest Rated</option>
                    <option value="price_asc">Price: Low to High</option>
                    <option value="price_desc">Price: High to Low</option>
                    <option value="newest">Newest First</option>
                  </select>
                </div>

                <div className="control-group price-input-group">
                  <label htmlFor="min-price-input">Min Price</label>
                  <input
                    id="min-price-input"
                    type="number"
                    min="0"
                    placeholder="PKR 0"
                    value={minimumPrice}
                    onChange={(e) => setMinimumPrice(e.target.value)}
                  />
                </div>

                <div className="control-group price-input-group">
                  <label htmlFor="max-price-input">Max Price</label>
                  <input
                    id="max-price-input"
                    type="number"
                    min="0"
                    placeholder="No limit"
                    value={maximumPrice}
                    onChange={(e) => setMaximumPrice(e.target.value)}
                  />
                </div>

                {filtersActive && (
                  <button
                    type="button"
                    className="button button-subtle clear-filters-btn"
                    onClick={clearFilters}
                  >
                    Reset Filters
                  </button>
                )}
              </div>

              <div className="results-counter">
                Showing <strong>{filteredServices.length}</strong> {filteredServices.length === 1 ? "service" : "services"}
              </div>
            </div>
          )}
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        {/* Service Cards Grid */}
        {loading ? (
          <div className="page-loader">
            <div className="loader-spinner" />
            <p>Loading available services...</p>
          </div>
        ) : filteredServices.length === 0 ? (
          <div className="empty-state-card">
            <div className="empty-state-icon">
              <Wrench size={36} />
            </div>
            <h3>{isProvider ? "No services created yet" : "No matching services found"}</h3>
            <p>
              {isProvider
                ? "Add your services to let customers discover and book your expertise."
                : "Try adjusting your search criteria or resetting filters to view all services."}
            </p>
            {isProvider ? (
              <button
                type="button"
                className="button button-primary"
                onClick={() => navigate("/provider/services")}
              >
                <Plus size={18} />
                Create Service
              </button>
            ) : filtersActive ? (
              <button type="button" className="button button-outline" onClick={clearFilters}>
                Clear All Filters
              </button>
            ) : null}
          </div>
        ) : (
          <div className="services-grid">
            {filteredServices.map((service) => (
              <article className="premium-service-card" key={service.id}>
                <div className="service-card-media">
                  {service.images?.[0] ? (
                    <img
                      src={
                        service.images[0].startsWith("http")
                          ? service.images[0]
                          : `https://service-provider-backend-yea9.onrender.com${service.images[0]}`
                      }
                      alt={service.title}
                      loading="lazy"
                    />
                  ) : (
                    <div className="media-placeholder">
                      <Wrench size={40} />
                    </div>
                  )}

                  <div className="media-badges">
                    <span className="category-tag">
                      {service.category_name || service.category?.name || "Professional"}
                    </span>
                    {service.is_featured && (
                      <span className="featured-badge">
                        <Star size={13} fill="currentColor" />
                        Featured
                      </span>
                    )}
                  </div>

                  {!isProvider && (
                    <button
                      type="button"
                      className={`favorite-toggle-btn ${
                        favoriteServiceIds.includes(service.id) ? "favorited" : ""
                      }`}
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleFavorite(service.id);
                      }}
                      title="Save to favorites"
                    >
                      <Heart
                        size={19}
                        fill={favoriteServiceIds.includes(service.id) ? "currentColor" : "none"}
                      />
                    </button>
                  )}
                </div>

                <div className="service-card-body">
                  <h3 className="service-card-title">{service.title}</h3>

                  {service.provider_name && (
                    <div className="provider-indicator">
                      <Store size={14} />
                      <span>{service.provider_name}</span>
                    </div>
                  )}

                  <div className="service-meta-row">
                    <div className="rating-pill">
                      <Star size={14} className="star-icon" fill="currentColor" />
                      <strong>{Number(service.provider_rating ?? 5.0).toFixed(1)}</strong>
                      <span>({Number(service.review_count ?? 0)})</span>
                    </div>

                    <div className="duration-pill">
                      <Clock3 size={14} />
                      <span>{service.duration_minutes || 60} mins</span>
                    </div>
                  </div>

                  <p className="service-card-desc">
                    {service.description || "Professional quality service guaranteed."}
                  </p>

                  <div className="service-card-footer">
                    <div className="price-tag">
                      <span className="price-amount">
                        PKR {Number(service.price || 0).toLocaleString()}
                      </span>
                      <span className="price-unit">
                        /{service.price_unit?.replaceAll("_", " ") || "visit"}
                      </span>
                    </div>

                    {isProvider ? (
                      <button
                        type="button"
                        className="button button-outline button-sm"
                        onClick={() => navigate("/provider/services")}
                      >
                        <Settings size={15} />
                        Manage
                      </button>
                    ) : (
                      <button
                        type="button"
                        className="button button-primary button-sm"
                        onClick={() => openBookingForm(service)}
                      >
                        Book Now
                        <ArrowRight size={15} />
                      </button>
                    )}
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </div>

      {/* =======================================================
          PREMIUM BOOKING MODAL
      ======================================================== */}
      {selectedService && isCustomer && (
        <div
          className="modal-backdrop"
          onMouseDown={(e) => {
            if (e.target === e.currentTarget) closeBookingForm();
          }}
        >
          <div className="booking-modal-card" role="dialog" aria-modal="true">
            <button
              type="button"
              className="modal-close-button"
              onClick={closeBookingForm}
              aria-label="Close"
            >
              <X size={20} />
            </button>

            {/* Modal Header */}
            <div className="booking-modal-header">
              <div className="service-summary-chip">
                <span className="summary-category">
                  {selectedService.category_name || "Service"}
                </span>
                <h2 className="summary-title">{selectedService.title}</h2>
                <div className="summary-details">
                  <span>Provided by <strong>{selectedService.provider_name}</strong></span>
                  <span>•</span>
                  <span><Clock3 size={14} /> {selectedService.duration_minutes || 60} mins</span>
                  <span>•</span>
                  <strong className="text-primary">
                    PKR {Number(selectedService.price || 0).toLocaleString()}
                  </strong>
                </div>
              </div>
            </div>

            {bookingError && (
              <div className="alert alert-error modal-alert">
                <AlertCircle size={17} />
                <span>{bookingError}</span>
              </div>
            )}

            {bookingSuccess && (
              <div className="alert alert-success modal-alert">
                <CheckCircle2 size={17} />
                <span>{bookingSuccess}</span>
              </div>
            )}

            <form className="booking-form" onSubmit={submitBooking}>
              {/* Step 1: Select Date */}
              <div className="form-section">
                <div className="section-label">
                  <CalendarDays size={16} className="text-primary" />
                  <span>1. Choose Appointment Date</span>
                </div>

                <div className="quick-date-chips">
                  {quickDates.map((item) => (
                    <button
                      key={item.dateStr}
                      type="button"
                      className={`quick-date-chip ${
                        bookingForm.scheduled_date === item.dateStr ? "selected" : ""
                      }`}
                      onClick={() => selectQuickDate(item.dateStr)}
                    >
                      <span className="chip-label">{item.label}</span>
                      <span className="chip-sub">{formatDateDisplay(item.dateStr)}</span>
                    </button>
                  ))}

                  <label className={`quick-date-chip custom-date-picker ${
                    !quickDates.some((d) => d.dateStr === bookingForm.scheduled_date) &&
                    bookingForm.scheduled_date
                      ? "selected"
                      : ""
                  }`}>
                    <span className="chip-label">Custom Date</span>
                    <input
                      type="date"
                      name="scheduled_date"
                      min={today}
                      value={bookingForm.scheduled_date}
                      onChange={updateBookingField}
                      required
                    />
                  </label>
                </div>
              </div>

              {/* Step 2: Select Time Slot */}
              <div className="form-section">
                <div className="section-label">
                  <Clock3 size={16} className="text-primary" />
                  <span>2. Select Time Slot</span>
                </div>

                {slotsLoading ? (
                  <div className="slots-loading-state">
                    <div className="loader-spinner small" />
                    <span>Loading available times for {formatDateDisplay(bookingForm.scheduled_date)}...</span>
                  </div>
                ) : availableTimeSlots.length === 0 ? (
                  <div className="no-slots-notice">
                    <AlertCircle size={18} />
                    <div>
                      <strong>No available slots for this date</strong>
                      <p>
                        {availabilityError ||
                          "All slots are currently booked or the provider is unavailable. Please select another date above."}
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="time-slots-container">
                    {groupedSlots.morning.length > 0 && (
                      <div className="slot-period-group">
                        <div className="period-header">
                          <Sun size={14} /> Morning
                        </div>
                        <div className="slots-grid">
                          {groupedSlots.morning.map((slot) => (
                            <button
                              key={slot}
                              type="button"
                              className={`slot-chip ${
                                bookingForm.scheduled_start === slot ? "active" : ""
                              }`}
                              onClick={() => selectTimeSlot(slot)}
                            >
                              {formatSlotTime(slot)}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {groupedSlots.afternoon.length > 0 && (
                      <div className="slot-period-group">
                        <div className="period-header">
                          <Sunset size={14} /> Afternoon
                        </div>
                        <div className="slots-grid">
                          {groupedSlots.afternoon.map((slot) => (
                            <button
                              key={slot}
                              type="button"
                              className={`slot-chip ${
                                bookingForm.scheduled_start === slot ? "active" : ""
                              }`}
                              onClick={() => selectTimeSlot(slot)}
                            >
                              {formatSlotTime(slot)}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {groupedSlots.evening.length > 0 && (
                      <div className="slot-period-group">
                        <div className="period-header">
                          <Moon size={14} /> Evening
                        </div>
                        <div className="slots-grid">
                          {groupedSlots.evening.map((slot) => (
                            <button
                              key={slot}
                              type="button"
                              className={`slot-chip ${
                                bookingForm.scheduled_start === slot ? "active" : ""
                              }`}
                              onClick={() => selectTimeSlot(slot)}
                            >
                              {formatSlotTime(slot)}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Step 3: Contact & Address */}
              <div className="form-section">
                <div className="section-label">
                  <MapPin size={16} className="text-primary" />
                  <span>3. Location & Contact Details</span>
                </div>

                <div className="form-grid-two">
                  <label className="input-group">
                    <span>Full Name</span>
                    <div className="input-box">
                      <UserRound size={16} />
                      <input
                        type="text"
                        name="customer_name"
                        value={bookingForm.customer_name}
                        onChange={updateBookingField}
                        placeholder="Your full name"
                        required
                      />
                    </div>
                  </label>

                  <label className="input-group">
                    <span>Phone Number</span>
                    <div className="input-box">
                      <Phone size={16} />
                      <input
                        type="tel"
                        name="phone_number"
                        value={bookingForm.phone_number}
                        onChange={updateBookingField}
                        placeholder="e.g. 0300 1234567"
                        required
                      />
                    </div>
                  </label>
                </div>

                {savedAddresses.length > 0 && (
                  <div className="saved-addresses-row">
                    <span className="saved-addr-label">Saved Addresses:</span>
                    <div className="saved-addr-chips">
                      {savedAddresses.map((addr) => {
                        const full = [
                          addr.address_line_1 || addr.address_line || addr.address || addr.street_address,
                          addr.city,
                          addr.state || addr.state_or_province || addr.province,
                        ]
                          .filter(Boolean)
                          .join(", ");
                        return (
                          <button
                            key={addr.id}
                            type="button"
                            className={`address-quick-pill ${
                              bookingForm.location === full ? "active" : ""
                            }`}
                            onClick={() =>
                              setBookingForm((c) => ({ ...c, location: full }))
                            }
                          >
                            <MapPin size={13} />
                            <span>{addr.label || "Address"}: {addr.city}</span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}

                <label className="input-group">
                  <span>Service Location Address</span>
                  <div className="input-box">
                    <MapPin size={16} />
                    <input
                      type="text"
                      name="location"
                      value={bookingForm.location}
                      onChange={updateBookingField}
                      placeholder="House / Apartment #, Street, Sector, City"
                      required
                    />
                  </div>
                </label>

                <label className="input-group">
                  <span>Special Notes / Instructions (Optional)</span>
                  <textarea
                    name="customer_notes"
                    value={bookingForm.customer_notes}
                    onChange={updateBookingField}
                    placeholder="Any specific requests, materials needed, or entry directions..."
                    rows={2}
                    maxLength={1000}
                  />
                </label>
              </div>

              {/* Step 4: Summary Card & Submission */}
              <div className="booking-summary-bar">
                <div className="summary-breakdown">
                  <div className="breakdown-item">
                    <span>Date & Time:</span>
                    <strong>
                      {bookingForm.scheduled_date ? formatDateDisplay(bookingForm.scheduled_date) : "—"}
                      {bookingForm.scheduled_start ? ` at ${formatSlotTime(bookingForm.scheduled_start)}` : ""}
                    </strong>
                  </div>
                  <div className="breakdown-item">
                    <span>Estimated Total:</span>
                    <strong className="summary-total-price">
                      PKR {Number(selectedService.price || 0).toLocaleString()}
                    </strong>
                  </div>
                </div>

                <div className="modal-actions-row">
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
                    className="button button-primary confirm-booking-btn"
                    disabled={
                      submitting ||
                      !bookingForm.scheduled_date ||
                      !bookingForm.scheduled_start ||
                      !bookingForm.customer_name.trim() ||
                      !bookingForm.phone_number.trim() ||
                      !bookingForm.location.trim()
                    }
                  >
                    {submitting ? (
                      <>
                        <div className="loader-spinner small white" />
                        <span>Sending request...</span>
                      </>
                    ) : (
                      <>
                        <span>Confirm Booking</span>
                        <CheckCircle2 size={17} />
                      </>
                    )}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </section>
  );
}
