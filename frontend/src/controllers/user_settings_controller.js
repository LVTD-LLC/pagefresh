import { Controller } from "@hotwired/stimulus";

export default class extends Controller {
  connect() {
    this.fetchAndStoreSettings();
  }

  async fetchAndStoreSettings() {
    try {
      const response = await fetch("/api/user/settings");
      if (!response.ok) {
        return;
      }
      const data = await response.json();

      localStorage.setItem("userSettings", JSON.stringify(data));

    } catch {
      return;
    }
  }
}
