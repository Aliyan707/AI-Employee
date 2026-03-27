import SupportForm from "../components/SupportForm";

/**
 * Root page — minimal professional support widget.
 *
 * Layout:
 *   Logo placeholder + product name
 *   SupportForm (email, name, message)
 *   Response area (rendered inside SupportForm via ResponseDisplay)
 *   Footer disclaimer
 */
export default function HomePage() {
  return (
    <main className="page-wrapper">
      <div className="widget-card">
        {/* Header */}
        <header className="widget-header">
          {/* Logo placeholder — replace src with your brand asset */}
          <div className="widget-logo" aria-hidden="true">
            {/* Headset icon (inline SVG, no external dependencies) */}
            <svg
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
              aria-hidden="true"
              focusable="false"
            >
              <path d="M12 2C6.48 2 2 6.48 2 12v4c0 1.1.9 2 2 2h1c1.1 0 2-.9 2-2v-3c0-1.1-.9-2-2-2H4.07C4.56 7.19 7.92 4 12 4s7.44 3.19 7.93 7H19c-1.1 0-2 .9-2 2v3c0 1.1.9 2 2 2h1c1.1 0 2-.9 2-2v-4c0-5.52-4.48-10-10-10z" />
            </svg>
          </div>

          <div>
            <h1 className="widget-title">Customer Support</h1>
            <p className="widget-subtitle">
              Typically responds in under a minute
            </p>
          </div>
        </header>

        {/* Support form + inline response area */}
        <SupportForm />
      </div>

      {/* Footer */}
      <footer className="page-footer">
        <p>Powered by AI &mdash; escalated queries are handled by humans.</p>
        <p>
          Need urgent help?{" "}
          <a href="mailto:support@example.com">Email our team</a>
        </p>
      </footer>
    </main>
  );
}
