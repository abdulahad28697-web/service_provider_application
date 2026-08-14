import { useCallback, useEffect, useState } from "react";
import {
  CheckCircle2,
  Clock3,
  DollarSign,
  Edit3,
  Plus,
  RefreshCw,
  Save,
  Trash2,
  Wrench,
  X,
} from "lucide-react";

import api from "../../api/api";

const emptyForm = {
  category_name: "",
  title: "",
  description: "",
  price: "",
  price_unit: "per_hour",
  duration_minutes: "60",
  is_active: true,
};

function getData(response) {
  return response?.data?.data ?? response?.data ?? {};
}

function getItems(response) {
  const data = getData(response);

  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.items)) return data.items;
  if (Array.isArray(data?.services)) return data.services;

  return [];
}

function ProviderServices() {
  const [services, setServices] = useState([]);
  const [form, setForm] = useState(emptyForm);

  const [editingId, setEditingId] = useState(null);
  const [showForm, setShowForm] = useState(false);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState(null);

  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  // ---------------------------------------------------------
  // LOAD ONLY CURRENT PROVIDER'S SERVICES
  // ---------------------------------------------------------

  const loadServices = useCallback(async () => {
    try {
      setLoading(true);
      setError("");

      // Get logged-in provider profile
      const profileResponse = await api.get("/providers/me");

      const provider = getData(profileResponse);

      if (!provider?.id) {
        throw new Error(
          "Unable to identify your provider profile.",
        );
      }

      /*
       * Request only services belonging to this provider.
       */
      const servicesResponse = await api.get("/services", {
        params: {
          provider_id: provider.id,
          page_size: 100,
        },
      });

      const allServices = getItems(servicesResponse);

      /*
       * Extra frontend protection:
       * Never display another provider's services here.
       */
      const ownServices = allServices.filter(
        (service) =>
          Number(service.provider_id) ===
          Number(provider.id),
      );

      setServices(ownServices);
    } catch (err) {
      setServices([]);

      setError(
        err.response?.data?.message ||
          err.response?.data?.detail ||
          err.message ||
          "Unable to load your services.",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadServices();
  }, [loadServices]);

  // ---------------------------------------------------------
  // FORM
  // ---------------------------------------------------------

  const handleChange = (event) => {
    const { name, value, type, checked } = event.target;

    setForm((current) => ({
      ...current,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const openCreateForm = () => {
    setEditingId(null);
    setForm(emptyForm);
    setError("");
    setMessage("");
    setShowForm(true);
  };

  const openEditForm = (service) => {
    setEditingId(service.id);

    setForm({
      category_name:
        service.category_name ||
        service.category?.name ||
        "",
      title: service.title || "",
      description: service.description || "",
      price: String(service.price ?? ""),
      price_unit:
        service.price_unit || "per_hour",
      duration_minutes: String(
        service.duration_minutes || 60,
      ),
      is_active: Boolean(service.is_active),
    });

    setError("");
    setMessage("");
    setShowForm(true);
  };

  const closeForm = () => {
    setEditingId(null);
    setForm(emptyForm);
    setShowForm(false);
  };

  // ---------------------------------------------------------
  // CREATE / UPDATE SERVICE
  // ---------------------------------------------------------

  const saveService = async (event) => {
    event.preventDefault();

    setError("");
    setMessage("");

    if (!form.category_name.trim()) {
      setError("Category is required.");
      return;
    }

    if (!form.title.trim()) {
      setError("Service title is required.");
      return;
    }

    if (
      form.price === "" ||
      Number(form.price) < 0
    ) {
      setError("Enter a valid service price.");
      return;
    }

    const payload = {
      category_name: form.category_name.trim(),
      title: form.title.trim(),
      description: form.description.trim(),
      price: Number(form.price),
      price_unit: form.price_unit,
      duration_minutes: Number(
        form.duration_minutes,
      ),
      is_active: form.is_active,
    };

    try {
      setSaving(true);

      if (editingId) {
        await api.patch(
          `/services/${editingId}`,
          payload,
        );

        setMessage(
          "Service updated successfully.",
        );
      } else {
        await api.post("/services", payload);

        setMessage(
          "Service created successfully.",
        );
      }

      closeForm();

      await loadServices();
    } catch (err) {
      setError(
        err.response?.data?.message ||
          err.response?.data?.detail ||
          "Unable to save this service.",
      );
    } finally {
      setSaving(false);
    }
  };

  // ---------------------------------------------------------
  // DELETE SERVICE
  // ---------------------------------------------------------

  const deleteService = async (serviceId) => {
    const confirmed = window.confirm(
      "Are you sure you want to delete this service?",
    );

    if (!confirmed) return;

    try {
      setDeletingId(serviceId);
      setError("");
      setMessage("");

      await api.delete(`/services/${serviceId}`);

      setServices((current) =>
        current.filter(
          (service) => service.id !== serviceId,
        ),
      );

      setMessage(
        "Service deleted successfully.",
      );
    } catch (err) {
      setError(
        err.response?.data?.message ||
          err.response?.data?.detail ||
          "Unable to delete this service.",
      );
    } finally {
      setDeletingId(null);
    }
  };

  // ---------------------------------------------------------
  // CATEGORY DISPLAY
  // ---------------------------------------------------------

  const getCategoryName = (service) => {
    return (
      service.category_name ||
      service.category?.name ||
      "Uncategorized"
    );
  };

  // ---------------------------------------------------------
  // UI
  // ---------------------------------------------------------

  return (
    <main className="page-section">
      <div className="container dashboard-container">

        {/* PAGE HEADER */}

        <div className="page-heading-row">
          <div>
            <span className="eyebrow">
              Provider workspace
            </span>

            <h1>Manage services</h1>

            <p>
              Create, update and manage the services
              offered to customers.
            </p>
          </div>

          <div className="heading-actions">
            <button
              type="button"
              className="button button-secondary"
              onClick={loadServices}
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

            <button
              type="button"
              className="button button-primary"
              onClick={openCreateForm}
            >
              <Plus size={18} />
              Add service
            </button>
          </div>
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

        {/* CREATE / EDIT FORM */}

        {showForm && (
          <section className="panel service-editor-panel">
            <div className="panel-heading">
              <div>
                <h2>
                  {editingId
                    ? "Update service"
                    : "Create a new service"}
                </h2>

                <p>
                  Add your own category, pricing and
                  service information.
                </p>
              </div>

              <button
                type="button"
                className="icon-button"
                onClick={closeForm}
                aria-label="Close service form"
              >
                <X size={20} />
              </button>
            </div>

            <form
              className="settings-form"
              onSubmit={saveService}
            >
              <div className="form-grid">

                {/* SERVICE TITLE */}

                <label className="form-field">
                  <span>Service title</span>

                  <input
                    type="text"
                    name="title"
                    className="text-input"
                    placeholder="Professional home cleaning"
                    value={form.title}
                    onChange={handleChange}
                    minLength={2}
                    maxLength={200}
                    required
                  />
                </label>

                {/* CATEGORY - TEXT INPUT */}

                <label className="form-field">
                  <span>Category</span>

                  <input
                    type="text"
                    name="category_name"
                    className="text-input"
                    placeholder="Home Cleaning, Plumbing, AC Repair..."
                    value={form.category_name}
                    onChange={handleChange}
                    minLength={2}
                    maxLength={120}
                    required
                  />
                </label>

                {/* DESCRIPTION */}

                <label className="form-field form-field-full">
                  <span>Description</span>

                  <textarea
                    name="description"
                    className="text-input textarea"
                    placeholder="Describe what is included in this service..."
                    value={form.description}
                    onChange={handleChange}
                    rows={5}
                    maxLength={2000}
                    required
                  />
                </label>

                {/* PRICE */}

                <label className="form-field">
                  <span>Price (PKR)</span>

                  <div className="input-with-icon">
                    <DollarSign size={18} />

                    <input
                      type="number"
                      name="price"
                      className="text-input"
                      placeholder="2500"
                      value={form.price}
                      onChange={handleChange}
                      min="0"
                      step="0.01"
                      required
                    />
                  </div>
                </label>

                {/* PRICE UNIT */}

                <label className="form-field">
                  <span>Price unit</span>

                  <select
                    name="price_unit"
                    className="text-input"
                    value={form.price_unit}
                    onChange={handleChange}
                    required
                  >
                    <option value="per_hour">
                      Per hour
                    </option>

                    <option value="per_visit">
                      Per visit
                    </option>

                    <option value="fixed">
                      Fixed price
                    </option>
                  </select>
                </label>

                {/* DURATION */}

                <label className="form-field">
                  <span>Duration in minutes</span>

                  <div className="input-with-icon">
                    <Clock3 size={18} />

                    <input
                      type="number"
                      name="duration_minutes"
                      className="text-input"
                      value={
                        form.duration_minutes
                      }
                      onChange={handleChange}
                      min="15"
                      max="1440"
                      step="15"
                      required
                    />
                  </div>
                </label>
              </div>

              {/* ACTIVE */}

              <label className="checkbox-field">
                <input
                  type="checkbox"
                  name="is_active"
                  checked={form.is_active}
                  onChange={handleChange}
                />

                <span>
                  Make this service visible to
                  customers
                </span>
              </label>

              {/* FORM BUTTONS */}

              <div className="form-actions">
                <button
                  type="button"
                  className="button button-secondary"
                  onClick={closeForm}
                  disabled={saving}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="button button-primary"
                  disabled={saving}
                >
                  {saving ? (
                    <RefreshCw
                      size={18}
                      className="spin"
                    />
                  ) : (
                    <Save size={18} />
                  )}

                  {saving
                    ? "Saving..."
                    : editingId
                      ? "Update service"
                      : "Save service"}
                </button>
              </div>
            </form>
          </section>
        )}

        {/* SERVICES */}

        {loading ? (
          <div className="state-card">
            <div className="spinner" />

            <p>Loading your services...</p>
          </div>
        ) : services.length === 0 ? (
          <div className="state-card">
            <Wrench size={48} />

            <h2>No services created</h2>

            <p>
              Create your first service so customers
              can find and book you.
            </p>

            <button
              type="button"
              className="button button-primary"
              onClick={openCreateForm}
            >
              <Plus size={18} />
              Create first service
            </button>
          </div>
        ) : (
          <div className="provider-services-grid">
            {services.map((service) => (
              <article
                className="panel provider-service-card"
                key={service.id}
              >
                <div className="provider-service-card-header">
                  <span className="provider-service-icon">
                    <Wrench size={21} />
                  </span>

                  <span
                    className={
                      service.is_active
                        ? "service-state active"
                        : "service-state inactive"
                    }
                  >
                    {service.is_active && (
                      <CheckCircle2 size={14} />
                    )}

                    {service.is_active
                      ? "Active"
                      : "Inactive"}
                  </span>
                </div>

                <span className="service-category-label">
                  {getCategoryName(service)}
                </span>

                <h2>{service.title}</h2>

                <p className="provider-service-description">
                  {service.description ||
                    "No description provided."}
                </p>

                <div className="provider-service-meta">
                  <span>
                    <DollarSign size={17} />

                    PKR{" "}
                    {Number(
                      service.price || 0,
                    ).toLocaleString()}

                    {" · "}

                    {String(
                      service.price_unit || "",
                    ).replaceAll("_", " ")}
                  </span>

                  <span>
                    <Clock3 size={17} />

                    {service.duration_minutes || 60}{" "}
                    minutes
                  </span>
                </div>

                <div className="provider-service-actions">
                  <button
                    type="button"
                    className="button button-secondary"
                    onClick={() =>
                      openEditForm(service)
                    }
                  >
                    <Edit3 size={17} />
                    Edit
                  </button>

                  <button
                    type="button"
                    className="danger-button"
                    onClick={() =>
                      deleteService(service.id)
                    }
                    disabled={
                      deletingId === service.id
                    }
                  >
                    <Trash2 size={17} />

                    {deletingId === service.id
                      ? "Deleting..."
                      : "Delete"}
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}

export default ProviderServices;