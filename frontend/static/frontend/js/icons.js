const baseIcon = {
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
};

export const icons = {
  hospital: L.icon({ ...baseIcon, className: 'marker-hospital' }),
  fire_station: L.icon({ ...baseIcon, className: 'marker-fire_station' }),
  police_station: L.icon({ ...baseIcon, className: 'marker-police_station' }),
  ambulance_base: L.icon({ ...baseIcon, className: 'marker-ambulance_base' }),
  default: L.icon(baseIcon),
};
