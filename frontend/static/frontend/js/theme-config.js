/**
 * Theme Configuration Module
 * Provides JavaScript access to CSS custom properties for theme colors
 * Enables single source of truth for colors across CSS and JavaScript
 */

/**
 * Read a CSS custom property value from the root element
 * @param {string} varName - CSS variable name (e.g., '--color-primary')
 * @returns {string} - The computed color value
 */
export const getThemeColor = (varName) => {
  return getComputedStyle(document.documentElement)
    .getPropertyValue(varName)
    .trim();
};

/**
 * Theme colors with getters that auto-update when theme changes
 * Uses getters to ensure values are always current (light/dark mode switching)
 */
export const themeColors = {
  // Primary trust colors
  get primary() { return getThemeColor('--color-primary'); },
  get primaryLight() { return getThemeColor('--color-primary-light'); },
  get primaryDark() { return getThemeColor('--color-primary-dark'); },
  get primarySubtle() { return getThemeColor('--color-primary-subtle'); },

  // Emergency accent colors
  get emergency() { return getThemeColor('--color-emergency'); },
  get emergencyLight() { return getThemeColor('--color-emergency-light'); },
  get emergencySubtle() { return getThemeColor('--color-emergency-subtle'); },

  // Map neutral colors (theme-independent)
  get mapCountyBorder() { return getThemeColor('--map-county-border'); },
  get mapCountyFill() { return getThemeColor('--map-county-fill'); },
  get mapCountyHover() { return getThemeColor('--map-county-hover'); },
  get mapCountyActive() { return getThemeColor('--map-county-active'); },
  get mapTooltipBg() { return getThemeColor('--map-tooltip-bg'); },
  get mapTooltipText() { return getThemeColor('--map-tooltip-text'); },

  // Neutral colors
  get background() { return getThemeColor('--color-background'); },
  get surface() { return getThemeColor('--color-surface'); },
  get surfaceElevated() { return getThemeColor('--color-surface-elevated'); },
  get border() { return getThemeColor('--color-border'); },

  // Text colors
  get textPrimary() { return getThemeColor('--color-text-primary'); },
  get textSecondary() { return getThemeColor('--color-text-secondary'); },
  get textTertiary() { return getThemeColor('--color-text-tertiary'); },
  get textInverse() { return getThemeColor('--color-text-inverse'); },
};

/**
 * Listen for system theme changes (light/dark mode switching)
 * @param {Function} callback - Function to call when theme changes
 * @returns {Function} - Cleanup function to remove listener
 */
export const onThemeChange = (callback) => {
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

  // Call callback with initial state
  callback(mediaQuery.matches);

  // Listen for changes
  const listener = (e) => callback(e.matches);
  mediaQuery.addEventListener('change', listener);

  // Return cleanup function
  return () => mediaQuery.removeEventListener('change', listener);
};

/**
 * Check if dark mode is currently active
 * @returns {boolean} - True if dark mode is active
 */
export const isDarkMode = () => {
  return window.matchMedia('(prefers-color-scheme: dark)').matches;
};
