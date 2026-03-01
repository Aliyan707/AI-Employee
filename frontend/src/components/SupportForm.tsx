"use client";

import { FormEvent, useState } from "react";
import ResponseDisplay from "./ResponseDisplay";

interface FormState {
  email: string;
  name: string;
  message: string;
}

interface ApiResponse {
  response_text: string | null;
  ticket_id: string | null;
  channel: string;
  escalated: boolean;
}

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function SupportForm() {
  const [form, setForm] = useState<FormState>({
    email: "",
    name: "",
    message: "",
  });
  const [errors, setErrors] = useState<Partial<FormState>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiResponse, setApiResponse] = useState<ApiResponse | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  function validate(): boolean {
    const newErrors: Partial<FormState> = {};
    if (!form.email) {
      newErrors.email = "Email address is required.";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
      newErrors.email = "Please enter a valid email address.";
    }
    if (!form.message || form.message.trim().length < 10) {
      newErrors.message = "Message must be at least 10 characters.";
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitError(null);
    setApiResponse(null);

    if (!validate()) return;

    setIsSubmitting(true);

    try {
      const payload = {
        email: form.email.trim(),
        name: form.name.trim() || undefined,
        message: form.message.trim(),
      };

      const res = await fetch(`${API_URL}/webhooks/webform`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const detail = await res.text();
        throw new Error(`Server error ${res.status}: ${detail}`);
      }

      const data: ApiResponse = await res.json();
      setApiResponse(data);

      // Reset form on success
      setForm({ email: "", name: "", message: "" });
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Something went wrong. Please try again.";
      setSubmitError(message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="support-form-wrapper">
      <form
        onSubmit={handleSubmit}
        className="support-form"
        noValidate
        aria-label="Customer support form"
      >
        {/* Email */}
        <div className="form-group">
          <label htmlFor="email" className="form-label">
            Email address <span className="form-required" aria-hidden="true">*</span>
          </label>
          <input
            id="email"
            type="email"
            className={`form-input ${errors.email ? "form-input--error" : ""}`}
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            placeholder="you@example.com"
            disabled={isSubmitting}
            required
            aria-describedby={errors.email ? "email-error" : undefined}
          />
          {errors.email && (
            <p id="email-error" className="form-error" role="alert">
              {errors.email}
            </p>
          )}
        </div>

        {/* Name (optional) */}
        <div className="form-group">
          <label htmlFor="name" className="form-label">
            Name{" "}
            <span className="form-optional">(optional)</span>
          </label>
          <input
            id="name"
            type="text"
            className="form-input"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            placeholder="Your name"
            disabled={isSubmitting}
            maxLength={255}
          />
        </div>

        {/* Message */}
        <div className="form-group">
          <label htmlFor="message" className="form-label">
            Message <span className="form-required" aria-hidden="true">*</span>
          </label>
          <textarea
            id="message"
            className={`form-textarea ${errors.message ? "form-input--error" : ""}`}
            value={form.message}
            onChange={(e) => setForm({ ...form, message: e.target.value })}
            placeholder="Describe your question or issue..."
            disabled={isSubmitting}
            required
            rows={5}
            minLength={10}
            aria-describedby={errors.message ? "message-error" : undefined}
          />
          {errors.message && (
            <p id="message-error" className="form-error" role="alert">
              {errors.message}
            </p>
          )}
        </div>

        {/* Submit error */}
        {submitError && (
          <div className="form-submit-error" role="alert">
            {submitError}
          </div>
        )}

        {/* Submit */}
        <button
          type="submit"
          className="form-submit"
          disabled={isSubmitting}
          aria-busy={isSubmitting}
        >
          {isSubmitting ? (
            <>
              <span className="spinner spinner--small" aria-hidden="true" />
              Sending...
            </>
          ) : (
            "Send Message"
          )}
        </button>
      </form>

      {/* Response */}
      <ResponseDisplay
        responseText={apiResponse?.response_text ?? null}
        escalated={apiResponse?.escalated ?? false}
        ticketId={apiResponse?.ticket_id ?? null}
        isLoading={isSubmitting}
      />
    </div>
  );
}
