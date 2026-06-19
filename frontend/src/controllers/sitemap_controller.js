import { Controller } from "@hotwired/stimulus";
import { showMessage } from "../utils/messages";
import { FOCUSABLE_SELECTOR } from "../utils/focusable";

export default class extends Controller {
  static targets = [
    "item",
    "formContainer",
    "toggleButton",
    "onboardingModal",
    "onboardingOverlay",
    "onboardingDialog",
    "onboardingInitialFocus",
  ];

  connect() {
    this.onboardingOpen = false;
    this.inertedElements = [];
    this.handleKeydownBound = this.handleKeydown.bind(this);
    document.addEventListener("keydown", this.handleKeydownBound);

    if (this.shouldSkipOnboarding()) {
      this.hideOnboarding();
    } else if (this.hasOnboardingModalTarget) {
      this.openOnboarding();
    }
  }

  disconnect() {
    document.removeEventListener("keydown", this.handleKeydownBound);
    this.releaseOnboardingBackground();
  }

  toggleForm(event) {
    event.preventDefault();
    this.formContainerTarget.classList.toggle("hidden");

    if (this.formContainerTarget.classList.contains("hidden")) {
      this.toggleButtonTarget.textContent = "Add Sitemap";
    } else {
      this.toggleButtonTarget.textContent = "Cancel";
    }
  }

  skipOnboarding(event) {
    event.preventDefault();
    this.setSkipOnboarding();
    this.hideOnboarding();
  }

  showOnboarding(event) {
    event.preventDefault();
    this.previouslyFocusedElement = event.currentTarget;
    this.openOnboarding();
  }

  async delete(event) {
    event.preventDefault();

    const button = event.currentTarget;
    const sitemapId = button.dataset.sitemapId;
    const sitemapUrl = button.dataset.sitemapUrl;

    if (!confirm(`Archive this sitemap?\n\n${sitemapUrl}\n\nYou can re-enable it from Settings.`)) {
      return;
    }

    try {
      const response = await fetch(`/api/sitemaps/${sitemapId}`, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": this.getCsrfToken(),
        },
      });

      const data = await response.json();

      if (response.ok && data.success) {
        const itemElement = button.closest('[data-sitemap-target="item"]');
        if (itemElement) {
          itemElement.remove();
        }

        const remainingItems = this.itemTargets.length;
        if (remainingItems === 0) {
          location.reload();
        }

        showMessage(data.message, "success");
      } else {
        showMessage(data.message || "Failed to archive sitemap", "error");
      }
    } catch {
      showMessage("An error occurred while archiving the sitemap", "error");
    }
  }

  handleKeydown(event) {
    if (!this.onboardingOpen) {
      return;
    }

    if (event.key === "Escape") {
      event.preventDefault();
      this.hideOnboarding();
      return;
    }

    if (event.key === "Tab") {
      this.trapOnboardingFocus(event);
    }
  }

  openOnboarding() {
    if (!this.hasOnboardingModalTarget) {
      return;
    }

    this.onboardingOpen = true;
    this.onboardingModalTarget.classList.remove("hidden");
    this.onboardingModalTarget.setAttribute("aria-hidden", "false");

    if (this.hasOnboardingOverlayTarget) {
      this.onboardingOverlayTarget.classList.remove("hidden");
    }

    this.lockOnboardingBackground();

    window.setTimeout(() => {
      this.focusInitialOnboardingField();
    }, 0);
  }

  hideOnboarding() {
    this.onboardingOpen = false;

    if (this.hasOnboardingModalTarget) {
      this.onboardingModalTarget.classList.add("hidden");
      this.onboardingModalTarget.setAttribute("aria-hidden", "true");
    }

    if (this.hasOnboardingOverlayTarget) {
      this.onboardingOverlayTarget.classList.add("hidden");
    }

    this.releaseOnboardingBackground();

    const nextFocusTarget =
      this.previouslyFocusedElement ||
      this.element.querySelector('[data-action~="click->sitemap#showOnboarding"]');

    if (nextFocusTarget instanceof HTMLElement) {
      nextFocusTarget.focus();
    }

    this.previouslyFocusedElement = null;
  }

  trapOnboardingFocus(event) {
    if (!this.hasOnboardingDialogTarget) {
      return;
    }

    const focusableElements = Array.from(
      this.onboardingDialogTarget.querySelectorAll(FOCUSABLE_SELECTOR)
    );

    if (focusableElements.length === 0) {
      event.preventDefault();
      this.onboardingDialogTarget.focus();
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

  focusInitialOnboardingField() {
    if (!this.hasOnboardingInitialFocusTarget) {
      this.focusOnboardingDialog();
      return;
    }

    const field = this.onboardingInitialFocusTarget.querySelector(FOCUSABLE_SELECTOR);
    if (field) {
      field.focus();
    } else {
      this.focusOnboardingDialog();
    }
  }

  lockOnboardingBackground() {
    this.releaseOnboardingBackground();

    if (!this.hasOnboardingModalTarget) {
      return;
    }

    const overlayElement = this.hasOnboardingOverlayTarget ? this.onboardingOverlayTarget : null;
    let activeBranch = this.onboardingModalTarget;

    while (activeBranch?.parentElement) {
      const parent = activeBranch.parentElement;
      Array.from(parent.children).forEach((element) => {
        if (element === activeBranch || element === overlayElement) {
          return;
        }

        this.inertElement(element);
      });

      if (parent === document.body) {
        break;
      }

      activeBranch = parent;
    }
  }

  releaseOnboardingBackground() {
    this.inertedElements.forEach((element) => {
      element.inert = false;
    });
    this.inertedElements = [];
  }

  inertElement(element) {
    if (!(element instanceof HTMLElement) || element.inert) {
      return;
    }

    element.inert = true;
    this.inertedElements.push(element);
  }

  focusOnboardingDialog() {
    if (this.hasOnboardingDialogTarget) {
      this.onboardingDialogTarget.focus();
    }
  }

  getCsrfToken() {
    return document.querySelector("[name=csrfmiddlewaretoken]").value;
  }

  shouldSkipOnboarding() {
    try {
      return localStorage.getItem("skipOnboarding") === "true";
    } catch (error) {
      return false;
    }
  }

  setSkipOnboarding() {
    try {
      localStorage.setItem("skipOnboarding", "true");
    } catch (error) {
      // Ignore localStorage errors.
    }
  }
}
