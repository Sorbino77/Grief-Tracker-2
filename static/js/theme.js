/* ShipTrack — toggleable theme (light / dark / auto).
 * Loaded synchronously in <head> so the chosen theme is applied
 * before the page paints (no flash of wrong theme on dark-mode users).
 *
 * Persists the preference in localStorage. When the preference is "auto"
 * the resolved theme follows the OS (prefers-color-scheme) and updates
 * live when the OS preference changes.
 */
(function () {
  "use strict";

  var STORAGE_KEY = "shiptrack-theme";
  var ALLOWED = ["light", "dark", "auto"];

  function getStoredTheme() {
    try {
      var v = localStorage.getItem(STORAGE_KEY);
      return ALLOWED.indexOf(v) !== -1 ? v : null;
    } catch (e) {
      return null;
    }
  }

  function setStoredTheme(theme) {
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch (e) {
      /* Private mode / blocked storage — ignore. */
    }
  }

  function getPreferredTheme() {
    return getStoredTheme() || "auto";
  }

  function resolveTheme(theme) {
    if (theme === "auto") {
      var mql = window.matchMedia("(prefers-color-scheme: dark)");
      return mql.matches ? "dark" : "light";
    }
    return theme;
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-bs-theme", resolveTheme(theme));
  }

  function updateToggleUI(theme) {
    document.querySelectorAll("[data-theme-set]").forEach(function (el) {
      var on = el.dataset.themeSet === theme;
      el.classList.toggle("active", on);
      el.setAttribute("aria-pressed", on ? "true" : "false");
    });
    var label = document.getElementById("themeToggleLabel");
    if (label) {
      label.textContent = theme.charAt(0).toUpperCase() + theme.slice(1);
    }
    var icon = document.getElementById("themeToggleIcon");
    if (icon) {
      var resolved = resolveTheme(theme);
      icon.textContent = theme === "auto" ? "◐" : (resolved === "dark" ? "🌙" : "☀");
    }
  }

  // 1. Apply immediately so paint is correct on first frame.
  applyTheme(getPreferredTheme());

  // 2. Live-follow OS changes when the preference is "auto".
  var mql = window.matchMedia("(prefers-color-scheme: dark)");
  var onMqlChange = function () {
    if (getPreferredTheme() === "auto") {
      applyTheme("auto");
      updateToggleUI("auto");
    }
  };
  if (mql.addEventListener) {
    mql.addEventListener("change", onMqlChange);
  } else if (mql.addListener) {
    // Safari < 14
    mql.addListener(onMqlChange);
  }

  // 3. Wire up the dropdown after the DOM is parsed.
  document.addEventListener("DOMContentLoaded", function () {
    updateToggleUI(getPreferredTheme());
    document.querySelectorAll("[data-theme-set]").forEach(function (el) {
      el.addEventListener("click", function (e) {
        e.preventDefault();
        var theme = el.dataset.themeSet;
        if (ALLOWED.indexOf(theme) === -1) return;
        setStoredTheme(theme);
        applyTheme(theme);
        updateToggleUI(theme);
      });
    });
  });
})();
