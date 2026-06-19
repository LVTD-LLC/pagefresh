export function showMessage(message, type = "error") {
  const messagesContainer =
    document.querySelector(".messages-container") || createMessagesContainer();
  const messageElement = createMessageElement(message, type);

  messagesContainer.appendChild(messageElement);
}

function createMessagesContainer() {
  const container = document.createElement("div");
  container.className = "fixed right-4 top-4 z-50 space-y-3 messages-container";
  container.setAttribute("aria-live", "polite");
  container.setAttribute("aria-atomic", "false");
  document.body.appendChild(container);

  return container;
}

function createMessageElement(message, type) {
  const isError = type === "error";
  const messageId = String(Date.now());
  const item = document.createElement("div");
  item.dataset.controller = "message";
  item.dataset.messageId = messageId;
  item.setAttribute("role", isError ? "alert" : "status");
  item.setAttribute("aria-live", isError ? "assertive" : "polite");
  item.dataset.action = [
    "mouseenter->message#pause",
    "mouseleave->message#resume",
    "focusin->message#pause",
    "focusout->message#resume",
  ].join(" ");
  item.className = [
    "pf-panel",
    "max-w-sm",
    "p-4",
    "opacity-0",
    "transition-all",
    "duration-300",
    "ease-out",
    "translate-x-full",
    isError ? "border-[oklch(0.86_0.08_25)]" : "border-[oklch(0.84_0.09_145)]",
  ].join(" ");

  const row = document.createElement("div");
  row.className = "flex items-start";

  const iconWrap = document.createElement("div");
  iconWrap.className = "mr-3 flex-shrink-0";
  iconWrap.appendChild(createTimerIcon(isError));

  const content = document.createElement("div");
  content.className = "flex-grow";

  const text = document.createElement("p");
  text.className = [
    "text-sm",
    "font-semibold",
    isError ? "text-[var(--pf-danger)]" : "text-[color:var(--pf-ink)]",
  ].join(" ");
  text.textContent = message;
  content.appendChild(text);

  const action = document.createElement("div");
  action.className = "ml-3 flex-shrink-0";
  action.appendChild(createDismissButton());

  row.append(iconWrap, content, action);
  item.appendChild(row);

  return item;
}

function createTimerIcon(isError) {
  const svg = createSvgElement("svg");
  svg.setAttribute("class", "h-5 w-5");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("aria-hidden", "true");

  const baseCircle = createSvgElement("circle");
  baseCircle.setAttribute("class", "text-[var(--pf-line)]");
  baseCircle.setAttribute("stroke-width", "2");
  baseCircle.setAttribute("stroke", "currentColor");
  baseCircle.setAttribute("fill", "transparent");
  baseCircle.setAttribute("r", "10");
  baseCircle.setAttribute("cx", "12");
  baseCircle.setAttribute("cy", "12");

  const progressCircle = createSvgElement("circle");
  progressCircle.setAttribute(
    "class",
    isError ? "text-[var(--pf-danger)]" : "text-[var(--pf-brand-dark)]"
  );
  progressCircle.setAttribute("stroke-width", "2");
  progressCircle.setAttribute("stroke", "currentColor");
  progressCircle.setAttribute("fill", "transparent");
  progressCircle.setAttribute("r", "10");
  progressCircle.setAttribute("cx", "12");
  progressCircle.setAttribute("cy", "12");
  progressCircle.dataset.messageTarget = "timerCircle";

  svg.append(baseCircle, progressCircle);

  return svg;
}

function createDismissButton() {
  const button = document.createElement("button");
  button.type = "button";
  button.dataset.action = "click->message#dismiss";
  button.className = [
    "inline-flex",
    "min-h-11",
    "min-w-11",
    "items-center",
    "justify-center",
    "rounded-md",
    "text-[color:var(--pf-muted)]",
    "hover:text-[color:var(--pf-ink)]",
    "focus:outline-none",
    "focus:ring-2",
    "focus:ring-[color:var(--pf-brand)]",
    "focus:ring-offset-2",
  ].join(" ");

  const label = document.createElement("span");
  label.className = "sr-only";
  label.textContent = "Dismiss";

  const svg = createSvgElement("svg");
  svg.setAttribute("class", "h-4 w-4");
  svg.setAttribute("fill", "none");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("stroke", "currentColor");
  svg.setAttribute("aria-hidden", "true");

  const path = createSvgElement("path");
  path.setAttribute("stroke-linecap", "round");
  path.setAttribute("stroke-linejoin", "round");
  path.setAttribute("stroke-width", "2");
  path.setAttribute("d", "M6 18L18 6M6 6l12 12");
  svg.appendChild(path);

  button.append(label, svg);

  return button;
}

function createSvgElement(name) {
  return document.createElementNS("http://www.w3.org/2000/svg", name);
}
