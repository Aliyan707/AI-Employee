"use client";

interface ResponseDisplayProps {
  responseText: string | null;
  escalated: boolean;
  ticketId: string | null;
  isLoading: boolean;
}

export default function ResponseDisplay({
  responseText,
  escalated,
  ticketId,
  isLoading,
}: ResponseDisplayProps) {
  if (isLoading) {
    return (
      <div className="response-display response-display--loading">
        <div className="spinner" aria-label="Loading response" />
        <p className="response-display__loading-text">
          Processing your request...
        </p>
      </div>
    );
  }

  if (!responseText && !escalated) {
    return null;
  }

  return (
    <div
      className={`response-display ${
        escalated ? "response-display--escalated" : "response-display--success"
      }`}
      role="region"
      aria-label="Support response"
    >
      {escalated ? (
        <div className="response-display__escalated">
          <div className="response-display__escalated-icon" aria-hidden="true">
            &#128100;
          </div>
          <h3 className="response-display__heading">
            Connecting you with a specialist
          </h3>
          <p className="response-display__body">
            {responseText ||
              "A team member will follow up with you shortly. Thank you for your patience."}
          </p>
          {ticketId && (
            <p className="response-display__ticket-ref">
              Reference:{" "}
              <code className="response-display__ticket-id">
                {ticketId.slice(0, 8).toUpperCase()}
              </code>
            </p>
          )}
          <p className="response-display__disclaimer">
            A human agent will review your request and respond within 2 business
            hours.
          </p>
        </div>
      ) : (
        <div className="response-display__ai">
          <div className="response-display__header">
            <span className="response-display__badge">AI Response</span>
            {ticketId && (
              <span className="response-display__ticket-ref">
                Ref:{" "}
                <code>{ticketId.slice(0, 8).toUpperCase()}</code>
              </span>
            )}
          </div>
          <div className="response-display__body response-display__body--ai">
            {responseText &&
              responseText.split("\n").map((line, idx) => (
                <p key={idx} className="response-display__paragraph">
                  {line}
                </p>
              ))}
          </div>
          <p className="response-display__disclaimer">
            Powered by AI. Escalated queries are handled by humans.
          </p>
        </div>
      )}
    </div>
  );
}
