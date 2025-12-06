/**
 * Dashboard Polling Module
 * 
 * Automatically polls API for updates every 15 seconds
 */

import { DashboardAPI } from './dashboard-api.js';
import { DashboardState } from './dashboard-state.js';

let pollInterval = null;
const POLL_FREQUENCY = 15000; // 15 seconds

/**
 * Start polling
 */
export function startPolling() {
  if (pollInterval) return; // Already running

  // Initial fetch
  poll();

  // Set up interval
  pollInterval = setInterval(poll, POLL_FREQUENCY);
  console.log('Dashboard polling started');
}

/**
 * Stop polling
 */
export function stopPolling() {
  if (pollInterval) {
    clearInterval(pollInterval);
    pollInterval = null;
    console.log('Dashboard polling stopped');
  }
}

/**
 * Extract features array from various API response formats
 * Handles: GeoJSON, paginated GeoJSON, paginated arrays, plain arrays
 */
function extractFeatures(response) {
  if (!response) return [];
  
  // Paginated response: {count, next, previous, results}
  if (response.results !== undefined) {
    const results = response.results;
    // Paginated GeoJSON: results is a FeatureCollection
    if (results && results.features) {
      return results.features;
    }
    // Paginated array
    if (Array.isArray(results)) {
      return results;
    }
    return [];
  }
  
  // Direct GeoJSON: {type: "FeatureCollection", features: [...]}
  if (response.features) {
    return response.features;
  }
  
  // Plain array
  if (Array.isArray(response)) {
    return response;
  }
  
  return [];
}

/**
 * Poll for updates
 */
async function poll() {
  try {
    // Fetch incidents and vehicles in parallel
    const [incidents, vehicles] = await Promise.all([
      DashboardAPI.getActiveIncidents(),
      DashboardAPI.getVehicles()
    ]);

    // Update state - handle various response formats
    DashboardState.setIncidents(extractFeatures(incidents));
    DashboardState.setVehicles(extractFeatures(vehicles));
  } catch (error) {
    console.error('Polling error:', error);
    // Don't stop polling on error, just log it
  }
}

/**
 * Force immediate poll
 */
export function pollNow() {
  return poll();
}

/**
 * Check if polling is active
 */
export function isPolling() {
  return pollInterval !== null;
}
