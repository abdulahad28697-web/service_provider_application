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
  const [confirmDeleteId, setConfirmDeleteId] = useState(null);

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
    setConfirmDeleteId(null);
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
    <section className="addresses-page">
      <div className="page-container">
        <div className="addresses-header">
          <div className="addresses-header-content">
            <p className="eyebrow">Saved locations</p>

            <h1>Manage addresses</h1>

            <p>
              Add and manage the locations used for your
              service bookings.
            </p>
          </div>

          <div className="addresses-header-actions">
            <button
              className="button button-outline"
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
          <section className="address-card" style={{ marginBottom: 24 }}>
            <div className="address-card-header">
              <div className="address-card-title">
                <div className="address-icon">
                  <MapPin size={22} />
                </div>

                <h2>
                  {editingId
                    ? "Edit address"
                    : "Add a new address"}
                </h2>
              </div>

              <button
                className="address-action-button"
                type="button"
                onClick={resetForm}
                aria-label="Close address form"
              >
                <X size={20} />
              </button>
            </div>

            <form
              className="auth-form"
              onSubmit={handleSubmit}
              style={{ marginTop: 8 }}
            >
              <div
                className="form-grid"
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: 16,
                }}
              >
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

                <label
                  className="form-field"
                  style={{ gridColumn: "1 / -1" }}
                >
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

                <label
                  className="checkbox-field"
                  style={{
                    gridColumn: "1 / -1",
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                  }}
                >
                  <input
                    type="checkbox"
                    name="is_default"
                    checked={form.is_default}
                    onChange={updateField}
                  />

                  <span>Set as default address</span>
                </label>
              </div>

              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                  marginTop: 20,
                }}
              >
                <button
                  className="button button-outline"
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
          <div className="address-empty-state">
            <RefreshCw className="spin" size={28} />
            <p>Loading your addresses...</p>
          </div>
        ) : addresses.length === 0 ? (
          <div className="address-empty-state">
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
                className="address-card"
                key={address.id}
              >
                <div className="address-card-header">
                  <div className="address-card-title">
                    <div className="address-icon">
                      <MapPin size={22} />
                    </div>

                    <h2>{address.label || "Address"}</h2>
                  </div>

                  <div className="address-card-actions">
                    <button
                      className="address-action-button"
                      type="button"
                      onClick={() => openEditForm(address)}
                      aria-label="Edit address"
                    >
                      <Edit3 size={18} />
                    </button>

                    <button
                      className="address-action-button delete"
                      type="button"
                      onClick={() =>
                        setConfirmDeleteId(address.id)
                      }
                      disabled={deletingId === address.id}
                      aria-label="Delete address"
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                </div>

                {address.is_default && (
                  <span className="address-default-badge">
                    Default
                  </span>
                )}

                <div className="address-details">
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
              </article>
            ))}
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {confirmDeleteId !== null && (
        <div
          className="modal-overlay"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) {
              setConfirmDeleteId(null);
            }
          }}
        >
          <div className="modal-card" role="dialog" aria-modal="true">
            <div className="modal-heading">
              <span className="eyebrow">Confirm deletion</span>
              <h2>Delete this address?</h2>
              <p>This action cannot be undone.</p>
            </div>

            <div className="modal-actions">
              <button
                type="button"
                className="button button-outline"
                onClick={() => setConfirmDeleteId(null)}
              >
                Cancel
              </button>

              <button
                type="button"
                className="button button-danger"
                onClick={() => deleteAddress(confirmDeleteId)}
              >
                <Trash2 size={18} />
                Delete address
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}