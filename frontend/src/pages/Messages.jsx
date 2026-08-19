import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  ArrowLeft,
  CheckCheck,
  MessageCircle,
  RefreshCw,
  Send,
  UserRound,
  CalendarDays,
  Clock,
  Sparkles,
} from "lucide-react";
import {
  useLocation,
  useNavigate,
  useSearchParams,
} from "react-router-dom";

import api from "../api/api";

function extractArray(response) {
  const data = response?.data?.data ?? response?.data ?? [];
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.items)) return data.items;
  return [];
}

function formatTime(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
}

function formatMessageDate(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

export default function Messages() {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();

  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [messageText, setMessageText] = useState("");
  const [loadingInbox, setLoadingInbox] = useState(true);
  const [loadingConversation, setLoadingConversation] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  let currentUser = null;
  try {
    currentUser = JSON.parse(localStorage.getItem("current_user") || "null");
  } catch {
    currentUser = null;
  }

  const bookingIdFromQuery = Number(searchParams.get("booking") || 0);
  const navigationBooking = location.state || {};
  const directBookingId = Number(
    navigationBooking.bookingId || bookingIdFromQuery || 0
  );

  // Load Inbox
  const loadInbox = useCallback(async (silent = false) => {
    try {
      if (!silent) setLoadingInbox(true);
      setError("");
      const response = await api.get("/messages");
      const items = extractArray(response);
      setConversations(items);
      return items;
    } catch (requestError) {
      if (!silent) {
        setError(
          requestError.response?.data?.message ||
            requestError.response?.data?.detail ||
            "Unable to load conversations."
        );
      }
      return [];
    } finally {
      if (!silent) setLoadingInbox(false);
    }
  }, []);

  // Load Conversation
  const loadConversation = useCallback(async (bookingId, silent = false) => {
    if (!bookingId) return;

    try {
      if (!silent) setLoadingConversation(true);
      const response = await api.get(`/messages/${bookingId}`);
      const list = extractArray(response);
      setMessages(list);

      setConversations((current) =>
        current.map((c) =>
          c.booking_id === bookingId ? { ...c, unread_count: 0 } : c
        )
      );
    } catch (requestError) {
      if (!silent) {
        setMessages([]);
        setError(
          requestError.response?.data?.message ||
            requestError.response?.data?.detail ||
            "Unable to load conversation."
        );
      }
    } finally {
      if (!silent) setLoadingConversation(false);
    }
  }, []);

  // Initial Load
  useEffect(() => {
    let isMounted = true;

    const init = async () => {
      const inbox = await loadInbox();
      if (!isMounted) return;

      if (!directBookingId) {
        if (inbox.length > 0 && !selectedConversation) {
          setSelectedConversation(inbox[0]);
          loadConversation(inbox[0].booking_id);
        }
        return;
      }

      const existing = inbox.find(
        (c) => Number(c.booking_id) === directBookingId
      );

      if (existing) {
        setSelectedConversation(existing);
        loadConversation(directBookingId);
      } else {
        const temp = {
          booking_id: directBookingId,
          reference_code:
            navigationBooking.referenceCode || `Booking #${directBookingId}`,
          service_title:
            navigationBooking.serviceTitle || "Service Booking",
          other_user_id: Number(
            navigationBooking.providerId || navigationBooking.customerId || 0
          ),
          other_user_name:
            navigationBooking.otherUserName ||
            (currentUser?.role === "provider" ? "Customer" : "Provider"),
          latest_message: null,
          latest_message_at: null,
          unread_count: 0,
          temporary: true,
        };
        setSelectedConversation(temp);
        loadConversation(directBookingId);
      }
    };

    init();

    return () => {
      isMounted = false;
    };
  }, [directBookingId]);

  // Open Conversation
  const openConversation = (conv) => {
    setSelectedConversation(conv);
    setMessageText("");
    navigate(`/messages?booking=${conv.booking_id}`, {
      replace: true,
      state: {
        bookingId: conv.booking_id,
        referenceCode: conv.reference_code,
        serviceTitle: conv.service_title,
        otherUserName: conv.other_user_name,
      },
    });
    loadConversation(conv.booking_id);
  };

  // Send Message
  const sendMessage = async (event) => {
    event.preventDefault();
    const content = messageText.trim();
    if (!content || !selectedConversation) return;

    try {
      setSending(true);
      setError("");

      const response = await api.post(
        `/messages/${selectedConversation.booking_id}`,
        { content }
      );

      const created = response?.data?.data ?? response?.data;
      if (created) {
        setMessages((current) => [...current, created]);
      }

      setMessageText("");

      const updatedInbox = await loadInbox(true);
      const realConv = updatedInbox.find(
        (c) => Number(c.booking_id) === Number(selectedConversation.booking_id)
      );
      if (realConv) {
        setSelectedConversation(realConv);
      }
    } catch (requestError) {
      setError(
        requestError.response?.data?.message ||
          requestError.response?.data?.detail ||
          "Unable to send message."
      );
    } finally {
      setSending(false);
    }
  };

  const unreadTotal = useMemo(
    () =>
      conversations.reduce(
        (acc, c) => acc + Number(c.unread_count || 0),
        0
      ),
    [conversations]
  );

  return (
    <main className="page-section messages-page">
      <div className="container messages-container">
        {/* Header */}
        <div className="page-heading-row">
          <div>
            <div className="badge-pill">
              <MessageCircle size={14} className="text-primary" />
              <span>Direct Messaging</span>
            </div>
            <h1 className="page-title">Booking Messages</h1>
            <p className="page-subtitle">
              Communicate with your {currentUser?.role === "provider" ? "clients" : "service providers"} regarding schedule, instructions, and updates.
            </p>
          </div>

          <div className="heading-actions">
            <button
              type="button"
              className="button button-outline button-sm"
              onClick={() => {
                loadInbox();
                if (selectedConversation) {
                  loadConversation(selectedConversation.booking_id);
                }
              }}
              disabled={loadingInbox}
            >
              <RefreshCw size={15} className={loadingInbox ? "spin" : ""} />
              Refresh
            </button>
          </div>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        {/* Messaging Box */}
        <div className="messages-layout-box">
          {/* Sidebar Conversations */}
          <aside className="messages-sidebar">
            <div className="sidebar-top-bar">
              <strong>Conversations</strong>
              {unreadTotal > 0 && (
                <span className="unread-badge-counter">{unreadTotal} unread</span>
              )}
            </div>

            <div className="conversation-scroll-list">
              {loadingInbox && conversations.length === 0 ? (
                <div className="messages-loading-state">
                  <div className="loader-spinner small" />
                  <span>Loading conversations...</span>
                </div>
              ) : conversations.length === 0 && !selectedConversation?.temporary ? (
                <div className="no-conversations-state">
                  <MessageCircle size={32} />
                  <strong>No conversations yet</strong>
                  <p>Conversations are started automatically when you book or receive a service booking.</p>
                </div>
              ) : (
                <>
                  {selectedConversation?.temporary &&
                    !conversations.some(
                      (c) => c.booking_id === selectedConversation.booking_id
                    ) && (
                      <button
                        type="button"
                        className="conversation-item active temporary"
                      >
                        <div className="item-avatar">
                          <UserRound size={18} />
                        </div>
                        <div className="item-info">
                          <div className="item-title-row">
                            <strong>{selectedConversation.other_user_name}</strong>
                            <span className="item-tag">New</span>
                          </div>
                          <span className="item-service">
                            {selectedConversation.service_title}
                          </span>
                          <span className="item-snippet">Draft message...</span>
                        </div>
                      </button>
                    )}

                  {conversations.map((conv) => {
                    const isSelected =
                      selectedConversation?.booking_id === conv.booking_id;
                    return (
                      <button
                        key={conv.booking_id}
                        type="button"
                        className={`conversation-item ${isSelected ? "active" : ""}`}
                        onClick={() => openConversation(conv)}
                      >
                        <div className="item-avatar">
                          <UserRound size={18} />
                        </div>
                        <div className="item-info">
                          <div className="item-title-row">
                            <strong>{conv.other_user_name || "User"}</strong>
                            {conv.latest_message_at && (
                              <span className="item-time">
                                {formatMessageDate(conv.latest_message_at)}
                              </span>
                            )}
                          </div>
                          <span className="item-service">
                            {conv.service_title || conv.reference_code}
                          </span>
                          <p className="item-snippet">
                            {conv.latest_message || "No messages yet"}
                          </p>
                        </div>
                        {Number(conv.unread_count || 0) > 0 && (
                          <span className="unread-dot-badge">
                            {conv.unread_count}
                          </span>
                        )}
                      </button>
                    );
                  })}
                </>
              )}
            </div>
          </aside>

          {/* Chat Message Window */}
          <section className="chat-window">
            {selectedConversation ? (
              <>
                {/* Chat Top Banner */}
                <div className="chat-header-bar">
                  <div className="chat-recipient-info">
                    <div className="recipient-avatar">
                      <UserRound size={20} />
                    </div>
                    <div>
                      <h3>{selectedConversation.other_user_name || "User"}</h3>
                      <div className="chat-booking-meta">
                        <span>{selectedConversation.service_title}</span>
                        <span>•</span>
                        <span className="booking-ref-badge">
                          {selectedConversation.reference_code}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Messages Body */}
                <div className="chat-messages-body">
                  {loadingConversation && messages.length === 0 ? (
                    <div className="chat-loading-pane">
                      <div className="loader-spinner small" />
                      <span>Loading messages...</span>
                    </div>
                  ) : messages.length === 0 ? (
                    <div className="empty-thread-pane">
                      <MessageCircle size={36} />
                      <h4>Start the conversation</h4>
                      <p>
                        Send a message regarding your appointment, arrival details, or questions.
                      </p>
                    </div>
                  ) : (
                    <div className="messages-thread">
                      {messages.map((msg) => {
                        const isMe = msg.sender_id === currentUser?.id;
                        return (
                          <div
                            key={msg.id}
                            className={`message-bubble-wrapper ${isMe ? "outgoing" : "incoming"}`}
                          >
                            <div className="message-bubble">
                              <p className="message-content">{msg.content}</p>
                              <span className="message-time">
                                {formatTime(msg.created_at)}
                              </span>
                            </div>
                          </div>
                        );
                      })}
                      <div ref={messagesEndRef} />
                    </div>
                  )}
                </div>

                {/* Message Input Box */}
                <form className="chat-input-bar" onSubmit={sendMessage}>
                  <input
                    type="text"
                    value={messageText}
                    onChange={(e) => setMessageText(e.target.value)}
                    placeholder="Type your message here..."
                    maxLength={2000}
                    disabled={sending}
                  />

                  <button
                    type="submit"
                    className="button button-primary send-msg-btn"
                    disabled={sending || !messageText.trim()}
                  >
                    {sending ? (
                      <div className="loader-spinner small white" />
                    ) : (
                      <>
                        <span>Send</span>
                        <Send size={15} />
                      </>
                    )}
                  </button>
                </form>
              </>
            ) : (
              <div className="no-chat-selected">
                <MessageCircle size={48} />
                <h3>Select a conversation</h3>
                <p>Choose an appointment from the left sidebar to read or send messages.</p>
              </div>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}