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
  CalendarCheck,
  CreditCard,
  ThumbsUp,
  MapPin,
  TrendingUp,
} from "lucide-react";
import { Link } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

const categories = [
  {
    title: "Home Repairs & Maintenance",
    description: "Plumbing, carpenter work, roofing, and general repairs.",
    icon: Wrench,
    color: "#2563eb",
  },
  {
    title: "Deep Cleaning & Maid",
    description: "Eco-friendly full house, kitchen, and commercial cleaning.",
    icon: Sparkles,
    color: "#059669",
  },
  {
    title: "Electrical & Appliances",
    description: "Certified electricians, AC service, and fridge repair.",
    icon: Zap,
    color: "#d97706",
  },
];

const howItWorks = [
  {
    step: "01",
    title: "Discover Verified Experts",
    description:
      "Search transparent ratings, real customer reviews, and clear upfront pricing for any service.",
    icon: Search,
  },
  {
    step: "02",
    title: "Choose Real-Time Slots",
    description:
      "Select your ideal appointment date and pick from guaranteed conflict-free available time windows.",
    icon: CalendarCheck,
  },
  {
    step: "03",
    title: "Enjoy Professional Service",
    description:
      "Your verified specialist arrives on schedule. Pay securely and leave a review once satisfied.",
    icon: ThumbsUp,
  },
];

const benefits = [
  {
    title: "100% Verified Providers",
    description:
      "Every specialist profile and credential is vetted to ensure dependable quality and safety.",
    icon: ShieldCheck,
  },
  {
    title: "Frictionless Booking",
    description:
      "Select your service, choose an available date and time slot, and receive instant booking confirmation.",
    icon: Clock3,
  },
  {
    title: "AI-Powered Assistant",
    description:
      "Chat with our built-in AI concierge to get intelligent recommendations tailored to your exact task.",
    icon: Bot,
  },
];

export default function Home() {
  const { user, isAuthenticated } = useAuth();

  return (
    <div className="home-wrapper">
      {/* Hero Section */}
      <section className="hero">
        <div className="container hero-grid">
          <div className="hero-content">
            <div className="badge-pill">
              <ShieldCheck size={14} className="text-primary" />
              <span>Verified On-Demand Services</span>
            </div>

            <h1>
              Book Trusted Local Experts for <span>Every Home Need</span>
            </h1>

            <p>
              Compare verified specialists, view real-time time slots, and schedule professional
              home services with total transparent pricing.
            </p>

            <div className="hero-actions">
              <Link className="button button-primary" to="/services">
                <Search size={18} />
                Explore Services
              </Link>

              <Link
                className="button button-outline"
                to={isAuthenticated ? "/assistant" : "/register"}
              >
                <Bot size={18} />
                {isAuthenticated ? "Ask AI Assistant" : "Create Free Account"}
              </Link>
            </div>

            <div className="hero-trust">
              <div className="avatars">
                <span>AK</span>
                <span>FA</span>
                <span>MA</span>
                <span>SA</span>
              </div>

              <div>
                <div className="stars">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <Star key={star} size={15} fill="#f59e0b" color="#f59e0b" />
                  ))}
                </div>
                <small>Rated <strong>4.9/5</strong> by over 2,500+ satisfied clients</small>
              </div>
            </div>
          </div>

          <div className="hero-card">
            <div className="hero-card-badge">
              <ShieldCheck size={18} />
              Quality Assured Platform
            </div>

            <div className="service-preview">
              <div className="preview-icon">
                <Wrench size={26} />
              </div>

              <div>
                <span className="preview-subtitle">Most Booked Today</span>
                <h3>Deep Home Cleaning</h3>
                <p>Top-rated certified specialists near you</p>
              </div>
            </div>

            <div className="preview-stats">
              <div>
                <strong>30 Mins</strong>
                <span>Avg Response</span>
              </div>
              <div>
                <strong>100%</strong>
                <span>Verified Pros</span>
              </div>
              <div>
                <strong>Transparent</strong>
                <span>Fixed Pricing</span>
              </div>
            </div>

            {user && (
              <div className="welcome-card">
                Welcome back, <strong>{user.full_name}</strong>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Popular Categories */}
      <section className="section">
        <div className="container">
          <div className="section-heading">
            <div>
              <span className="eyebrow">Top Categories</span>
              <h2>Services Tailored for You</h2>
            </div>

            <Link className="text-link" to="/services">
              View All Services
              <ArrowRight size={17} />
            </Link>
          </div>

          <div className="card-grid three-columns">
            {categories.map(({ title, description, icon: Icon }) => (
              <article className="category-card" key={title}>
                <div className="card-icon">
                  <Icon size={24} />
                </div>
                <h3>{title}</h3>
                <p>{description}</p>
                <Link to="/services" className="category-card-link">
                  Browse specialists
                  <ArrowRight size={15} />
                </Link>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="section section-muted">
        <div className="container">
          <div className="section-heading centered">
            <span className="eyebrow">Seamless Process</span>
            <h2>How ServiceHub Works</h2>
            <p>Three effortless steps to connect with dependable professionals.</p>
          </div>

          <div className="card-grid three-columns">
            {howItWorks.map(({ step, title, description, icon: Icon }) => (
              <div className="how-it-works-card" key={step}>
                <div className="step-badge">{step}</div>
                <div className="how-icon">
                  <Icon size={26} />
                </div>
                <h3>{title}</h3>
                <p>{description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Platform Benefits */}
      <section className="section">
        <div className="container">
          <div className="section-heading centered">
            <span className="eyebrow">The ServiceHub Difference</span>
            <h2>Built for Safety, Quality, and Speed</h2>
          </div>

          <div className="card-grid three-columns">
            {benefits.map(({ title, description, icon: Icon }) => (
              <article className="benefit-card" key={title}>
                <div className="benefit-icon-wrap">
                  <Icon size={26} />
                </div>
                <h3>{title}</h3>
                <p>{description}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Banner */}
      <section className="cta-section">
        <div className="container">
          <div className="cta-banner">
            <div>
              <h2>Ready to Book a Professional Service?</h2>
              <p>Join thousands of customers who rely on ServiceHub for high-quality, stress-free services.</p>
            </div>
            <div className="cta-actions">
              <Link to="/services" className="button button-primary cta-btn">
                Book a Service Now
                <ArrowRight size={18} />
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}