import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <section
      style={{
        minHeight: "60vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        textAlign: "center",
        padding: "2rem",
        gap: "1rem",
      }}
    >
      <h1 style={{ fontSize: "5rem", fontWeight: 800, color: "var(--color-primary, #6366f1)", margin: 0, lineHeight: 1 }}>
        404
      </h1>
      <h2 style={{ fontSize: "1.5rem", fontWeight: 600, margin: 0 }}>Page Not Found</h2>
      <p style={{ color: "var(--color-muted, #6b7280)", maxWidth: 400 }}>
        The page you&rsquo;re looking for doesn&rsquo;t exist or has been moved.
      </p>
      <Link
        to="/"
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "0.5rem",
          background: "var(--color-primary, #6366f1)",
          color: "#fff",
          padding: "0.75rem 1.5rem",
          borderRadius: "0.5rem",
          textDecoration: "none",
          fontWeight: 600,
          marginTop: "0.5rem",
        }}
      >
        ← Back to Home
      </Link>
    </section>
  );
}
