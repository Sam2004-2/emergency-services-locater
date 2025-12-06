// State management and utility functions

export const state = {
  map: null,
  cluster: null,
  countyLayer: null,
  userLatLng: null,
  userMarker: null,
  radiusOverlay: null,
  dropPinMode: false,
};

export const $ = (selector) => document.querySelector(selector);

export const statusEl = () => $('#statusMsg');

export const status = (message) => {
  const el = statusEl();
  if (el) el.textContent = message;
};

export const kmToM = (km) => Math.round(Number(km) * 1000);
