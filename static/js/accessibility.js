/**
 * Gaming-Style Accessibility Options Manager
 *
 * This script applies user accessibility preferences from the server to the DOM.
 * It reads data attributes set by the template and applies corresponding CSS classes/attributes.
 */

(function() {
  'use strict';

  // Wait for DOM to be ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAccessibility);
  } else {
    initAccessibility();
  }

  function initAccessibility() {
    // Load accessibility preferences from data attributes on <html>
    const prefs = {
      highContrast: document.documentElement.getAttribute('data-a11y-high-contrast'),
      dyslexiaFont: document.documentElement.getAttribute('data-a11y-dyslexia'),
      fontSize: document.documentElement.getAttribute('data-a11y-font-size'),
      colorblind: document.documentElement.getAttribute('data-a11y-colorblind'),
      reducedMotion: document.documentElement.getAttribute('data-a11y-reduced-motion'),
      largeTargets: document.documentElement.getAttribute('data-a11y-large-targets'),
      keyboardHints: document.documentElement.getAttribute('data-a11y-keyboard-hints'),
      simplified: document.documentElement.getAttribute('data-a11y-simplified'),
      readingGuide: document.documentElement.getAttribute('data-a11y-reading-guide'),
      captions: document.documentElement.getAttribute('data-a11y-captions'),
      screenReader: document.documentElement.getAttribute('data-a11y-screen-reader'),
    };

    // Apply preferences to document
    applyAccessibilityPreferences(prefs);

    // Add skip link for keyboard navigation
    addSkipLink();

    // Add keyboard shortcut to toggle accessibility settings
    addAccessibilityShortcuts();

    // Log applied settings (for debugging)
    logAppliedSettings(prefs);
  }

  function applyAccessibilityPreferences(prefs) {
    const html = document.documentElement;

    // 1. High Contrast Mode
    if (prefs.highContrast === 'true') {
      html.setAttribute('data-a11y-high-contrast', 'true');
    }

    // 2. Dyslexia-Friendly Font
    if (prefs.dyslexiaFont === 'true') {
      html.setAttribute('data-a11y-dyslexia', 'true');
      // Load OpenDyslexic font if available
      loadDyslexicFont();
    }

    // 3. Font Size
    if (prefs.fontSize && prefs.fontSize !== 'normal') {
      html.setAttribute('data-a11y-font-size', prefs.fontSize);
    }

    // 4. Colorblind Mode
    if (prefs.colorblind && prefs.colorblind !== 'none') {
      html.setAttribute('data-a11y-colorblind', prefs.colorblind);
    }

    // 5. Reduced Motion
    if (prefs.reducedMotion === 'true') {
      html.setAttribute('data-a11y-reduced-motion', 'true');
    }

    // 6. Large Touch Targets
    if (prefs.largeTargets === 'true') {
      html.setAttribute('data-a11y-large-targets', 'true');
    }

    // 7. Keyboard Navigation Hints
    if (prefs.keyboardHints === 'true') {
      html.setAttribute('data-a11y-keyboard-hints', 'true');
      enableEnhancedKeyboardNav();
    }

    // 8. Simplified Layout
    if (prefs.simplified === 'true') {
      html.setAttribute('data-a11y-simplified', 'true');
    }

    // 9. Reading Guide
    if (prefs.readingGuide === 'true') {
      html.setAttribute('data-a11y-reading-guide', 'true');
    }

    // 10. Captions
    if (prefs.captions === 'true') {
      html.setAttribute('data-a11y-captions', 'true');
      showCaptions();
    }

    // 11. Screen Reader Mode
    if (prefs.screenReader === 'true') {
      html.setAttribute('data-a11y-screen-reader', 'true');
      optimizeForScreenReader();
    }

    // Apply prefers-reduced-motion media query
    applyReducedMotionPreference();
  }

  function loadDyslexicFont() {
    // Create style tag for OpenDyslexic font
    const fontLink = document.createElement('link');
    fontLink.rel = 'stylesheet';
    fontLink.href = 'https://fonts.googleapis.com/css2?family=OpenDyslexic&display=swap';
    fontLink.onerror = function() {
      // Fallback if CDN is not available
      console.warn('OpenDyslexic font failed to load, using system fallback');
    };
    document.head.appendChild(fontLink);
  }

  function enableEnhancedKeyboardNav() {
    // Show all focusable elements with keyboard navigation
    document.addEventListener('keydown', function(e) {
      // Alt + / to show keyboard shortcuts
      if (e.altKey && e.key === '/') {
        toggleKeyboardShortcutsOverlay();
      }

      // Tab through interactive elements
      if (e.key === 'Tab') {
        // Browser handles this natively, but we can enhance with visual feedback
        document.body.classList.add('keyboard-nav-active');
      }
    });

    document.addEventListener('mousedown', function() {
      document.body.classList.remove('keyboard-nav-active');
    });
  }

  function addSkipLink() {
    const skipLink = document.createElement('a');
    skipLink.href = '#main';
    skipLink.textContent = 'Skip to main content';
    skipLink.className = 'skip-to-main';
    skipLink.setAttribute('aria-label', 'Skip to main content');

    // Insert skip link at the beginning of body
    document.body.insertBefore(skipLink, document.body.firstChild);

    // Ensure main content has an ID
    const main = document.querySelector('main');
    if (main && !main.id) {
      main.id = 'main';
    }
  }

  function addAccessibilityShortcuts() {
    const shortcuts = {
      'alt+a': function() { openAccessibilitySettings(); },
      'alt+?': function() { toggleKeyboardShortcutsOverlay(); },
    };

    document.addEventListener('keydown', function(e) {
      if (e.altKey) {
        if (e.key.toLowerCase() === 'a') {
          e.preventDefault();
          openAccessibilitySettings();
        }
        if (e.key === '?') {
          e.preventDefault();
          toggleKeyboardShortcutsOverlay();
        }
      }
    });
  }

  function openAccessibilitySettings() {
    // Find and navigate to accessibility settings
    const a11yLink = document.querySelector('a[href*="/accessibility/"]');
    if (a11yLink) {
      window.location.href = a11yLink.href;
    } else {
      // Fallback: try common path
      window.location.href = '/u/accessibility/';
    }
  }

  function toggleKeyboardShortcutsOverlay() {
    let overlay = document.getElementById('keyboard-shortcuts-overlay');

    if (!overlay) {
      overlay = createKeyboardShortcutsOverlay();
      document.body.appendChild(overlay);
    }

    overlay.style.display = overlay.style.display === 'none' ? 'block' : 'none';
  }

  function createKeyboardShortcutsOverlay() {
    const overlay = document.createElement('div');
    overlay.id = 'keyboard-shortcuts-overlay';
    overlay.style.cssText = `
      position: fixed;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      background: white;
      border: 2px solid #000;
      padding: 2rem;
      border-radius: 8px;
      z-index: 9999;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
      max-height: 80vh;
      overflow-y: auto;
      display: none;
    `;

    overlay.innerHTML = `
      <h2 style="margin-top: 0;">Keyboard Shortcuts</h2>
      <dl style="margin: 0;">
        <dt><kbd>Tab</kbd></dt>
        <dd>Navigate through interactive elements</dd>

        <dt><kbd>Shift</kbd> + <kbd>Tab</kbd></dt>
        <dd>Navigate backwards</dd>

        <dt><kbd>Enter</kbd></dt>
        <dd>Activate buttons and links</dd>

        <dt><kbd>Space</kbd></dt>
        <dd>Toggle checkboxes and radio buttons</dd>

        <dt><kbd>Alt</kbd> + <kbd>A</kbd></dt>
        <dd>Open accessibility settings</dd>

        <dt><kbd>Alt</kbd> + <kbd>?</kbd></dt>
        <dd>Show this keyboard shortcuts overlay</dd>

        <dt><kbd>Escape</kbd></dt>
        <dd>Close this overlay</dd>
      </dl>
      <p style="margin: 1rem 0 0 0; font-size: 0.9em; color: #666;">
        Press <kbd>Escape</kbd> to close
      </p>
    `;

    overlay.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') {
        overlay.style.display = 'none';
      }
    });

    return overlay;
  }

  function applyReducedMotionPreference() {
    // Check for system prefers-reduced-motion setting
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

    function handleMotionPreference(matches) {
      if (matches) {
        document.documentElement.setAttribute('data-a11y-reduced-motion', 'true');
      }
    }

    // Check initial state
    handleMotionPreference(prefersReducedMotion.matches);

    // Listen for changes
    prefersReducedMotion.addEventListener('change', (e) => {
      handleMotionPreference(e.matches);
    });
  }

  function showCaptions() {
    // Enable captions on all video elements
    const videos = document.querySelectorAll('video');
    videos.forEach(video => {
      video.setAttribute('controls', '');
      if (!video.querySelector('track[kind="captions"]')) {
        const track = document.createElement('track');
        track.kind = 'captions';
        track.label = 'Captions';
        video.appendChild(track);
      }
    });
  }

  function optimizeForScreenReader() {
    // Ensure all interactive elements have proper ARIA labels
    document.querySelectorAll('button:not([aria-label]):not([title])').forEach(btn => {
      if (!btn.textContent.trim()) {
        btn.setAttribute('aria-label', 'Button');
      }
    });

    // Ensure form fields have labels
    document.querySelectorAll('input:not([aria-label]):not([aria-describedby])').forEach(input => {
      const label = document.querySelector(`label[for="${input.id}"]`);
      if (!label && !input.getAttribute('aria-label')) {
        input.setAttribute('aria-label', input.placeholder || 'Input field');
      }
    });
  }

  function logAppliedSettings(prefs) {
    const applied = Object.keys(prefs).filter(key => prefs[key] === 'true' || (prefs[key] && prefs[key] !== 'none' && prefs[key] !== 'normal'));
    if (applied.length > 0) {
      console.info('🎮 Gaming Accessibility Options Applied:', applied);
    }
  }

  // Expose global accessibility API for debugging/testing
  window.ShipTrackA11y = {
    openSettings: openAccessibilitySettings,
    showShortcuts: toggleKeyboardShortcutsOverlay,
    getPreferences: function() {
      return {
        highContrast: document.documentElement.getAttribute('data-a11y-high-contrast'),
        dyslexiaFont: document.documentElement.getAttribute('data-a11y-dyslexia'),
        fontSize: document.documentElement.getAttribute('data-a11y-font-size'),
        colorblind: document.documentElement.getAttribute('data-a11y-colorblind'),
        reducedMotion: document.documentElement.getAttribute('data-a11y-reduced-motion'),
        largeTargets: document.documentElement.getAttribute('data-a11y-large-targets'),
        keyboardHints: document.documentElement.getAttribute('data-a11y-keyboard-hints'),
        simplified: document.documentElement.getAttribute('data-a11y-simplified'),
        readingGuide: document.documentElement.getAttribute('data-a11y-reading-guide'),
        captions: document.documentElement.getAttribute('data-a11y-captions'),
        screenReader: document.documentElement.getAttribute('data-a11y-screen-reader'),
      };
    },
  };
})();
