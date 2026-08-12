import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  ArrowLeft,
  CheckCheck,
  MessageCircle,
  RefreshCw,
  Send,
  UserRound,
} from "lucide-react";

import {
  useLocation,
  useNavigate,
  useSearchParams,
} from "react-router-dom";

import api from "../api/api";


function extractData(response) {
  return (
    response?.data?.data ??
    response?.data ??
    []
  );
}


function extractArray(response) {
  const data = extractData(response);

  if (Array.isArray(data)) {
    return data;
  }

  if (Array.isArray(data?.items)) {
    return data.items;
  }

  return [];
}


function formatTime(value) {
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


export default function Messages() {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();

  const [conversations, setConversations] =
    useState([]);

  const [
    selectedConversation,
    setSelectedConversation,
  ] = useState(null);

  const [messages, setMessages] =
    useState([]);

  const [messageText, setMessageText] =
    useState("");

  const [loadingInbox, setLoadingInbox] =
    useState(true);

  const [
    loadingConversation,
    setLoadingConversation,
  ] = useState(false);

  const [sending, setSending] =
    useState(false);

  const [error, setError] =
    useState("");


  let currentUser = null;

  try {
    currentUser = JSON.parse(
      localStorage.getItem(
        "current_user",
      ) || "null",
    );
  } catch {
    currentUser = null;
  }


  // =========================================================
  // DIRECT BOOKING FROM BOOKING HISTORY / PROVIDER BOOKINGS
  // =========================================================

  const bookingIdFromQuery = Number(
    searchParams.get("booking") || 0,
  );

  const navigationBooking =
    location.state || {};

  const directBookingId =
    Number(
      navigationBooking.bookingId ||
        bookingIdFromQuery ||
        0,
    );


  // =========================================================
  // LOAD INBOX
  // =========================================================

  const loadInbox =
    useCallback(async () => {
      try {
        setLoadingInbox(true);
        setError("");

        const response = await api.get(
          "/messages",
        );

        const items =
          extractArray(response);

        setConversations(items);

        return items;
      } catch (requestError) {
        setError(
          requestError.response?.data
            ?.message ||
            requestError.response?.data
              ?.detail ||
            "Unable to load conversations.",
        );

        return [];
      } finally {
        setLoadingInbox(false);
      }
    }, []);


  // =========================================================
  // LOAD CONVERSATION
  // =========================================================

  const loadConversation =
    useCallback(async (bookingId) => {
      if (!bookingId) {
        return;
      }

      try {
        setLoadingConversation(true);
        setError("");

        const response = await api.get(
          `/messages/${bookingId}`,
        );

        setMessages(
          extractArray(response),
        );

        setConversations((current) =>
          current.map(
            (conversation) =>
              conversation.booking_id ===
              bookingId
                ? {
                    ...conversation,
                    unread_count: 0,
                  }
                : conversation,
          ),
        );
      } catch (requestError) {
        setMessages([]);

        setError(
          requestError.response?.data
            ?.message ||
            requestError.response?.data
              ?.detail ||
            "Unable to load conversation.",
        );
      } finally {
        setLoadingConversation(false);
      }
    }, []);


  // =========================================================
  // INITIAL LOAD
  // =========================================================

  useEffect(() => {
    const initializeMessages =
      async () => {
        const inbox =
          await loadInbox();

        if (!directBookingId) {
          return;
        }

        /*
         * If this booking already has messages, use
         * the real conversation from the inbox.
         */
        const existingConversation =
          inbox.find(
            (conversation) =>
              Number(
                conversation.booking_id,
              ) === directBookingId,
          );

        if (existingConversation) {
          setSelectedConversation(
            existingConversation,
          );

          await loadConversation(
            directBookingId,
          );

          return;
        }

        /*
         * No messages exist yet. Build a temporary
         * conversation from navigation state so the
         * customer/provider can send the first message.
         */
        const temporaryConversation = {
          booking_id: directBookingId,

          reference_code:
            navigationBooking.referenceCode ||
            `Booking #${directBookingId}`,

          service_title:
            navigationBooking.serviceTitle ||
            "Service booking",

          other_user_id:
            Number(
              navigationBooking.providerId ||
                navigationBooking.customerId ||
                0,
            ),

          other_user_name:
            navigationBooking.otherUserName ||
            (currentUser?.role ===
            "provider"
              ? "Customer"
              : "Provider"),

          latest_message: null,
          latest_message_at: null,
          unread_count: 0,
          temporary: true,
        };

        setSelectedConversation(
          temporaryConversation,
        );

        await loadConversation(
          directBookingId,
        );
      };

    initializeMessages();
  }, [
    directBookingId,
    loadConversation,
    loadInbox,
  ]);


  // =========================================================
  // OPEN EXISTING CONVERSATION
  // =========================================================

  const openConversation =
    async (conversation) => {
      setSelectedConversation(
        conversation,
      );

      setMessageText("");

      navigate(
        `/messages?booking=${conversation.booking_id}`,
        {
          replace: true,
          state: {
            bookingId:
              conversation.booking_id,
            referenceCode:
              conversation.reference_code,
            serviceTitle:
              conversation.service_title,
            otherUserName:
              conversation.other_user_name,
          },
        },
      );

      await loadConversation(
        conversation.booking_id,
      );
    };


  // =========================================================
  // POLLING
  // =========================================================

  useEffect(() => {
    if (!selectedConversation) {
      return undefined;
    }

    const intervalId =
      window.setInterval(
        async () => {
          await loadConversation(
            selectedConversation.booking_id,
          );

          await loadInbox();
        },
        10000,
      );

    return () => {
      window.clearInterval(
        intervalId,
      );
    };
  }, [
    selectedConversation,
    loadConversation,
    loadInbox,
  ]);


  // =========================================================
  // SEND MESSAGE
  // =========================================================

  const sendMessage =
    async (event) => {
      event.preventDefault();

      const content =
        messageText.trim();

      if (
        !content ||
        !selectedConversation
      ) {
        return;
      }

      try {
        setSending(true);
        setError("");

        const response =
          await api.post(
            `/messages/${selectedConversation.booking_id}`,
            {
              content,
            },
          );

        const created =
          extractData(response);

        setMessages((current) => [
          ...current,
          created,
        ]);

        setMessageText("");

        /*
         * After the first message, the backend inbox
         * now contains this booking conversation.
         */
        const updatedInbox =
          await loadInbox();

        const realConversation =
          updatedInbox.find(
            (conversation) =>
              Number(
                conversation.booking_id,
              ) ===
              Number(
                selectedConversation.booking_id,
              ),
          );

        if (realConversation) {
          setSelectedConversation(
            realConversation,
          );
        }
      } catch (requestError) {
        setError(
          requestError.response?.data
            ?.message ||
            requestError.response?.data
              ?.detail ||
            "Unable to send message.",
        );
      } finally {
        setSending(false);
      }
    };


  // =========================================================
  // UNREAD TOTAL
  // =========================================================

  const unreadTotal = useMemo(
    () =>
      conversations.reduce(
        (total, conversation) =>
          total +
          Number(
            conversation.unread_count ||
              0,
          ),
        0,
      ),
    [conversations],
  );


  // =========================================================
  // UI
  // =========================================================

  return (
    <main className="messages-page">

      <div className="messages-container">

        <section className="messages-header">

          <div>
            <span className="eyebrow">
              Booking conversations
            </span>

            <h1>
              Messages
            </h1>

            <p>
              Chat with customers or providers
              about your service bookings.
            </p>
          </div>


          <div className="messages-header-actions">

            {unreadTotal > 0 && (
              <span className="messages-unread-summary">
                <MessageCircle size={17} />

                {unreadTotal} unread
              </span>
            )}

            <button
              type="button"
              className="button button-outline"
              onClick={loadInbox}
              disabled={loadingInbox}
            >
              <RefreshCw
                size={18}
                className={
                  loadingInbox
                    ? "spin"
                    : ""
                }
              />

              Refresh
            </button>

          </div>

        </section>


        {error && (
          <div className="alert alert-error">
            {error}
          </div>
        )}


        <section className="messages-shell">

          {/* =================================================
              INBOX
          ================================================== */}

          <aside className="messages-sidebar">

            <div className="messages-sidebar-header">
              <div>
                <strong>
                  Conversations
                </strong>

                <span>
                  {conversations.length}{" "}
                  {conversations.length === 1
                    ? "conversation"
                    : "conversations"}
                </span>
              </div>
            </div>


            <div className="messages-conversation-list">

              {loadingInbox &&
              conversations.length ===
                0 ? (
                <div className="messages-empty-small">
                  <RefreshCw
                    className="spin"
                    size={24}
                  />

                  <span>
                    Loading...
                  </span>
                </div>
              ) : conversations.length ===
                  0 &&
                !selectedConversation ? (
                <div className="messages-empty-small">

                  <MessageCircle
                    size={32}
                  />

                  <strong>
                    No conversations yet
                  </strong>

                  <span>
                    Open a booking and choose
                    Message provider/customer
                    to start chatting.
                  </span>

                </div>
              ) : (
                conversations.map(
                  (conversation) => {
                    const active =
                      Number(
                        selectedConversation
                          ?.booking_id,
                      ) ===
                      Number(
                        conversation.booking_id,
                      );

                    return (
                      <button
                        type="button"
                        key={
                          conversation.booking_id
                        }
                        className={`messages-conversation-item ${
                          active
                            ? "active"
                            : ""
                        }`}
                        onClick={() =>
                          openConversation(
                            conversation,
                          )
                        }
                      >

                        <span className="messages-avatar">
                          <UserRound
                            size={20}
                          />
                        </span>


                        <span className="messages-conversation-content">

                          <span className="messages-conversation-top">

                            <strong>
                              {conversation.other_user_name ||
                                "ServiceHub user"}
                            </strong>

                            <small>
                              {formatTime(
                                conversation.latest_message_at,
                              )}
                            </small>

                          </span>


                          <span className="messages-service-name">
                            {conversation.service_title}
                          </span>


                          <span className="messages-latest-row">

                            <span>
                              {conversation.latest_message ||
                                "Open conversation"}
                            </span>

                            {Number(
                              conversation.unread_count ||
                                0,
                            ) > 0 && (
                              <strong className="messages-unread-badge">
                                {
                                  conversation.unread_count
                                }
                              </strong>
                            )}

                          </span>


                          <small className="messages-reference">
                            {
                              conversation.reference_code
                            }
                          </small>

                        </span>

                      </button>
                    );
                  },
                )
              )}

            </div>

          </aside>


          {/* =================================================
              CHAT
          ================================================== */}

          <section className="messages-chat">

            {!selectedConversation ? (
              <div className="messages-chat-empty">

                <MessageCircle
                  size={48}
                />

                <h2>
                  Select a conversation
                </h2>

                <p>
                  Choose a booking conversation
                  from the left or open Messages
                  from one of your booking cards.
                </p>

              </div>
            ) : (
              <>

                {/* CHAT HEADER */}

                <div className="messages-chat-header">

                  <button
                    type="button"
                    className="messages-mobile-back"
                    onClick={() => {
                      setSelectedConversation(
                        null,
                      );

                      setMessages([]);

                      navigate(
                        "/messages",
                        {
                          replace: true,
                        },
                      );
                    }}
                  >
                    <ArrowLeft
                      size={18}
                    />
                  </button>


                  <span className="messages-avatar">
                    <UserRound
                      size={21}
                    />
                  </span>


                  <div>
                    <strong>
                      {selectedConversation.other_user_name ||
                        "ServiceHub user"}
                    </strong>

                    <span>
                      {
                        selectedConversation.service_title
                      }
                    </span>

                    <small>
                      {
                        selectedConversation.reference_code
                      }
                    </small>
                  </div>

                </div>


                {/* MESSAGE BODY */}

                <div className="messages-chat-body">

                  {loadingConversation &&
                  messages.length ===
                    0 ? (
                    <div className="messages-chat-loading">
                      <RefreshCw
                        className="spin"
                        size={28}
                      />

                      Loading messages...
                    </div>
                  ) : messages.length ===
                    0 ? (
                    <div className="messages-chat-empty small">

                      <MessageCircle
                        size={38}
                      />

                      <h3>
                        Start the conversation
                      </h3>

                      <p>
                        Send the first message about
                        this booking.
                      </p>

                    </div>
                  ) : (
                    messages.map(
                      (message) => {
                        const mine =
                          Number(
                            message.sender_id,
                          ) ===
                          Number(
                            currentUser?.id,
                          );

                        return (
                          <div
                            key={message.id}
                            className={`message-row ${
                              mine
                                ? "mine"
                                : "theirs"
                            }`}
                          >
                            <div className="message-bubble">

                              <p>
                                {
                                  message.content
                                }
                              </p>

                              <span>
                                {formatTime(
                                  message.created_at,
                                )}

                                {mine &&
                                  message.is_read && (
                                    <CheckCheck
                                      size={14}
                                    />
                                  )}
                              </span>

                            </div>
                          </div>
                        );
                      },
                    )
                  )}

                </div>


                {/* COMPOSER */}

                <form
                  className="messages-composer"
                  onSubmit={sendMessage}
                >

                  <textarea
                    value={messageText}
                    onChange={(event) =>
                      setMessageText(
                        event.target.value,
                      )
                    }
                    placeholder="Write a message..."
                    rows={2}
                    maxLength={3000}
                    disabled={sending}
                  />


                  <button
                    type="submit"
                    className="button"
                    disabled={
                      sending ||
                      !messageText.trim()
                    }
                  >
                    <Send size={18} />

                    {sending
                      ? "Sending..."
                      : "Send"}
                  </button>

                </form>

              </>
            )}

          </section>

        </section>

      </div>

    </main>
  );
}