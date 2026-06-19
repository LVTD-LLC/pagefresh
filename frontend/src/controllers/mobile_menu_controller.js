import { Controller } from "@hotwired/stimulus";

export default class extends Controller {
  static targets = ["button", "menu"];

  connect() {
    this.close();
  }

  toggle(event) {
    event.preventDefault();
    event.stopPropagation();

    if (this.isOpen) {
      this.close();
    } else {
      this.open();
    }
  }

  open() {
    this.isOpen = true;
    this.buttonTarget.setAttribute("aria-expanded", "true");
    this.menuTarget.classList.remove("hidden");
  }

  close() {
    if (!this.hasButtonTarget || !this.hasMenuTarget) {
      return;
    }

    this.isOpen = false;
    this.buttonTarget.setAttribute("aria-expanded", "false");
    this.menuTarget.classList.add("hidden");
  }

  closeOnOutside(event) {
    if (this.isOpen && !this.element.contains(event.target)) {
      this.close();
    }
  }

  closeOnEscape(event) {
    if (!this.isOpen || event.key !== "Escape") {
      return;
    }

    event.preventDefault();
    this.close();
    this.buttonTarget.focus();
  }
}
