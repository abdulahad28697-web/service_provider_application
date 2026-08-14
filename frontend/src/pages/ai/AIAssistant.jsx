import { useRef, useState } from "react";
import {
  Bot,
  CalendarCheck,
  Lightbulb,
  LoaderCircle,
  MessageCircleQuestion,
  Search,
  Send,
  Sparkles,
  User,
} from "lucide-react";

import api from "../../api/api";

const welcomeMessage = {
  id: 1,
  sender: "assistant",
  text:
    "Hello! I am your ServiceHub AI Assistant. I can help you find providers, " +
    "compare services, answer common questions and assist with bookings.",
  actions: [
    "Recommend a provider",
    "Find affordable services",
    "Help me book",
    "Answer an FAQ",
  ],
};

const quickPrompts = [
  {
    icon: Search,
    title: "Find a provider",
    prompt: "Help me find a trusted plumbing provider.",
  },
  {
    icon: Lightbulb,
    title: "Get recommendations",
    prompt: "Recommend an affordable home cleaning service.",
  },
  {
    icon: CalendarCheck,
    title: "Booking assistance",
    prompt: "Help me book a service for tomorrow.",
  },
  {
    icon: MessageCircleQuestion,
    title: "Ask a question",
    prompt: "How does ServiceHub booking work?",
  },
];

function getResponseData(response) {
  return response?.data?.data ?? response?.data ?? {};
}

function AIAssistant() {
  const [messages, setMessages] = useState([welcomeMessage]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");

  const messageId = useRef(2);

  const addMessage = (message) => {
    setMessages((current) => [
      ...current,
      {
        id: messageId.current++,
        ...message,
      },
    ]);
  };

  const sendMessage = async (messageText) => {
    const cleanMessage = messageText.trim();

    if (!cleanMessage || sending) return;

    addMessage({
      sender: "user",
      text: cleanMessage,
      actions: [],
    });

    setInput("");
    setSending(true);
    setError("");

    try {
      const response = await api.post("/ai/chatbot", {
        message: cleanMessage,
      });

      const data = getResponseData(response);

      addMessage({
        sender: "assistant",
        text:
          data.response ||
          data.reply ||
          data.message ||
          "I received your request. How else can I help you?",
        actions: data.suggested_actions || data.actions || [],
      });
    } catch (err) {
      setError(
        err.response?.data?.message ||
          err.response?.data?.detail ||
          "The AI assistant is currently unavailable. Please try again."
      );

      addMessage({
        sender: "assistant",
        text:
          "Sorry, I could not process your request right now. " +
          "Please check that the backend server is running and try again.",
        actions: ["Try again"],
      });
    } finally {
      setSending(false);
    }
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    sendMessage(input);
  };

  return (
    <main className="page-section ai-page">
      <div className="container ai-page-container">
        <div className="ai-page-heading">
          <div className="ai-heading-icon">
            <Sparkles size={28} />
          </div>

          <div>
            <span className="eyebrow">Smart service assistance</span>
            <h1>AI User Assistant</h1>
            <p>
              Search naturally, compare options and get personalized help with
              your service bookings.
            </p>
          </div>
        </div>

        <div className="ai-layout">
          <aside className="ai-sidebar">
            <section className="panel ai-sidebar-panel">
              <h2>How can I help?</h2>
              <p>Select an option or type your own question.</p>

              <div className="quick-prompt-list">
                {quickPrompts.map((item) => {
                  const Icon = item.icon;

                  return (
                    <button
                      type="button"
                      className="quick-prompt"
                      key={item.title}
                      onClick={() => sendMessage(item.prompt)}
                      disabled={sending}
                    >
                      <span>
                        <Icon size={19} />
                      </span>

                      <div>
                        <strong>{item.title}</strong>
                        <small>{item.prompt}</small>
                      </div>
                    </button>
                  );
                })}
              </div>
            </section>

            <section className="panel ai-tip-panel">
              <Lightbulb size={22} />

              <div>
                <h3>Ask naturally</h3>
                <p>
                  Try: “Find a highly rated electrician under PKR 2,000.”
                </p>
              </div>
            </section>
          </aside>

          <section className="panel chat-panel">
            <div className="chat-header">
              <div className="chat-avatar assistant-avatar">
                <Bot size={22} />
              </div>

              <div>
                <h2>ServiceHub Assistant</h2>

                <span className="online-status">
                  <span />
                  Online
                </span>
              </div>
            </div>

            <div className="chat-messages" aria-live="polite">
              {messages.map((message) => (
                <div
                  className={`chat-message-row ${
                    message.sender === "user"
                      ? "chat-message-user"
                      : "chat-message-assistant"
                  }`}
                  key={message.id}
                >
                  <div
                    className={`chat-avatar ${
                      message.sender === "user"
                        ? "user-avatar"
                        : "assistant-avatar"
                    }`}
                  >
                    {message.sender === "user" ? (
                      <User size={18} />
                    ) : (
                      <Bot size={18} />
                    )}
                  </div>

                  <div className="chat-message-content">
                    <div className="chat-bubble">
                      <p>{message.text}</p>
                    </div>

                    {message.actions?.length > 0 && (
                      <div className="suggested-actions">
                        {message.actions.map((action) => (
                          <button
                            type="button"
                            key={action}
                            onClick={() => sendMessage(action)}
                            disabled={sending}
                          >
                            {action}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {sending && (
                <div className="chat-message-row chat-message-assistant">
                  <div className="chat-avatar assistant-avatar">
                    <Bot size={18} />
                  </div>

                  <div className="chat-bubble typing-bubble">
                    <LoaderCircle className="spin-icon" size={18} />
                    <span>Assistant is thinking...</span>
                  </div>
                </div>
              )}
            </div>

            {error && <div className="chat-error">{error}</div>}

            <form className="chat-input-form" onSubmit={handleSubmit}>
              <input
                type="text"
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder="Ask me to find, compare or book a service..."
                aria-label="Message for AI assistant"
                disabled={sending}
              />

              <button
                type="submit"
                className="chat-send-button"
                disabled={sending || !input.trim()}
                aria-label="Send message"
              >
                <Send size={20} />
              </button>
            </form>
          </section>
        </div>
      </div>
    </main>
  );
}

export default AIAssistant;