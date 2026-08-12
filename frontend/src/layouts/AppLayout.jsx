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
  Search,
  User,
  UserPlus,
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
      return undefined;
    }

    loadNotifications();

    /*
     * Refresh occasionally so new booking updates
     * appear without requiring a full page refresh.
     */
    const intervalId = window.setInterval(
      loadNotifications,
      30000,
    );

    return () => {
      window.clearInterval(intervalId);
    };
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

        /*
         * All notifications currently created by the
         * booking system point to a booking.
         */
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
    const willOpen =
      !notificationOpen;

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
      return undefined;
    }

    loadUnreadMessages();

    const intervalId = window.setInterval(
      loadUnreadMessages,
      15000,
    );

    return () => {
      window.clearInterval(intervalId);
    };
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
                size={23}
              />
            </span>

            <span>
              Service<span>Hub</span>
            </span>
          </Link>


          {/* MOBILE MENU */}

          <button
            type="button"
            className="mobile-menu-button"
            onClick={() =>
              setMenuOpen(
                (current) => !current,
              )
            }
            aria-label="Open navigation menu"
            aria-expanded={menuOpen}
          >
            {menuOpen ? (
              <X size={24} />
            ) : (
              <Menu size={24} />
            )}
          </button>


          {/* =================================================
              NAVIGATION
          ================================================== */}

          <nav
            className={`main-nav ${
              menuOpen
                ? "main-nav-open"
                : ""
            }`}
          >
            <NavLink
              to="/"
              end
              className={getNavClass}
              onClick={closeMenu}
            >
              <Home size={17} />
              Home
            </NavLink>


            <NavLink
              to="/services"
              className={getNavClass}
              onClick={closeMenu}
            >
              <Search size={17} />
              Services
            </NavLink>


            {user && (
              <>
                {/* CUSTOMER BOOKING HISTORY */}

                {!isProvider && (
                  <NavLink
                    to="/bookings"
                    className={
                      getNavClass
                    }
                    onClick={closeMenu}
                  >
                    <CalendarDays
                      size={17}
                    />
                    Bookings
                  </NavLink>
                )}


                {/* PROVIDER BOOKINGS */}

                {isProvider && (
                  <>
                    <NavLink
                      to="/provider/bookings"
                      className={
                        getNavClass
                      }
                      onClick={closeMenu}
                    >
                      <CalendarDays
                        size={17}
                      />
                      Bookings
                    </NavLink>

                    <NavLink
                      to="/provider/earnings"
                      className={
                        getNavClass
                      }
                      onClick={closeMenu}
                    >
                      <WalletCards
                        size={17}
                      />
                      Earnings
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


                <NavLink
                  to="/ai-assistant"
                  className={getNavClass}
                  onClick={closeMenu}
                >
                  <Bot size={17} />
                  AI Assistant
                </NavLink>


                <NavLink
                  to="/profile"
                  className={getNavClass}
                  onClick={closeMenu}
                >
                  <User size={17} />
                  Profile
                </NavLink>


                {/* CUSTOMER-ONLY ITEMS */}

                {isCustomer && (
                  <>
                    <NavLink
                      to="/favorites"
                      className={
                        getNavClass
                      }
                      onClick={closeMenu}
                    >
                      <Heart size={18} />
                      Favorites
                    </NavLink>

                    <NavLink
                      to="/addresses"
                      className={
                        getNavClass
                      }
                      onClick={closeMenu}
                    >
                      <MapPin size={18} />
                      Addresses
                    </NavLink>
                  </>
                )}


                {/* PROVIDER DASHBOARD */}

                {isProvider && (
                  <NavLink
                    to="/provider"
                    className={
                      getNavClass
                    }
                    onClick={closeMenu}
                  >
                    <BriefcaseBusiness
                      size={17}
                    />
                    Provider
                  </NavLink>
                )}


                {/* =============================================
                    NOTIFICATION BELL
                ============================================== */}

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
                    <Bell size={20} />

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

              </>
            )}


            {/* =================================================
                AUTH ACTIONS
            ================================================== */}

            <div className="nav-auth-actions">
              {user ? (
                <button
                  type="button"
                  className="button button-secondary nav-logout-button"
                  onClick={handleLogout}
                >
                  <LogOut size={17} />
                  Logout
                </button>
              ) : (
                <>
                  <Link
                    to="/login"
                    className="button button-secondary"
                    onClick={closeMenu}
                  >
                    <LogIn size={17} />
                    Sign in
                  </Link>

                  <Link
                    to="/register"
                    className="button button-primary"
                    onClick={closeMenu}
                  >
                    <UserPlus
                      size={17}
                    />
                    Register
                  </Link>
                </>
              )}
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
            Service provider and booking
            platform
          </p>
        </div>
      </footer>
    </div>
  );
}


export default AppLayout;