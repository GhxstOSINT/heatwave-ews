(() => {
  const key = "heatsafe-theme";
  const media = window.matchMedia("(prefers-color-scheme: dark)");
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const readPreference = () => {
    try { return localStorage.getItem(key); } catch { return null; }
  };
  const current = () => document.documentElement.dataset.theme === "dark" ? "dark" : "light";
  const apply = (theme) => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;
    document.dispatchEvent(new CustomEvent("heatsafe:theme", { detail: theme }));
  };
  apply(readPreference() === "dark" ? "dark" : readPreference() === "light" ? "light" : media.matches ? "dark" : "light");
  document.documentElement.classList.add("page-enter");

  const makeIcon = (theme) => {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("fill", "none");
    svg.setAttribute("stroke", "currentColor");
    svg.setAttribute("stroke-width", "1.8");
    svg.setAttribute("stroke-linecap", "round");
    svg.setAttribute("aria-hidden", "true");
    if (theme === "dark") {
      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute("d", "M20.5 14.2A8.6 8.6 0 0 1 9.8 3.5a8.7 8.7 0 1 0 10.7 10.7Z");
      svg.append(path);
    } else {
      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("cx", "12");
      circle.setAttribute("cy", "12");
      circle.setAttribute("r", "3.5");
      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute("d", "M12 2v2m0 16v2M4.9 4.9l1.4 1.4m11.4 11.4 1.4 1.4M2 12h2m16 0h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4");
      svg.append(circle, path);
    }
    return svg;
  };
  let toggle;
  const renderToggle = () => {
    if (!toggle) return;
    const dark = current() === "dark";
    const label = document.createElement("span");
    label.textContent = dark ? "Light mode" : "Dark mode";
    toggle.replaceChildren(makeIcon(dark ? "light" : "dark"), label);
    toggle.setAttribute("aria-label", `Switch to ${dark ? "light" : "dark"} mode`);
    toggle.setAttribute("aria-pressed", String(dark));
  };
  const mountToggle = () => {
    const slot = document.getElementById("heatsafe-theme-slot");
    if (!slot || toggle) return Boolean(toggle);
    toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "heatsafe-theme-toggle";
    toggle.addEventListener("click", () => {
      const next = current() === "dark" ? "light" : "dark";
      try { localStorage.setItem(key, next); } catch { /* The choice still works for this page. */ }
      apply(next);
    });
    slot.append(toggle);
    renderToggle();
    return true;
  };
  document.addEventListener("heatsafe:theme", renderToggle);
  media.addEventListener("change", () => { if (!readPreference()) apply(media.matches ? "dark" : "light"); });
  window.addEventListener("storage", (event) => {
    if (event.key === key) apply(event.newValue === "dark" ? "dark" : event.newValue === "light" ? "light" : media.matches ? "dark" : "light");
  });
  const observeToggle = () => {
    if (mountToggle()) return;
    const observer = new MutationObserver(() => { if (mountToggle()) observer.disconnect(); });
    observer.observe(document.body, { childList: true, subtree: true });
  };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", observeToggle, { once: true });
  else observeToggle();

  const navigate = (url, replace = false) => {
    if (document.documentElement.classList.contains("page-leaving")) return;
    if (reducedMotion.matches) { window.location[replace ? "replace" : "assign"](url); return; }
    document.documentElement.classList.add("page-leaving");
    window.setTimeout(() => window.location[replace ? "replace" : "assign"](url), 170);
  };
  window.HeatSafeUI = { navigate };
  document.addEventListener("click", (event) => {
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const link = event.target instanceof Element ? event.target.closest("a[href]") : null;
    if (link?.closest(".heatsafe-mobile-nav")) {
      const menu = link.closest("details");
      if (menu) menu.open = false;
    }
    if (!link || link.target && link.target !== "_self" || link.hasAttribute("download")) return;
    const url = new URL(link.href, window.location.href);
    if (url.origin !== window.location.origin || !/^\/(?:landing|login|signup|dashboard)\.html$/.test(url.pathname)) return;
    if (url.pathname === window.location.pathname && url.search === window.location.search && url.hash) return;
    event.preventDefault();
    navigate(url.href);
  });
  window.addEventListener("pageshow", () => document.documentElement.classList.remove("page-leaving"));
})();
