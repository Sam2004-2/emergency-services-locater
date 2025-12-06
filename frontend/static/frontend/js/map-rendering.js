// Marker and cluster rendering functions

import { icons } from './icons.js';
import { state } from './map-state.js';

export function unwrapCollection(data) {
  if (!data) {
    return { type: 'FeatureCollection', features: [] };
  }
  if (data.type === 'FeatureCollection') {
    return data;
  }
  if (Array.isArray(data.features)) {
    return { type: 'FeatureCollection', features: data.features };
  }
  if (data.results && data.results.type === 'FeatureCollection') {
    return data.results;
  }
  return { type: 'FeatureCollection', features: [] };
}

function popupHtml(feature) {
  const props = feature.properties || {};
  const meta = props.properties || {};
  const phone = props.phone ? `<div>☎ ${props.phone}</div>` : '';
  const website = props.website
    ? `<div>🔗 <a href="${props.website}" target="_blank" rel="noopener">Website</a></div>`
    : '';
  return `
    <div class="fw-semibold">${props.name}</div>
    <div class="text-muted small mb-1">${(props.type || '').replace('_', ' ')}</div>
    <div class="small">${props.address || ''}</div>
    ${phone}${website}
    ${meta.ae ? '<span class="badge bg-success mt-1">A&amp;E</span>' : ''}
  `;
}

function featureToMarker(feature, latlng) {
  const type = feature.properties?.type || 'default';
  return L.marker(latlng, { icon: icons[type] || icons.default }).bindPopup(popupHtml(feature));
}

export function clearMarkers() {
  if (state.cluster) {
    state.map.removeLayer(state.cluster);
  }
  state.cluster = L.markerClusterGroup({ chunkedLoading: true });
  state.map.addLayer(state.cluster);
}

export function renderFacilities(payload, { fit = false } = {}) {
  const collection = unwrapCollection(payload);
  clearMarkers();
  const layer = L.geoJSON(collection, { pointToLayer: featureToMarker });
  state.cluster.addLayer(layer);
  if (fit && layer.getLayers().length) {
    state.map.fitBounds(layer.getBounds(), { padding: [20, 20] });
  }
  return collection.features.length;
}

export function resetRadiusOverlay() {
  if (state.radiusOverlay) {
    state.map.removeLayer(state.radiusOverlay);
    state.radiusOverlay = null;
  }
}
