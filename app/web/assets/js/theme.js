// Light or dark: the visitor's choice if they made one, otherwise their system setting. Loaded in <head> (not as a
// module) so the page is painted in the right theme from the start.
(() => {
  const root = document.documentElement;
  const KEY = "herbar-theme";
  try {
    const stored = localStorage.getItem(KEY);
    if (stored === "light" || stored === "dark") root.dataset.theme = stored;
  } catch { /* storage unavailable: follow the system */ }
  const system = matchMedia("(prefers-color-scheme: light)");
  const current = () => root.dataset.theme || (system.matches ? "light" : "dark");
  const paint = () => {
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.content = current() === "light" ? "#f6f5f0" : "#121614";
  };
  document.addEventListener("DOMContentLoaded", () => {
    const button = document.querySelector("[data-theme-toggle]");
    const label = () => {
      if (!button) return;
      const next = current() === "light" ? "dark" : "light";
      button.dataset.next = next;
      button.setAttribute("aria-label", `Switch to the ${next} theme`);
      button.title = `Switch to the ${next} theme`;
    };
    paint();
    label();
    system.addEventListener("change", () => { paint(); label(); });
    if (!button) return;
    button.hidden = false;
    button.addEventListener("click", () => {
      root.dataset.theme = current() === "light" ? "dark" : "light";
      try { localStorage.setItem(KEY, root.dataset.theme); } catch { /* the choice lasts for this page only */ }
      paint();
      label();
    });
  });
})();
