"""
OSRM routing service for calculating routes between points.

Uses the free OSRM demo server for routing calculations.
For production, consider self-hosting OSRM or using a paid service.
"""
import logging
from typing import Any

import requests
from django.contrib.gis.geos import LineString, Point

logger = logging.getLogger(__name__)

OSRM_BASE_URL = "https://router.project-osrm.org/route/v1/driving"
REQUEST_TIMEOUT = 10  # seconds


class OSRMService:
    """
    Client for OSRM (Open Source Routing Machine) API.

    Provides routing between geographic points with distance and
    duration estimates, plus detailed route geometry.
    """

    @staticmethod
    def get_route(
        origin: Point,
        destination: Point,
        alternatives: bool = False
    ) -> dict[str, Any] | None:
        """
        Get driving route between two points.

        Args:
            origin: Starting point (GEOS Point with SRID 4326)
            destination: End point (GEOS Point with SRID 4326)
            alternatives: Include alternative routes

        Returns:
            Dict with 'geometry' (LineString), 'distance' (meters),
            'duration' (seconds), or None if routing fails
        """
        # OSRM expects lon,lat order
        coords = f"{origin.x},{origin.y};{destination.x},{destination.y}"
        url = f"{OSRM_BASE_URL}/{coords}"

        params = {
            'overview': 'full',
            'geometries': 'geojson',
            'alternatives': 'true' if alternatives else 'false',
        }

        try:
            response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            if data.get('code') != 'Ok' or not data.get('routes'):
                logger.warning("OSRM returned no routes: %s", data.get('code'))
                return None

            route = data['routes'][0]
            geometry = LineString(
                route['geometry']['coordinates'],
                srid=4326
            )

            return {
                'geometry': geometry,
                'distance': route['distance'],  # meters
                'duration': route['duration'],  # seconds
            }

        except requests.Timeout:
            logger.error("OSRM request timed out")
            return None
        except requests.RequestException as e:
            logger.error("OSRM request failed: %s", e)
            return None
        except (KeyError, ValueError) as e:
            logger.error("Failed to parse OSRM response: %s", e)
            return None

    @staticmethod
    def get_route_for_incident(incident, from_vehicle: bool = True) -> dict[str, Any] | None:
        """
        Get route to an incident from assigned vehicle or nearest facility.

        Args:
            incident: Incident model instance
            from_vehicle: If True, route from assigned vehicle; else from facility

        Returns:
            Route dict or None if no origin available
        """
        destination = incident.location

        # Try to get origin from assigned vehicle
        if from_vehicle and incident.assigned_vehicles.exists():
            vehicle = incident.assigned_vehicles.first()
            origin = vehicle.current_position
        # Fall back to nearest facility
        elif incident.nearest_facility:
            origin = incident.nearest_facility.geom
        else:
            logger.warning("No origin available for incident %s", incident.id)
            return None

        return OSRMService.get_route(origin, destination)

    @staticmethod
    def update_incident_route(incident) -> bool:
        """
        Calculate and cache route for an incident.

        Args:
            incident: Incident model instance to update

        Returns:
            True if route was updated, False otherwise
        """
        route_data = OSRMService.get_route_for_incident(incident)
        if route_data:
            incident.route_geometry = route_data['geometry']
            incident.route_distance_m = route_data['distance']
            incident.route_duration_s = route_data['duration']
            incident.save(update_fields=[
                'route_geometry', 'route_distance_m', 'route_duration_s'
            ])
            return True
        return False

    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format duration in seconds to human-readable string."""
        minutes = int(seconds / 60)
        if minutes < 60:
            return f"{minutes} min"
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours}h {mins}m"

    @staticmethod
    def format_distance(meters: float) -> str:
        """Format distance in meters to human-readable string."""
        if meters < 1000:
            return f"{int(meters)} m"
        km = meters / 1000
        return f"{km:.1f} km"
