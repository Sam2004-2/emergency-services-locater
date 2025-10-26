const API = {
  // Get CSRF token from meta tag
  getCSRFToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.content : '';
  },
  
  async counties() {
    const res = await fetch('/api/counties/?limit=200');
    if (!res.ok) throw new Error('Failed to load counties');
    return res.json();
  },
  async facilitiesList(params = {}) {
    const url = new URL('/api/facilities/', window.location.origin);
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== '') {
        url.searchParams.set(key, value);
      }
    });
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to load facilities');
    return res.json();
  },
  async withinRadius({ lat, lon, radius_m, type }) {
    const url = new URL('/api/facilities/within-radius/', window.location.origin);
    url.searchParams.set('lat', lat);
    url.searchParams.set('lon', lon);
    url.searchParams.set('radius_m', radius_m);
    if (type) url.searchParams.set('type', type);
    const res = await fetch(url);
    if (!res.ok) throw new Error('Radius query failed');
    return res.json();
  },
  async nearest({ lat, lon, limit = 5, type }) {
    const url = new URL('/api/facilities/nearest/', window.location.origin);
    url.searchParams.set('lat', lat);
    url.searchParams.set('lon', lon);
    url.searchParams.set('limit', limit);
    if (type) url.searchParams.set('type', type);
    const res = await fetch(url);
    if (!res.ok) throw new Error('Nearest query failed');
    return res.json();
  },
  async withinCounty({ id, name, type }) {
    const url = new URL('/api/facilities/within-county/', window.location.origin);
    if (id) url.searchParams.set('id', id);
    if (name) url.searchParams.set('name', name);
    if (type) url.searchParams.set('type', type);
    const res = await fetch(url);
    if (!res.ok) throw new Error('County query failed');
    return res.json();
  },
  async withinPolygon(geojson, type) {
    const body = { geometry: geojson.geometry };
    if (type) body.type = type;
    const res = await fetch('/api/facilities/within-polygon/', {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'X-CSRFToken': this.getCSRFToken(),
      },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error('Polygon query failed');
    return res.json();
  },
};

export default API;
