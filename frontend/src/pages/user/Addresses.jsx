import {
  useCallback,
  useEffect,
  useState,
} from "react";
import {
  Check,
  Edit3,
  MapPin,
  Plus,
  RefreshCw,
  Trash2,
  X,
} from "lucide-react";

import api from "../../api/api";

const emptyForm = {
  label: "Home",
  address_line_1: "",
  city: "",
  state: "",
  postal_code: "",
  country: "Pakistan",
  is_default: false,
};

function extractAddresses(response) {
  const data = response?.data?.data;

  if (Array.isArray(data)) {
    return data;
  }

  if (Array.isArray(data?.items)) {
    return data.items;
  }

  return [];
}

function getErrorMessage(error, fallback) {
  const data = error.response?.data;

  if (Array.isArray(data?.details) && data.details.length > 0) {
    return data.details
      .map((detail) => {
        const field = detail.field
          ? `${detail.field}: `
          : "";

        return `${field}${detail.message}`;
      })
      .join(" ");
  }

  return data?.message || data?.detail || fallback;
}

export default function Addresses() {
  const [addresses, setAddresses] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const loadAddresses = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const response = await api.get(
        "/users/me/addresses",
      );

      setAddresses(extractAddresses(response));
    } catch (requestError) {
      setError(
        getErrorMessage(
          requestError,
          "Unable to load your addresses.",
        ),
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAddresses();
  }, [loadAddresses]);

  const updateField = (event) => {
    const { name, value, type, checked } =
      event.target;

    setForm((current) => ({
      ...current,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const resetForm = () => {
    setForm(emptyForm);
    setEditingId(null);
    setShowForm(false);
    setError("");
  };

  const openCreateForm = () => {
    setForm(emptyForm);
    setEditingId(null);
    setShowForm(true);
    setError("");
    setSuccess("");
  };

  const openEditForm = (address) => {
    setForm({
      label: address.label || "Home",
      address_line_1:
        address.address_line_1 ||
        address.address_line ||
        address.address ||
        address.street_address ||
        "",
      city: address.city || "",
      state:
        address.state ||
        address.state_or_province ||
        address.province ||
        "",
      postal_code:
        address.postal_code ||
        address.zip_code ||
        "",
      country: address.country || "Pakistan",
      is_default: Boolean(address.is_default),
    });

    setEditingId(address.id);
    setShowForm(true);
    setError("");
    setSuccess("");
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    setSuccess("");

    const payload = {
      label: form.label.trim(),
      address_line_1: form.address_line_1.trim(),
      city: form.city.trim(),
      state: form.state.trim(),
      postal_code: form.postal_code.trim(),
      country: form.country.trim(),
      is_default: form.is_default,
    };

    try {
      if (editingId) {
        await api.patch(
          `/users/me/addresses/${editingId}`,
          payload,
        );

        setSuccess("Address updated successfully.");
      } else {
        await api.post(
          "/users/me/addresses",
          payload,
        );

        setSuccess("Address added successfully.");
      }

      setForm(emptyForm);
      setEditingId(null);
      setShowForm(false);

      await loadAddresses();
    } catch (requestError) {
      setError(
        getErrorMessage(
          requestError,
          editingId
            ? "Unable to update the address."
            : "Unable to add the address.",
        ),
      );
    } finally {
      setSubmitting(false);
    }
  };

  const deleteAddress = async (addressId) => {
    const confirmed = window.confirm(
      "Are you sure you want to delete this address?",
    );

    if (!confirmed) {
      return;
    }

    setDeletingId(addressId);
    setError("");
    setSuccess("");

    try {
      await api.delete(
        `/users/me/addresses/${addressId}`,
      );

      setSuccess("Address deleted successfully.");

      setAddresses((current) =>
        current.filter(
          (address) => address.id !== addressId,
        ),
      );

      if (editingId === addressId) {
        resetForm();
      }
    } catch (requestError) {
      setError(
        getErrorMessage(
          requestError,
          "Unable to delete the address.",
        ),
      );
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <main className="page-shell">
      <section className="page-section">
        <div className="page-heading-row">
          <div>
            <p className="eyebrow">Saved locations</p>

            <h1>Manage addresses</h1>

            <p className="page-description">
              Add and manage the locations used for your
              service bookings.
            </p>
          </div>

          <div className="page-actions">
            <button
              className="button button-secondary"
              type="button"
              onClick={loadAddresses}
              disabled={loading}
            >
              <RefreshCw
                size={18}
                className={loading ? "spin" : ""}
              />

              Refresh
            </button>

            <button
              className="button"
              type="button"
              onClick={openCreateForm}
            >
              <Plus size={18} />
              Add address
            </button>
          </div>
        </div>

        {error && (
          <div className="alert alert-error">
            {error}
          </div>
        )}

        {success && (
          <div className="alert alert-success">
            {success}
          </div>
        )}

        {showForm && (
          <section className="content-card address-form-card">
            <div className="card-heading-row">
              <div>
                <h2>
                  {editingId
                    ? "Edit address"
                    : "Add a new address"}
                </h2>

                <p>
                  Enter the complete location details below.
                </p>
              </div>

              <button
                className="icon-button"
                type="button"
                onClick={resetForm}
                aria-label="Close address form"
              >
                <X size={20} />
              </button>
            </div>

            <form
              className="address-form"
              onSubmit={handleSubmit}
            >
              <div className="form-grid">
                <label className="form-field">
                  <span>Address label</span>

                  <select
                    name="label"
                    value={form.label}
                    onChange={updateField}
                  >
                    <option value="Home">Home</option>
                    <option value="Work">Work</option>
                    <option value="Office">Office</option>
                    <option value="Other">Other</option>
                  </select>
                </label>

                <label className="form-field">
                  <span>Country</span>

                  <input
                    type="text"
                    name="country"
                    value={form.country}
                    onChange={updateField}
                    placeholder="Pakistan"
                    required
                  />
                </label>

                <label className="form-field form-field-full">
                  <span>Complete address</span>

                  <input
                    type="text"
                    name="address_line_1"
                    value={form.address_line_1}
                    onChange={updateField}
                    placeholder="House number, street and area"
                    required
                  />
                </label>

                <label className="form-field">
                  <span>City</span>

                  <input
                    type="text"
                    name="city"
                    value={form.city}
                    onChange={updateField}
                    placeholder="Faisalabad"
                    required
                  />
                </label>

                <label className="form-field">
                  <span>State or province</span>

                  <input
                    type="text"
                    name="state"
                    value={form.state}
                    onChange={updateField}
                    placeholder="Punjab"
                    required
                  />
                </label>

                <label className="form-field">
                  <span>Postal code</span>

                  <input
                    type="text"
                    name="postal_code"
                    value={form.postal_code}
                    onChange={updateField}
                    placeholder="38000"
                    required
                  />
                </label>

                <label className="checkbox-field">
                  <input
                    type="checkbox"
                    name="is_default"
                    checked={form.is_default}
                    onChange={updateField}
                  />

                  <span>Set as default address</span>
                </label>
              </div>

              <div className="form-actions">
                <button
                  className="button button-secondary"
                  type="button"
                  onClick={resetForm}
                >
                  <X size={18} />
                  Cancel
                </button>

                <button
                  className="button"
                  type="submit"
                  disabled={submitting}
                >
                  <Check size={18} />

                  {submitting
                    ? "Saving..."
                    : editingId
                      ? "Update address"
                      : "Save address"}
                </button>
              </div>
            </form>
          </section>
        )}

        {loading ? (
          <div className="content-card empty-state">
            <RefreshCw className="spin" size={28} />
            <p>Loading your addresses...</p>
          </div>
        ) : addresses.length === 0 ? (
          <div className="content-card empty-state">
            <MapPin size={36} />

            <h2>No saved addresses</h2>

            <p>
              Add an address to make booking services easier.
            </p>

            {!showForm && (
              <button
                className="button"
                type="button"
                onClick={openCreateForm}
              >
                <Plus size={18} />
                Add your first address
              </button>
            )}
          </div>
        ) : (
          <div className="address-grid">
            {addresses.map((address) => (
              <article
                className="content-card address-card"
                key={address.id}
              >
                <div className="address-card-icon">
                  <MapPin size={22} />
                </div>

                <div className="address-card-content">
                  <div className="address-card-title">
                    <h2>{address.label || "Address"}</h2>

                    {address.is_default && (
                      <span className="status-badge">
                        Default
                      </span>
                    )}
                  </div>

                  <p>
                    {address.address_line_1 ||
                      address.address_line ||
                      address.address ||
                      address.street_address}
                  </p>

                  <p>
                    {[
                      address.city,
                      address.state ||
                        address.state_or_province ||
                        address.province,
                      address.postal_code ||
                        address.zip_code,
                    ]
                      .filter(Boolean)
                      .join(", ")}
                  </p>

                  <p>{address.country}</p>
                </div>

                <div className="address-card-actions">
                  <button
                    className="icon-button"
                    type="button"
                    onClick={() => openEditForm(address)}
                    aria-label="Edit address"
                  >
                    <Edit3 size={18} />
                  </button>

                  <button
                    className="icon-button icon-button-danger"
                    type="button"
                    onClick={() =>
                      deleteAddress(address.id)
                    }
                    disabled={deletingId === address.id}
                    aria-label="Delete address"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}