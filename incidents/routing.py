"""
Routing service integration for fastest-route calculation.

Supports OSRM (Open Source Routing Machine) for route calculation
with fallback to direct distance estimation.
"""
import logging
import requests
from dataclasses import dataclass
from typing import Optional, List, Tuple
from django.conf import settings
from django.contrib.gis.geos import Point, LineString


logger = logging.getLogger(__name__)


@dataclass
class RouteResult:
    """Result of a route calculation."""
    distance_m: float
    duration_s: float
    geometry: dict  # GeoJSON LineString
    instructions: List[dict] = None
    
    def to_dict(self):
        return {
            'distance_m': self.distance_m,
            'duration_s': self.duration_s,
            'geometry': self.geometry,
            'instructions': self.instructions or [],
        }


class RoutingService:
    """
    Routing service for calculating fastest routes between points.
    
    Uses OSRM by default, with fallback to direct distance calculation.
    """
    
    def __init__(self):
        self.osrm_url = getattr(settings, 'OSRM_URL', 'https://router.project-osrm.org')
        self.timeout = getattr(settings, 'ROUTING_TIMEOUT', 10)
    
    def calculate_route(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        vehicle_type: str = None
    ) -> Optional[RouteResult]:
        """
        Calculate the fastest route between two points.
        
        Args:
            origin: (latitude, longitude) of origin
            destination: (latitude, longitude) of destination
            vehicle_type: Optional vehicle type for profile selection
            
        Returns:
            RouteResult with distance, duration, geometry and instructions
        """
        try:
            return self._osrm_route(origin, destination, vehicle_type)
        except Exception as e:
            logger.warning(f"OSRM routing failed: {e}, falling back to direct distance")
            return self._fallback_route(origin, destination)
    
    def _osrm_route(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        vehicle_type: str = None
    ) -> RouteResult:
        """
        Calculate route using OSRM API.
        
        OSRM expects coordinates as longitude,latitude
        """
        # OSRM profile based on vehicle type
        profile = 'driving'  # Default for emergency vehicles
        
        # Format coordinates as lon,lat for OSRM
        coords = f"{origin[1]},{origin[0]};{destination[1]},{destination[0]}"
        
        url = f"{self.osrm_url}/route/v1/{profile}/{coords}"
        params = {
            'overview': 'full',
            'geometries': 'geojson',
            'steps': 'true',
            'annotations': 'true',
        }
        
        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('code') != 'Ok':
            raise ValueError(f"OSRM error: {data.get('message', 'Unknown error')}")
        
        route = data['routes'][0]
        
        # Extract turn-by-turn instructions
        instructions = []
        for leg in route.get('legs', []):
            for step in leg.get('steps', []):
                instructions.append({
                    'instruction': step.get('maneuver', {}).get('instruction', ''),
                    'distance_m': step.get('distance', 0),
                    'duration_s': step.get('duration', 0),
                    'name': step.get('name', ''),
                    'mode': step.get('mode', 'driving'),
                })
        
        return RouteResult(
            distance_m=route['distance'],
            duration_s=route['duration'],
            geometry=route['geometry'],
            instructions=instructions,
        )
    
    def _fallback_route(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float]
    ) -> RouteResult:
        """
        Fallback route calculation using direct distance.
        
        Uses Haversine formula for distance and estimates duration.
        """
        from math import radians, sin, cos, sqrt, atan2
        
        lat1, lon1 = radians(origin[0]), radians(origin[1])
        lat2, lon2 = radians(destination[0]), radians(destination[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        # Earth's radius in meters
        R = 6371000
        distance_m = R * c
        
        # Estimate duration assuming 50 km/h average speed for emergency vehicles
        # In urban areas with traffic, this is a reasonable estimate
        avg_speed_ms = 50 * 1000 / 3600  # 50 km/h in m/s
        duration_s = distance_m / avg_speed_ms
        
        # Create a simple LineString geometry
        geometry = {
            'type': 'LineString',
            'coordinates': [
                [origin[1], origin[0]],
                [destination[1], destination[0]],
            ]
        }
        
        return RouteResult(
            distance_m=distance_m,
            duration_s=duration_s,
            geometry=geometry,
            instructions=[
                {
                    'instruction': 'Head towards destination (direct route)',
                    'distance_m': distance_m,
                    'duration_s': duration_s,
                    'name': 'Direct route',
                    'mode': 'driving',
                }
            ],
        )
    
    def find_nearest_vehicles(
        self,
        incident_location: Tuple[float, float],
        vehicles: list,
        max_results: int = 5
    ) -> List[dict]:
        """
        Find nearest vehicles to an incident with route calculations.
        
        Args:
            incident_location: (latitude, longitude) of incident
            vehicles: List of Vehicle model instances
            max_results: Maximum number of results to return
            
        Returns:
            List of vehicles with route information, sorted by ETA
        """
        results = []
        
        for vehicle in vehicles:
            if not vehicle.current_location:
                continue
            
            vehicle_location = (
                vehicle.current_location.y,
                vehicle.current_location.x
            )
            
            try:
                route = self.calculate_route(vehicle_location, incident_location)
                if route:
                    results.append({
                        'vehicle_id': vehicle.id,
                        'call_sign': vehicle.call_sign,
                        'vehicle_type': vehicle.vehicle_type,
                        'status': vehicle.status,
                        'distance_m': route.distance_m,
                        'duration_s': route.duration_s,
                        'eta_minutes': route.duration_s / 60,
                        'route': route.to_dict(),
                    })
            except Exception as e:
                logger.error(f"Error calculating route for vehicle {vehicle.call_sign}: {e}")
                continue
        
        # Sort by duration (ETA)
        results.sort(key=lambda x: x['duration_s'])
        
        return results[:max_results]
    
    def optimize_assignment(
        self,
        incident_location: Tuple[float, float],
        available_vehicles: list,
        required_vehicle_types: List[str] = None
    ) -> List[dict]:
        """
        Optimize vehicle assignment for an incident.
        
        Uses a greedy algorithm to assign the best vehicle for each
        required type based on ETA.
        
        Args:
            incident_location: (latitude, longitude) of incident
            available_vehicles: List of available Vehicle instances
            required_vehicle_types: List of vehicle types needed
            
        Returns:
            List of recommended assignments with route information
        """
        if not required_vehicle_types:
            # Default: just find the single nearest vehicle
            results = self.find_nearest_vehicles(incident_location, available_vehicles, 1)
            return results
        
        assignments = []
        assigned_vehicle_ids = set()
        
        for vehicle_type in required_vehicle_types:
            # Filter vehicles by type and not already assigned
            type_vehicles = [
                v for v in available_vehicles
                if v.vehicle_type == vehicle_type and v.id not in assigned_vehicle_ids
            ]
            
            if not type_vehicles:
                logger.warning(f"No available vehicles of type {vehicle_type}")
                continue
            
            # Find nearest vehicle of this type
            results = self.find_nearest_vehicles(incident_location, type_vehicles, 1)
            
            if results:
                result = results[0]
                result['required_for'] = vehicle_type
                assignments.append(result)
                assigned_vehicle_ids.add(result['vehicle_id'])
        
        return assignments


# Singleton instance
routing_service = RoutingService()
