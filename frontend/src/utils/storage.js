/**
 * Utility functions for sessionStorage with TTL support
 */

const DEFAULT_TTL = 1000 * 60 * 15; // 15 minutes

/**
 * Set item in sessionStorage with optional TTL
 * @param {string} key - Storage key
 * @param {any} value - Value to store
 * @param {number} ttl - Time to live in milliseconds
 */
export function setSessionItem(key, value, ttl = DEFAULT_TTL) {
  const item = {
    value,
    timestamp: Date.now(),
    ttl,
  };
  sessionStorage.setItem(key, JSON.stringify(item));
}

/**
 * Get item from sessionStorage, returns null if expired
 * @param {string} key - Storage key
 * @returns {any} - Stored value or null
 */
export function getSessionItem(key) {
  try {
    const itemStr = sessionStorage.getItem(key);
    if (!itemStr) return null;

    const item = JSON.parse(itemStr);
    const now = Date.now();

    // Check if expired
    if (now - item.timestamp > item.ttl) {
      sessionStorage.removeItem(key);
      return null;
    }

    return item.value;
  } catch (error) {
    console.error(`Error reading sessionStorage key "${key}":`, error);
    return null;
  }
}

/**
 * Remove item from sessionStorage
 * @param {string} key - Storage key
 */
export function removeSessionItem(key) {
  sessionStorage.removeItem(key);
}

/**
 * Clear all expired items from sessionStorage
 */
export function cleanupSessionStorage() {
  const keys = Object.keys(sessionStorage);
  keys.forEach((key) => {
    getSessionItem(key); // This will auto-remove if expired
  });
}
