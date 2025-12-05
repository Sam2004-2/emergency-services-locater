/**
 * Routing Service for OSRM Integration
 * 
 * Provides route calculation and display on Leaflet maps.
 */

class RoutingService {
    constructor(map, options = {}) {
        this.map = map;
        this.osrmUrl = options.osrmUrl || 'https://router.project-osrm.org';
        this.apiUrl = options.apiUrl || '/api';
        this.routeLayer = null;
        this.markerLayer = null;
        this.currentRoute = null;
        
        // Route styling
        this.routeStyles = {
            default: { color: '#2196F3', weight: 5, opacity: 0.8 },
            active: { color: '#4CAF50', weight: 6, opacity: 0.9 },
            emergency: { color: '#f44336', weight: 6, opacity: 0.9 },
            alternative: { color: '#9E9E9E', weight: 4, opacity: 0.6 }
        };
    }

    /**
     * Calculate route using server-side OSRM integration
     */
    async calculateRoute(origin, destination, options = {}) {
        try {
            const response = await fetch(`${this.apiUrl}/routing/calculate/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    origin: {
                        lat: origin.lat,
                        lng: origin.lng
                    },
                    destination: {
                        lat: destination.lat,
                        lng: destination.lng
                    },
                    ...options
                })
            });

            if (!response.ok) {
                throw new Error(`Route calculation failed: ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error calculating route:', error);
            throw error;
        }
    }

    /**
     * Calculate route directly from OSRM (client-side)
     */
    async calculateRouteOSRM(origin, destination, options = {}) {
        const profile = options.profile || 'driving';
        const coords = `${origin.lng},${origin.lat};${destination.lng},${destination.lat}`;
        const url = `${this.osrmUrl}/route/v1/${profile}/${coords}?overview=full&geometries=geojson&steps=true`;

        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`OSRM request failed: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.code !== 'Ok' || !data.routes || data.routes.length === 0) {
                throw new Error('No route found');
            }

            return {
                route: data.routes[0],
                geometry: data.routes[0].geometry,
                distance: data.routes[0].distance,
                duration: data.routes[0].duration,
                legs: data.routes[0].legs
            };
        } catch (error) {
            console.error('Error calculating OSRM route:', error);
            throw error;
        }
    }

    /**
     * Display route on map
     */
    displayRoute(routeData, options = {}) {
        // Clear existing route
        this.clearRoute();

        const style = options.style || 'default';
        const routeStyle = { ...this.routeStyles[style], ...options.customStyle };

        // Create route layer
        if (routeData.geometry) {
            this.routeLayer = L.geoJSON(routeData.geometry, {
                style: () => routeStyle
            }).addTo(this.map);
        } else if (routeData.route && routeData.route.geometry) {
            this.routeLayer = L.geoJSON(routeData.route.geometry, {
                style: () => routeStyle
            }).addTo(this.map);
        }

        // Add markers if requested
        if (options.showMarkers) {
            this.addRouteMarkers(routeData, options);
        }

        // Fit map to route
        if (options.fitBounds && this.routeLayer) {
            this.map.fitBounds(this.routeLayer.getBounds(), { padding: [50, 50] });
        }

        this.currentRoute = routeData;
        return this.routeLayer;
    }

    /**
     * Add markers at route endpoints
     */
    addRouteMarkers(routeData, options = {}) {
        this.markerLayer = L.layerGroup().addTo(this.map);

        const coords = routeData.geometry?.coordinates || 
                       routeData.route?.geometry?.coordinates || [];

        if (coords.length >= 2) {
            // Origin marker
            const origin = L.marker([coords[0][1], coords[0][0]], {
                icon: this.createMarkerIcon('origin', options.originIcon)
            }).addTo(this.markerLayer);

            if (options.originLabel) {
                origin.bindPopup(options.originLabel);
            }

            // Destination marker
            const dest = L.marker([coords[coords.length - 1][1], coords[coords.length - 1][0]], {
                icon: this.createMarkerIcon('destination', options.destinationIcon)
            }).addTo(this.markerLayer);

            if (options.destinationLabel) {
                dest.bindPopup(options.destinationLabel);
            }
        }
    }

    /**
     * Create a marker icon
     */
    createMarkerIcon(type, customIcon) {
        if (customIcon) return customIcon;

        const colors = {
            origin: '#4CAF50',
            destination: '#f44336',
            waypoint: '#2196F3'
        };

        return L.divIcon({
            className: 'route-marker',
            html: `<div style="
                background-color: ${colors[type] || colors.waypoint};
                width: 24px;
                height: 24px;
                border-radius: 50%;
                border: 3px solid white;
                box-shadow: 0 2px 5px rgba(0,0,0,0.3);
            "></div>`,
            iconSize: [24, 24],
            iconAnchor: [12, 12]
        });
    }

    /**
     * Clear current route from map
     */
    clearRoute() {
        if (this.routeLayer) {
            this.map.removeLayer(this.routeLayer);
            this.routeLayer = null;
        }
        if (this.markerLayer) {
            this.map.removeLayer(this.markerLayer);
            this.markerLayer = null;
        }
        this.currentRoute = null;
    }

    /**
     * Find optimal vehicle assignment for an incident
     */
    async findOptimalAssignment(incidentId) {
        try {
            const response = await fetch(`${this.apiUrl}/routing/optimize_assignment/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    incident_id: incidentId
                })
            });

            if (!response.ok) {
                throw new Error(`Optimization failed: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error finding optimal assignment:', error);
            throw error;
        }
    }

    /**
     * Show route from vehicle to incident
     */
    async showVehicleToIncident(vehicleLocation, incidentLocation, options = {}) {
        try {
            const routeData = await this.calculateRouteOSRM(
                { lat: vehicleLocation[0], lng: vehicleLocation[1] },
                { lat: incidentLocation[0], lng: incidentLocation[1] }
            );

            return this.displayRoute(routeData, {
                style: 'emergency',
                showMarkers: true,
                fitBounds: true,
                originLabel: 'Vehicle Location',
                destinationLabel: 'Incident Location',
                ...options
            });
        } catch (error) {
            console.error('Error showing vehicle-to-incident route:', error);
            throw error;
        }
    }

    /**
     * Get route statistics
     */
    getRouteStats() {
        if (!this.currentRoute) return null;

        const route = this.currentRoute.route || this.currentRoute;
        return {
            distanceMeters: route.distance,
            distanceKm: (route.distance / 1000).toFixed(2),
            durationSeconds: route.duration,
            durationMinutes: Math.ceil(route.duration / 60),
            formattedDuration: this.formatDuration(route.duration),
            formattedDistance: this.formatDistance(route.distance)
        };
    }

    /**
     * Format duration in human-readable form
     */
    formatDuration(seconds) {
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const remainingMinutes = minutes % 60;

        if (hours > 0) {
            return `${hours}h ${remainingMinutes}m`;
        }
        return `${minutes}m`;
    }

    /**
     * Format distance in human-readable form
     */
    formatDistance(meters) {
        if (meters < 1000) {
            return `${Math.round(meters)}m`;
        }
        return `${(meters / 1000).toFixed(1)}km`;
    }

    /**
     * Get CSRF token from cookie
     */
    getCsrfToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}

// Export for modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RoutingService;
}
