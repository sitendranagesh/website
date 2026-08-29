/**
 * Sitendra Platform Theme Engine (Light & Dark Mode Switcher)
 * Fast, flicker-free theme initialization with localStorage persistence and OS preference sync.
 */

(function() {
  // 1. Detect & Apply Initial Theme Instantly (Default to Elegant Light Mode)
  const savedTheme = localStorage.getItem("sitendra_theme");
  const initialTheme = savedTheme ? savedTheme : "light";

  document.documentElement.setAttribute("data-theme", initialTheme);

  // 2. Helper to Toggle Theme
  window.toggleSitendraTheme = function() {
    const currentTheme = document.documentElement.getAttribute("data-theme") || "dark";
    const newTheme = currentTheme === "dark" ? "light" : "dark";

    document.documentElement.setAttribute("data-theme", newTheme);
    localStorage.setItem("sitendra_theme", newTheme);

    updateThemeIcons(newTheme);
  };

  function updateThemeIcons(theme) {
    document.querySelectorAll(".theme-toggle-btn").forEach(btn => {
      if (theme === "light") {
        btn.innerHTML = `<span class="theme-icon">🌙</span><span class="theme-label" style="display: none;">Dark</span>`;
        btn.setAttribute("title", "Switch to Dark Mode");
        btn.setAttribute("aria-label", "Switch to Dark Mode");
      } else {
        btn.innerHTML = `<span class="theme-icon">☀️</span><span class="theme-label" style="display: none;">Light</span>`;
        btn.setAttribute("title", "Switch to Light Mode");
        btn.setAttribute("aria-label", "Switch to Light Mode");
      }
    });
  }

  // 3. Attach Listeners When DOM Ready
  document.addEventListener("DOMContentLoaded", () => {
    const currentTheme = document.documentElement.getAttribute("data-theme") || "dark";
    updateThemeIcons(currentTheme);

    document.querySelectorAll(".theme-toggle-btn").forEach(btn => {
      btn.addEventListener("click", window.toggleSitendraTheme);
    });
  });

  // 4. Listen to OS Theme Changes if user hasn't set explicit preference
  if (window.matchMedia) {
    window.matchMedia("(prefers-color-scheme: light)").addEventListener("change", (e) => {
      if (!localStorage.getItem("sitendra_theme")) {
        const osTheme = e.matches ? "light" : "dark";
        document.documentElement.setAttribute("data-theme", osTheme);
        updateThemeIcons(osTheme);
      }
    });
  }
})();
