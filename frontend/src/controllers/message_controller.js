import { Controller } from "@hotwired/stimulus";

const DISMISS_DURATION_MS = 7000;
const TICK_MS = 100;

export default class extends Controller {
  static targets = ["timerCircle"];
  static values = {
    delay: { type: Number, default: 100 },
  };

  connect() {
    this.dismissed = false;
    this.paused = false;
    this.startedAt = 0;
    this.elapsedBeforePause = 0;
    this.prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    this.reveal();

    if (!this.prefersReducedMotion) {
      this.startTimer();
    }
  }

  disconnect() {
    this.clearTimer();
  }

  pause() {
    if (!this.startedAt || this.paused) {
      return;
    }

    this.paused = true;
    this.elapsedBeforePause += Date.now() - this.startedAt;
    this.clearTimer();
  }

  resume() {
    if (!this.paused || this.dismissed || this.prefersReducedMotion) {
      return;
    }

    this.paused = false;
    this.startTimer();
  }

  dismiss() {
    this.dismissed = true;
    this.clearTimer();
    this.element.classList.add("opacity-0", "translate-x-full");

    window.setTimeout(() => {
      this.element.remove();
    }, this.prefersReducedMotion ? 0 : 300);
  }

  reveal() {
    window.setTimeout(() => {
      this.element.classList.remove("opacity-0", "translate-x-full");
    }, this.prefersReducedMotion ? 0 : this.delayValue);
  }

  startTimer() {
    this.startedAt = Date.now();
    this.interval = window.setInterval(() => {
      const elapsed = this.elapsedBeforePause + Date.now() - this.startedAt;
      const progress = Math.min(elapsed / DISMISS_DURATION_MS, 1);

      this.updateTimer(progress);

      if (progress >= 1) {
        this.dismiss();
      }
    }, TICK_MS);
  }

  updateTimer(progress) {
    if (!this.hasTimerCircleTarget) {
      return;
    }

    const radius = 10;
    const circumference = 2 * Math.PI * radius;
    this.timerCircleTarget.style.strokeDasharray = `${circumference} ${circumference}`;
    this.timerCircleTarget.style.strokeDashoffset = circumference - progress * circumference;
  }

  clearTimer() {
    if (this.interval) {
      window.clearInterval(this.interval);
      this.interval = null;
    }
  }
}
