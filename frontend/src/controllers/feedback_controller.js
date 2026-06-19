import { Controller } from "@hotwired/stimulus";
import { showMessage } from "../utils/messages";

const FOCUSABLE_SELECTOR = [
  "a[href]",
  "button:not([disabled])",
  "textarea:not([disabled])",
  "input:not([disabled])",
  "select:not([disabled])",
  "[tabindex]:not([tabindex='-1'])",
].join(",");

export default class extends Controller {
  static targets = ["toggleButton", "overlay", "formContainer", "feedbackInput"];

  connect() {
    this.isOpen = false;
    this.inertedElements = [];
    this.handleKeydownBound = this.handleKeydown.bind(this);
    document.addEventListener("keydown", this.handleKeydownBound);
  }

  disconnect() {
    document.removeEventListener("keydown", this.handleKeydownBound);
    this.releaseBackground();
  }

  toggleFeedback() {
    if (this.isOpen) {
      this.closeFeedback();
    } else {
      this.openFeedback();
    }
  }

  openFeedback() {
    this.previouslyFocusedElement = document.activeElement;
    this.isOpen = true;
    this.toggleButtonTarget.setAttribute("aria-expanded", "true");
    this.overlayTarget.setAttribute("aria-hidden", "false");
    this.overlayTarget.classList.remove("opacity-0", "pointer-events-none");
    this.overlayTarget.classList.add("opacity-100", "pointer-events-auto");
    this.formContainerTarget.classList.remove("scale-95");
    this.formContainerTarget.classList.add("scale-100");
    this.lockBackground();

    window.setTimeout(() => {
      this.feedbackInputTarget.focus();
    }, this.prefersReducedMotion() ? 0 : 150);
  }

  closeFeedback() {
    if (!this.isOpen) {
      return;
    }

    this.isOpen = false;
    this.toggleButtonTarget.setAttribute("aria-expanded", "false");
    this.formContainerTarget.classList.remove("scale-100");
    this.formContainerTarget.classList.add("scale-95");
    this.overlayTarget.classList.remove("opacity-100", "pointer-events-auto");
    this.overlayTarget.classList.add("opacity-0", "pointer-events-none");
    this.overlayTarget.setAttribute("aria-hidden", "true");
    this.releaseBackground();

    if (this.previouslyFocusedElement instanceof HTMLElement) {
      this.previouslyFocusedElement.focus();
    }
  }

  closeIfClickedOutside(event) {
    if (event.target === this.overlayTarget) {
      this.closeFeedback();
    }
  }

  handleKeydown(event) {
    if (!this.isOpen) {
      return;
    }

    if (event.key === "Escape") {
      event.preventDefault();
      this.closeFeedback();
      return;
    }

    if (event.key === "Tab") {
      this.trapFocus(event);
      return;
    }

    if (
      event.key === "Enter" &&
      !event.shiftKey &&
      document.activeElement === this.feedbackInputTarget
    ) {
      event.preventDefault();
      this.submitFeedback(event);
    }
  }

  trapFocus(event) {
    const focusableElements = Array.from(
      this.formContainerTarget.querySelectorAll(FOCUSABLE_SELECTOR)
    );

    if (focusableElements.length === 0) {
      event.preventDefault();
      this.formContainerTarget.focus();
      return;
    }

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    if (event.shiftKey && document.activeElement === firstElement) {
      event.preventDefault();
      lastElement.focus();
    } else if (!event.shiftKey && document.activeElement === lastElement) {
      event.preventDefault();
      firstElement.focus();
    }
  }

  submitFeedback(event) {
    event.preventDefault();

    const feedback = this.feedbackInputTarget.value.trim();
    if (!feedback) {
      return;
    }

    const submitButton = this.element.querySelector("button[type='submit']");
    const originalButtonText = submitButton?.textContent || "Submit";
    if (submitButton) {
      submitButton.disabled = true;
      submitButton.textContent = "Submitting...";
    }

    fetch("/api/submit-feedback", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
      },
      body: JSON.stringify({ feedback, page: window.location.pathname }),
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
        }

        return response.json();
      })
      .then((data) => {
        this.resetForm();
        this.closeFeedback();
        showMessage(data.message || "Feedback submitted successfully", "success");
      })
      .catch((error) => {
        showMessage(error.message || "Failed to submit feedback. Please try again later.", "error");

        if (submitButton) {
          submitButton.disabled = false;
          submitButton.textContent = originalButtonText;
        }
      });
  }

  resetForm() {
    this.feedbackInputTarget.value = "";
  }

  lockBackground() {
    this.inertedElements = Array.from(document.body.children).filter((element) => {
      return element !== this.element && !element.hasAttribute("aria-live");
    });
    this.inertedElements.forEach((element) => {
      element.inert = true;
    });
  }

  releaseBackground() {
    this.inertedElements.forEach((element) => {
      element.inert = false;
    });
    this.inertedElements = [];
  }

  prefersReducedMotion() {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }
}
