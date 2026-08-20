import { useEffect, useState } from "react";
import {
  Camera,
  KeyRound,
  Save,
  Trash2,
  User,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import api from "../../api/api";
import { useAuth } from "../../context/AuthContext";

export default function Profile() {
  const navigate = useNavigate();
  const {
    user,
    logout,
  } = useAuth();

  const [profile, setProfile] = useState({
    full_name: "",
    phone_number: "",
    bio: "",
    profile_picture_url: "",
  });

  const [initialProfile, setInitialProfile] = useState({
    full_name: "",
    phone_number: "",
    bio: "",
    profile_picture_url: "",
  });

  const [passwords, setPasswords] = useState({
    current_password: "",
    new_password: "",
  });

  const [deletePassword, setDeletePassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    if (!user) {
      return;
    }

    const nextProfile = {
      full_name: user.full_name || "",
      phone_number:
        user.phone_number ||
        user.phone ||
        "",
      bio: user.bio || "",
      profile_picture_url:
        user.profile_picture_url || "",
    };

    setProfile(nextProfile);
    setInitialProfile(nextProfile);
  }, [user]);

  const showResult = (successMessage) => {
    setError("");
    setMessage(successMessage);
  };

  const showError = (requestError, fallback) => {
    setMessage("");
    setError(
      requestError.response?.data?.message ||
        requestError.response?.data?.detail ||
        fallback,
    );
  };

  const handleProfileSubmit = async (event) => {
  event.preventDefault();

  const payload = {};

  const fullName = profile.full_name.trim();
  const phoneNumber =
    profile.phone_number.trim();
  const bio = profile.bio.trim();

  if (
    fullName !==
    initialProfile.full_name.trim()
  ) {
    payload.full_name = fullName;
  }

  if (
    phoneNumber !==
    initialProfile.phone_number.trim()
  ) {
    payload.phone_number = phoneNumber;
  }

  if (
    bio !==
    initialProfile.bio.trim()
  ) {
    payload.bio = bio;
  }

  if (Object.keys(payload).length === 0) {
    setError("");
    setMessage(
      "No changes to save.",
    );
    return;
  }

  if (!fullName) {
    setMessage("");
    setError(
      "Full name is required.",
    );
    return;
  }

  try {
    setSaving(true);
    setError("");
    setMessage("");

    const response = await api.patch(
      "/users/me",
      payload,
    );

    const updated =
      response?.data?.data ??
      response?.data ??
      {};

    const nextProfile = {
      full_name:
        updated.full_name ??
        fullName,

      phone_number:
        updated.phone_number ??
        phoneNumber,

      bio:
        updated.bio ??
        bio,

      profile_picture_url:
        updated.profile_picture_url ??
        profile.profile_picture_url,
    };

    setProfile(nextProfile);
    setInitialProfile(nextProfile);

    setMessage(
      "Profile updated successfully.",
    );
  } catch (requestError) {
    setMessage("");

    setError(
      requestError.response?.data?.message ||
        requestError.response?.data?.detail ||
        "Unable to update profile.",
    );
  } finally {
    setSaving(false);
  }
};

  const handlePictureUpload = async (event) => {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    setUploading(true);

    try {
      const response = await api.post(
        "/uploads/profile-picture",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        },
      );

      const imageUrl = response.data.data.image_url;

      await api.patch("/users/me", {
        profile_picture_url: imageUrl,
      });

      setProfile((current) => {
        const next = {
          ...current,
          profile_picture_url: imageUrl,
        };

        setInitialProfile(next);

        return next;
      });

      showResult("Profile picture updated.");
    } catch (requestError) {
      showError(
        requestError,
        "Unable to upload profile picture.",
      );
    } finally {
      setUploading(false);
      event.target.value = "";
    }
  };

  const handlePasswordChange = async (event) => {
    event.preventDefault();

    try {
      await api.post("/auth/change-password", passwords);

      setPasswords({
        current_password: "",
        new_password: "",
      });

      showResult("Password changed successfully.");
    } catch (requestError) {
      showError(
        requestError,
        "Unable to change your password.",
      );
    }
  };

  const handleDeleteAccount = async () => {
    if (
      !window.confirm(
        "Deactivate your account? You will be signed out.",
      )
    ) {
      return;
    }

    try {
      await api.delete("/users/me", {
        data: {
          password: deletePassword,
        },
      });

      logout();
      navigate("/");
    } catch (requestError) {
      showError(
        requestError,
        "Unable to deactivate your account.",
      );
    }
  };

  const imageSource =
    profile.profile_picture_url
      ? profile.profile_picture_url.startsWith(
          "http",
        )
        ? profile.profile_picture_url
        : `https://service-provider-backend-yea9.onrender.com${profile.profile_picture_url}`
      : null;

  return (
    <section className="section page-section">
      <div className="container dashboard-container">
        <div className="page-heading">
          <div>
            <span className="eyebrow">Your account</span>
            <h1>Profile settings</h1>
            <p>
              Manage your personal information and account
              security.
            </p>
          </div>
        </div>

        {message && (
          <div className="alert alert-success">{message}</div>
        )}

        {error && (
          <div className="alert alert-error">{error}</div>
        )}

        <div className="settings-grid">
          <aside className="profile-summary panel">
            <div className="profile-avatar">
              {imageSource ? (
                <img
                  src={imageSource}
                  alt={profile.full_name}
                />
              ) : (
                <User size={42} />
              )}

              <label className="avatar-upload">
                <Camera size={17} />
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  onChange={handlePictureUpload}
                  disabled={uploading}
                />
              </label>
            </div>

            <h2>{user?.full_name}</h2>
            <p>{user?.email}</p>
            <span className="role-badge">
              {user?.role}
            </span>

            {uploading && <small>Uploading image...</small>}
          </aside>

          <div className="settings-content">
            <form
              className="panel settings-form"
              onSubmit={handleProfileSubmit}
            >
              <div className="panel-heading">
                <User size={21} />
                <div>
                  <h2>Personal information</h2>
                  <p>Update your public account details.</p>
                </div>
              </div>

              <label className="form-field">
                <span>Full name</span>
                <input
                  className="text-input"
                  value={profile.full_name}
                  onChange={(event) =>
                    setProfile((current) => ({
                      ...current,
                      full_name: event.target.value,
                    }))
                  }
                  required
                />
              </label>

              <label className="form-field">
                <span>Phone number</span>
                <input
                  className="text-input"
                  value={profile.phone_number}
                  onChange={(event) =>
                    setProfile((current) => ({
                      ...current,
                      phone_number: event.target.value,
                    }))
                  }
                  placeholder="+92 300 0000000"
                />
              </label>

              <label className="form-field">
                <span>About you</span>
                <textarea
                  className="text-input textarea"
                  value={profile.bio}
                  onChange={(event) =>
                    setProfile((current) => ({
                      ...current,
                      bio: event.target.value,
                    }))
                  }
                  placeholder="Tell providers about your requirements..."
                  maxLength={1000}
                />
              </label>

              <button
                type="submit"
                className="button"
                disabled={
                  saving ||
                  (
                    profile.full_name.trim() ===
                      initialProfile.full_name.trim() &&
                    profile.phone_number.trim() ===
                      initialProfile.phone_number.trim() &&
                    profile.bio.trim() ===
                      initialProfile.bio.trim()
                  )
                }
              >
                <Save size={17} />
                {saving ? "Saving..." : "Save changes"}
              </button>
            </form>

            <form
              className="panel settings-form"
              onSubmit={handlePasswordChange}
            >
              <div className="panel-heading">
                <KeyRound size={21} />
                <div>
                  <h2>Change password</h2>
                  <p>Use a secure, unique password.</p>
                </div>
              </div>

              <label className="form-field">
                <span>Current password</span>
                <input
                  className="text-input"
                  type="password"
                  value={passwords.current_password}
                  onChange={(event) =>
                    setPasswords((current) => ({
                      ...current,
                      current_password: event.target.value,
                    }))
                  }
                  required
                />
              </label>

              <label className="form-field">
                <span>New password</span>
                <input
                  className="text-input"
                  type="password"
                  value={passwords.new_password}
                  onChange={(event) =>
                    setPasswords((current) => ({
                      ...current,
                      new_password: event.target.value,
                    }))
                  }
                  required
                />
              </label>

              <button type="submit" className="button">
                <KeyRound size={17} />
                Change password
              </button>
            </form>

            <div className="panel danger-panel">
              <div>
                <h2>Deactivate account</h2>
                <p>
                  Your booking history will be retained, but
                  you will no longer be able to sign in.
                </p>
              </div>

              <input
                className="text-input"
                type="password"
                value={deletePassword}
                onChange={(event) =>
                  setDeletePassword(event.target.value)
                }
                placeholder="Confirm your password"
              />

              <button
                type="button"
                className="danger-button"
                onClick={handleDeleteAccount}
                disabled={!deletePassword}
              >
                <Trash2 size={17} />
                Deactivate account
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
