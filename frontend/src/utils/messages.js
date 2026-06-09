// static/js/utils/messages.js
export function showMessage(message, type = 'error') {
  const messagesContainer = document.querySelector('.messages-container') || createMessagesContainer();

  const messageId = Date.now();
  const messageHTML = `
    <div data-reveal-target="item" data-message-id="${messageId}" class="pf-panel max-w-sm p-4 opacity-0 transition-all duration-300 ease-in-out translate-x-full ${type === 'error' ? 'border-[oklch(0.86_0.08_25)]' : 'border-[oklch(0.84_0.09_145)]'}">
      <div class="flex items-start">
        <div class="mr-3 flex-shrink-0">
          <svg class="h-5 w-5" viewBox="0 0 24 24">
            <circle class="text-[var(--pf-line)]" stroke-width="2" stroke="currentColor" fill="transparent" r="10" cx="12" cy="12"/>
            <circle class="${type === 'error' ? 'text-[var(--pf-danger)]' : 'text-[var(--pf-brand-dark)]'}" stroke-width="2" stroke="currentColor" fill="transparent" r="10" cx="12" cy="12" data-timer-circle/>
          </svg>
        </div>
        <div class="flex-grow">
          <p class="text-sm font-semibold ${type === 'error' ? 'text-[var(--pf-danger)]' : 'text-[color:var(--pf-ink)]'}">
            ${message}
          </p>
        </div>
        <div class="ml-3 flex-shrink-0">
          <button onclick="this.closest('[data-reveal-target=item]').remove()" type="button" class="inline-flex h-6 w-6 items-center justify-center rounded-md text-[color:var(--pf-muted)] hover:text-[color:var(--pf-ink)]">
            <span class="sr-only">Dismiss</span>
            <svg class="h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  `;

  messagesContainer.insertAdjacentHTML('beforeend', messageHTML);

  const messageElement = document.querySelector(`[data-message-id="${messageId}"]`);
  setTimeout(() => {
    messageElement.classList.remove('opacity-0', 'translate-x-full');
    startTimer(messageElement);
  }, 100);
}

function createMessagesContainer() {
  const container = document.createElement('div');
  container.className = 'fixed right-4 top-4 z-50 space-y-3 messages-container';
  document.body.appendChild(container);
  return container;
}

function startTimer(item) {
  const timerCircle = item.querySelector('[data-timer-circle]');
  const radius = 10;
  const circumference = 2 * Math.PI * radius;

  timerCircle.style.strokeDasharray = `${circumference} ${circumference}`;
  timerCircle.style.strokeDashoffset = circumference;

  let progress = 0;
  const interval = setInterval(() => {
    if (progress >= 100) {
      clearInterval(interval);
      hideMessage(item);
    } else {
      progress++;
      const offset = circumference - (progress / 100) * circumference;
      timerCircle.style.strokeDashoffset = offset;
    }
  }, 50);
}

function hideMessage(item) {
  item.classList.add('opacity-0', 'translate-x-full');
  setTimeout(() => {
    item.remove();
  }, 300);
}
