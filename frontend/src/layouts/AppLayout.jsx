import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  Link,
  NavLink,
  Outlet,
  useNavigate,
} from "react-router-dom";

import {
  Bell,
  Bot,
  BriefcaseBusiness,
  CalendarDays,
  CheckCheck,
  Heart,
  Home,
  LogIn,
  LogOut,
  MapPin,
  Menu,
  MessageCircle,
  MessageSquareText,
  Search,
  ShieldCheck,
  User,
  UserPlus,
  Users,
  WalletCards,
  X,
} from "lucide-react";

import { useAuth } from "../context/AuthContext";
import api from "../api/api";


function extractNotifications(response) {
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


function formatNotificationTime(value) {
  if (!value) {
    return "";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return date.toLocaleString("en-PK", {
    day: "numeric",
    month: "short",
    hour: "numeric",
    minute: "2-digit",
  });
}


function AppLayout() {
  const [menuOpen, setMenuOpen] =
    useState(false);

  const [
    notificationOpen,
    setNotificationOpen,
  ] = useState(false);

  const [
    notifications,
    setNotifications,
  ] = useState([]);

  const [
    notificationsLoading,
    setNotificationsLoading,
  ] = useState(false);

  const [
    notificationError,
    setNotificationError,
  ] = useState("");

  const [
    unreadMessages,
    setUnreadMessages,
  ] = useState(0);

  const { user, logout } = useAuth();

  const navigate = useNavigate();


  // =========================================================
  // USER ROLE
  // =========================================================

  const userRole =
    typeof user?.role === "string"
      ? user.role.toLowerCase()
      : user?.role?.value?.toLowerCase();

  const isProvider =
    userRole === "provider";

  const isCustomer =
    userRole === "customer";

  const isAdmin =
    userRole === "admin";


  // =========================================================
  // NAVIGATION
  // =========================================================

  const closeMenu = () => {
    setMenuOpen(false);
  };


  const handleLogout = () => {
    logout();

    closeMenu();
    setNotificationOpen(false);
    setNotifications([]);
    setUnreadMessages(0);

    navigate("/login");
  };


  const getNavClass = ({
    isActive,
  }) =>
    isActive
      ? "nav-link nav-link-active"
      : "nav-link";


  // =========================================================
  // NOTIFICATIONS
  // =========================================================

  const loadNotifications =
    useCallback(async () => {
      if (!user) {
        setNotifications([]);
        return;
      }

      try {
        setNotificationsLoading(true);
        setNotificationError("");

        const response = await api.get(
          "/notifications",
        );

        setNotifications(
          extractNotifications(response),
        );
      } catch (requestError) {
        setNotificationError(
          requestError.response?.data?.message ||
            requestError.response?.data?.detail ||
            "Unable to load notifications.",
        );
      } finally {
        setNotificationsLoading(false);
      }
    }, [user]);

  useEffect(() => {

    if (!user) {
      setNotifications([]);
      return;
    }
    loadNotifications();
  }, [user, loadNotifications]);

  const unreadCount = useMemo(
    () =>
      notifications.filter(
        (notification) =>
          !notification.is_read,
      ).length,
    [notifications],
  );

  const markNotificationRead =
    async (notification) => {
      try {
        if (!notification.is_read) {
          const response = await api.patch(
            `/notifications/${notification.id}/read`,
          );

          const updated =
            response?.data?.data ??
            response?.data;

          setNotifications((current) =>
            current.map((item) =>
              item.id === notification.id
                ? {
                    ...item,
                    ...updated,
                    is_read: true,
                  }
                : item,
            ),
          );
        }

        setNotificationOpen(false);
        closeMenu();

        if (
          String(
            notification.notification_type ||
              "",
          ).startsWith("booking_")
        ) {
          if (isProvider) {
            navigate(
              "/provider/bookings",
            );
          } else {
            navigate("/bookings");
          }
          return;
        }
      } catch (requestError) {
        setNotificationError(
          requestError.response?.data?.message ||
            requestError.response?.data?.detail ||
            "Unable to open notification.",
        );
      }
    };

  const markAllRead = async () => {
    if (unreadCount === 0) {
      return;
    }

    try {
      setNotificationError("");

      await api.patch(
        "/notifications/read-all",
      );

      setNotifications((current) =>
        current.map((notification) => ({
          ...notification,
          is_read: true,
        })),
      );
    } catch (requestError) {
      setNotificationError(
        requestError.response?.data?.message ||
          requestError.response?.data?.detail ||
          "Unable to mark notifications as read.",
      );
    }
  };

  const toggleNotifications = async () => {
    const willOpen = !notificationOpen;
    setNotificationOpen(willOpen);

    if (willOpen) {
      await loadNotifications();
    }
  };

  // =========================================================
  // MESSAGE UNREAD COUNT
  // =========================================================

  const loadUnreadMessages =
    useCallback(async () => {
      if (!user) {
        setUnreadMessages(0);
        return;
      }

      try {
        const response = await api.get(
          "/messages/unread-count",
        );

        const data =
          response?.data?.data ??
          response?.data ??
          {};

        setUnreadMessages(
          Number(data?.unread_count || 0),
        );
      } catch {
        setUnreadMessages(0);
      }
    }, [user]);

  useEffect(() => {
    if (!user) {
      setUnreadMessages(0);
      return;
    }

    loadUnreadMessages();
  }, [user, loadUnreadMessages]);


  const handleMessagesClick = () => {
    closeMenu();
    setNotificationOpen(false);
    navigate("/messages");
  };


  // =========================================================
  // UI
  // =========================================================

  return (
    <div className="app-shell">

      {/* =====================================================
          HEADER
      ====================================================== */}

      <header className="site-header">
        <div className="container header-container">

          {/* BRAND */}
          <Link
            to="/"
            className="brand"
            onClick={closeMenu}
          >
            <span className="brand-icon">
              <BriefcaseBusiness
                size={22}
              />
            </span>

            <span className="brand-title">
              Service<span>Hub</span>
            </span>
          </Link>

          {/* MOBILE MENU BUTTON */}
          <button
            type="button"
            className="mobile-menu-button"
            onClick={() =>
              setMenuOpen(
                (current) => !current,
              )
            }
            aria-label="Toggle navigation menu"
            aria-expanded={menuOpen}
          >
            {menuOpen ? (
              <X size={24} />
            ) : (
              <Menu size={24} />
            )}
          </button>

          {/* NAVIGATION */}
          <nav
            className={`main-nav ${
              menuOpen
                ? "main-nav-open"
                : ""
            }`}
          >
            <div className="nav-links-group">
              <NavLink
                to="/"
                end
                className={getNavClass}
                onClick={closeMenu}
              >
                <Home size={16} />
                Home
              </NavLink>

              <NavLink
                to="/services"
                className={getNavClass}
                onClick={closeMenu}
              >
                <Search size={16} />
                Services
              </NavLink>


            {user && (
              <>
                {/* ADMIN NAVIGATION */}
                {isAdmin && (
                  <>
                    <NavLink
                      to="/admin"
                      end
                      className={getNavClass}
                      onClick={closeMenu}
                    >
                      <ShieldCheck size={17} />
                      Dashboard
                    </NavLink>

                    <NavLink
                      to="/admin/providers"
                      className={getNavClass}
                      onClick={closeMenu}
                    >
                      <Users size={17} />
                      Applications
                    </NavLink>

                    <NavLink
                      to="/admin/bookings"
                      className={getNavClass}
                      onClick={closeMenu}
                    >
                      <CalendarDays size={17} />
                      Bookings
                    </NavLink>

                    <NavLink
                      to="/admin/payments"
                      className={getNavClass}
                      onClick={closeMenu}
                    >
                      <WalletCards size={17} />
                      Payments
                    </NavLink>

                    <NavLink
                      to="/admin/reviews"
                      className={getNavClass}
                      onClick={closeMenu}
                    >
                      <MessageSquareText size={17} />
                      Reviews
                    </NavLink>
                  </>
                )}


                {/* CUSTOMER NAVIGATION */}
                {isCustomer && (
                  <>
                    <NavLink
                      to="/bookings"
                      className={getNavClass}
                      onClick={closeMenu}
                    >
                      <CalendarDays size={17} />
                      Bookings
                    </NavLink>

                    <NavLink
                      to="/favorites"
                      className={getNavClass}
                      onClick={closeMenu}
                    >
                      <Heart size={17} />
                      Favorites
                    </NavLink>

                    <NavLink
                      to="/addresses"
                      className={getNavClass}
                      onClick={closeMenu}
                    >
                      <MapPin size={17} />
                      Addresses
                    </NavLink>

                    <NavLink
                      to="/become-provider"
                      className={getNavClass}
                      onClick={closeMenu}
                    >
                      <BriefcaseBusiness size={17} />
                      Become Provider
                    </NavLink>
                  </>
                )}

                {/* PROVIDER NAVIGATION */}
                {isProvider && (
                  <>
                    <NavLink
                      to="/provider/bookings"
                      className={getNavClass}
                      onClick={closeMenu}
                    >
                      <CalendarDays size={17} />
                      Bookings
                    </NavLink>

                    <NavLink
                      to="/provider/earnings"
                      className={getNavClass}
                      onClick={closeMenu}
                    >
                      <WalletCards size={17} />
                      Earnings
                    </NavLink>

                    <NavLink
                      to="/provider"
                      className={getNavClass}
                      onClick={closeMenu}
                    >
                      <BriefcaseBusiness size={17} />
                      Provider Portal
                    </NavLink>
                  </>
                )}

                {/* MESSAGES */}
                <button
                  type="button"
                  className="nav-link nav-messages-link"
                  onClick={handleMessagesClick}
                >
                  <MessageCircle size={17} />
                  <span>Messages</span>

                  {unreadMessages > 0 && (
                    <span className="nav-message-count">
                      {unreadMessages > 99
                        ? "99+"
                        : unreadMessages}
                    </span>
                  )}
                </button>

                {/* AI ASSISTANT */}
                <NavLink
                  to="/ai-assistant"
                  className={getNavClass}
                  onClick={closeMenu}
                >
                  <Bot size={17} />
                  AI Assistant
                </NavLink>

                {/* PROFILE */}
                <NavLink
                  to="/profile"
                  className={getNavClass}
                  onClick={closeMenu}
                >
                  <User size={17} />
                  Profile
                </NavLink>
              </>
            )}
          </div>

            {/* =================================================
                ACTIONS GROUP (Notifications + Auth / Logout)
            ================================================== */}
            <div className="nav-actions-group">
              {user && (
                <div className="notification-menu">
                  <button
                    type="button"
                    className={`notification-bell ${
                      notificationOpen
                        ? "active"
                        : ""
                    }`}
                    onClick={
                      toggleNotifications
                    }
                    aria-label="Notifications"
                    aria-expanded={
                      notificationOpen
                    }
                  >
                    <Bell size={19} />

                    {unreadCount > 0 && (
                      <span className="notification-count">
                        {unreadCount > 99
                          ? "99+"
                          : unreadCount}
                      </span>
                    )}
                  </button>

                  {/* NOTIFICATION DROPDOWN */}
                  {notificationOpen && (
                    <div className="notification-dropdown">
                      <div className="notification-dropdown-header">
                        <div>
                          <strong>
                            Notifications
                          </strong>

                          <span>
                            {unreadCount} unread
                          </span>
                        </div>

                        {unreadCount >
                          0 && (
                          <button
                            type="button"
                            onClick={
                              markAllRead
                            }
                          >
                            <CheckCheck
                              size={16}
                            />

                            Mark all read
                          </button>
                        )}
                      </div>

                      {notificationError && (
                        <div className="notification-error">
                          {
                            notificationError
                          }
                        </div>
                      )}

                      <div className="notification-list">
                        {notificationsLoading &&
                        notifications.length ===
                          0 ? (
                          <div className="notification-empty">
                            Loading
                            notifications...
                          </div>
                        ) : notifications.length ===
                          0 ? (
                          <div className="notification-empty">
                            <Bell
                              size={30}
                            />

                            <strong>
                              No notifications
                            </strong>

                            <span>
                              Booking updates
                              will appear here.
                            </span>
                          </div>
                        ) : (
                          notifications
                            .slice(0, 15)
                            .map(
                              (
                                notification,
                              ) => (
                                <button
                                  key={
                                    notification.id
                                  }
                                  type="button"
                                  className={`notification-item ${
                                    !notification.is_read
                                      ? "unread"
                                      : ""
                                  }`}
                                  onClick={() =>
                                    markNotificationRead(
                                      notification,
                                    )
                                  }
                                >
                                  <span className="notification-item-icon">
                                    <CalendarDays
                                      size={
                                        18
                                      }
                                    />
                                  </span>

                                  <span className="notification-item-content">
                                    <strong>
                                      {
                                        notification.title
                                      }
                                    </strong>

                                    <span>
                                      {
                                        notification.message
                                      }
                                    </span>

                                    <small>
                                      {formatNotificationTime(
                                        notification.created_at,
                                      )}
                                    </small>
                                  </span>

                                  {!notification.is_read && (
                                    <span className="notification-unread-dot" />
                                  )}
                                </button>
                              ),
                            )
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* AUTH ACTIONS */}
              <div className="nav-auth-actions">
                {user ? (
                  <button
                    type="button"
                    className="button button-danger-outline nav-logout-button"
                    onClick={handleLogout}
                  >
                    <LogOut size={16} />
                    <span>Logout</span>
                  </button>
                ) : (
                  <>
                    <Link
                      to="/login"
                      className="button button-secondary"
                      onClick={closeMenu}
                    >
                      <LogIn size={16} />
                      <span>Sign in</span>
                    </Link>

                    <Link
                      to="/register"
                      className="button button-primary"
                      onClick={closeMenu}
                    >
                      <UserPlus
                        size={16}
                      />
                      <span>Register</span>
                    </Link>

                    <Link
                      to="/admin/login"
                      className="button button-admin-portal"
                      onClick={closeMenu}
                      title="Sign in as platform administrator"
                    >
                      <ShieldCheck size={15} />
                      <span>Admin</span>
                    </Link>
                  </>
                )}
              </div>
            </div>
          </nav>
        </div>
      </header>


      {/* =====================================================
          PAGE CONTENT
      ====================================================== */}

      <div className="app-content">
        <Outlet />
      </div>


      {/* =====================================================
          FOOTER
      ====================================================== */}

      <footer className="site-footer">
        <div className="container footer-grid">

          <div className="footer-about">
            <Link
              to="/"
              className="brand footer-brand"
            >
              <span className="brand-icon">
                <BriefcaseBusiness
                  size={22}
                />
              </span>

              <span>
                Service<span>Hub</span>
              </span>
            </Link>

            <p>
              Find trusted local
              professionals, compare
              services and book the right
              provider with confidence.
            </p>
          </div>


          <div className="footer-links">
            <h3>Platform</h3>

            <Link to="/">
              Home
            </Link>

            <Link to="/services">
              Browse services
            </Link>

            {user &&
              (isProvider ? (
                <Link to="/provider/bookings">
                  Provider bookings
                </Link>
              ) : (
                <Link to="/bookings">
                  My bookings
                </Link>
              ))}
          </div>


          <div className="footer-links">
            <h3>Account</h3>

            {user ? (
              <>
                <Link to="/profile">
                  My profile
                </Link>

                {isCustomer && (
                  <>
                    <Link to="/addresses">
                      My addresses
                    </Link>

                    <Link to="/favorites">
                      Favorites
                    </Link>
                  </>
                )}

                <Link to="/messages">
                  Messages
                </Link>

                <Link to="/ai-assistant">
                  AI assistant
                </Link>
              </>
            ) : (
              <>
                <Link to="/login">
                  Sign in
                </Link>

                <Link to="/register">
                  Create account
                </Link>

                <Link to="/forgot-password">
                  Reset password
                </Link>
              </>
            )}
          </div>


          <div className="footer-links">
            <h3>For providers</h3>

            {user ? (
              isProvider ? (
                <>
                  <Link to="/provider">
                    Provider dashboard
                  </Link>

                  <Link to="/provider/bookings">
                    Manage bookings
                  </Link>

                  <Link to="/provider/availability">
                    Availability
                  </Link>

                  <Link to="/provider/earnings">
                    Earnings & revenue
                  </Link>
                </>
              ) : (
                <Link to="/become-provider">
                  Become a provider
                </Link>
              )
            ) : (
              <Link to="/register">
                Join ServiceHub
              </Link>
            )}
          </div>
        </div>


        <div className="container footer-bottom">
          <p>
            © {new Date().getFullYear()}{" "}
            ServiceHub. All rights
            reserved.
          </p>

          <p>
            <Link to="/admin/login" style={{ textDecoration: 'underline' }}>
              Admin Portal
            </Link>
          </p>
        </div>

      </footer>
    </div>
  );
}


export default AppLayout;