import {
  ArrowRight,
  Bot,
  CheckCircle2,
  Clock3,
  Search,
  ShieldCheck,
  Sparkles,
  Star,
  Wrench,
  Zap,
} from "lucide-react";
import { Link } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

const categories = [
  {
    title: "Home repairs",
    description: "Plumbing, electrical and maintenance.",
    icon: Wrench,
  },
  {
    title: "Cleaning",
    description: "Reliable home and office cleaning.",
    icon: Sparkles,
  },
  {
    title: "Electrical",
    description: "Qualified professionals for safe repairs.",
    icon: Zap,
  },
];

const benefits = [
  {
    title: "Verified professionals",
    description:
      "Provider applications are reviewed before approval.",
    icon: ShieldCheck,
  },
  {
    title: "Easy booking",
    description:
      "Choose a service, date and location in minutes.",
    icon: Clock3,
  },
  {
    title: "AI-powered matching",
    description:
      "Receive recommendations based on your needs.",
    icon: Bot,
  },
];

export default function Home() {
  const { user, isAuthenticated } = useAuth();

  return (
    <>
      <section className="hero">
        <div className="container hero-grid">
          <div className="hero-content">
            <span className="eyebrow">
              <CheckCircle2 size={16} />
              Trusted local professionals
            </span>

            <h1>
              Find the right expert for{" "}
              <span>every service.</span>
            </h1>

            <p>
              Search, compare and book verified service
              providers from one simple platform.
            </p>

            <div className="hero-actions">
              <Link
                className="button"
                to="/services"
              >
                <Search size={18} />
                Explore services
              </Link>

              <Link
                className="button button-outline"
                to={
                  isAuthenticated
                    ? "/assistant"
                    : "/register"
                }
              >
                <Bot size={18} />
                {isAuthenticated
                  ? "Ask AI assistant"
                  : "Create free account"}
              </Link>
            </div>

            <div className="hero-trust">
              <div className="avatars">
                <span>AK</span>
                <span>FA</span>
                <span>MA</span>
              </div>

              <div>
                <div className="stars">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <Star
                      key={star}
                      size={15}
                      fill="currentColor"
                    />
                  ))}
                </div>
                <small>
                  Built for customers and professionals
                </small>
              </div>
            </div>
          </div>

          <div className="hero-card">
            <div className="hero-card-badge">
              <ShieldCheck size={20} />
              Verified providers
            </div>

            <div className="service-preview">
              <div className="preview-icon">
                <Wrench size={25} />
              </div>

              <div>
                <span>Popular service</span>
                <h3>Home maintenance</h3>
                <p>Top-rated experts near you</p>
              </div>
            </div>

            <div className="preview-stats">
              <div>
                <strong>Fast</strong>
                <span>Search</span>
              </div>
              <div>
                <strong>Secure</strong>
                <span>Accounts</span>
              </div>
              <div>
                <strong>Smart</strong>
                <span>Matching</span>
              </div>
            </div>

            {user && (
              <div className="welcome-card">
                Welcome back,{" "}
                <strong>{user.full_name}</strong>
              </div>
            )}
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container">
          <div className="section-heading">
            <div>
              <span className="eyebrow">
                Explore categories
              </span>
              <h2>Services for every need</h2>
            </div>

            <Link
              className="text-link"
              to="/services"
            >
              View all
              <ArrowRight size={17} />
            </Link>
          </div>

          <div className="card-grid three-columns">
            {categories.map(
              ({ title, description, icon: Icon }) => (
                <article
                  className="category-card"
                  key={title}
                >
                  <div className="card-icon">
                    <Icon size={24} />
                  </div>
                  <h3>{title}</h3>
                  <p>{description}</p>
                  <Link to="/services">
                    Browse services
                    <ArrowRight size={16} />
                  </Link>
                </article>
              ),
            )}
          </div>
        </div>
      </section>

      <section className="section section-muted">
        <div className="container">
          <div className="section-heading centered">
            <span className="eyebrow">
              Why ServiceHub
            </span>
            <h2>Simple, secure and intelligent</h2>
            <p>
              Everything you need to discover and manage
              professional services.
            </p>
          </div>

          <div className="card-grid three-columns">
            {benefits.map(
              ({ title, description, icon: Icon }) => (
                <article
                  className="benefit-card"
                  key={title}
                >
                  <Icon size={27} />
                  <h3>{title}</h3>
                  <p>{description}</p>
                </article>
              ),
            )}
          </div>
        </div>
      </section>
    </>
  );
}