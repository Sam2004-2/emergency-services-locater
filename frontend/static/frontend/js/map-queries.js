// Query functions for facilities

import API from './api.js';
import { $, status, kmToM, state } from './map-state.js';
import { renderFacilities, resetRadiusOverlay } from './map-rendering.js';
import { locateUser } from './map-interactions.js';
import { themeColors } from './theme-config.js';

export async function queryNearest() {
  try {
    const type = $('#type')?.value || undefined;
    if (!state.userLatLng) {
      await locateUser(true);
    }
    if (!state.userLatLng) return;
    const { lat, lng } = state.userLatLng;
    status('Finding nearest facilities…');
    const data = await API.nearest({ lat, lon: lng, limit: 5, type });
    const count = renderFacilities(data, { fit: true });
    status(count ? `Found ${count} nearest facilities.` : 'No facilities found.');
    resetRadiusOverlay();
  } catch (error) {
    console.error(error);
    status('Nearest query failed.');
  }
}

export async function queryWithinRadius() {
  try {
    const type = $('#type')?.value || undefined;
    if (!state.userLatLng) {
      await locateUser(true);
    }
    if (!state.userLatLng) return;
    const { lat, lng } = state.userLatLng;
    const radiusKm = $('#radius')?.value || 10;
    status(`Searching within ${radiusKm} km…`);
    const data = await API.withinRadius({
      lat,
      lon: lng,
      radius_m: kmToM(radiusKm),
      type,
    });
    const count = renderFacilities(data, { fit: true });
    resetRadiusOverlay();
    if (state.userLatLng) {
      state.radiusOverlay = L.circle(state.userLatLng, {
        radius: kmToM(radiusKm),
        color: themeColors.primary,
        weight: 1,
      }).addTo(state.map);
    }
    status(count ? `Showing ${count} facilities within ${radiusKm} km.` : 'No facilities found within radius.');
  } catch (error) {
    console.error(error);
    status('Radius query failed.');
  }
}

export async function queryWithinCounty() {
  const id = $('#countySelect')?.value;
  const type = $('#type')?.value || undefined;
  if (!id) {
    status('Select a county to filter.');
    return;
  }
  try {
    status('Filtering by county…');
    const data = await API.withinCounty({ id, type });
    const count = renderFacilities(data, { fit: true });
    resetRadiusOverlay();
    status(count ? 'Showing facilities within county.' : 'No facilities found in selected county.');
  } catch (error) {
    console.error(error);
    status('County query failed.');
  }
}
