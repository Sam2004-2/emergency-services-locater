"""
Coverage analysis services for emergency response.

Provides PostGIS-based spatial analysis for:
- Response time coverage zones
- Gap analysis (underserved areas)
- Facility coverage statistics
"""
import logging
from typing import List, Dict, Optional, Tuple
from django.contrib.gis.db.models.functions import Distance, Area
from django.contrib.gis.geos import Point, Polygon, MultiPolygon
from django.contrib.gis.measure import D
from django.db.models import Count, Avg, F
from django.db import connection


logger = logging.getLogger(__name__)


class CoverageAnalyzer:
    """
    Spatial coverage analysis for emergency services.
    
    Uses PostGIS for efficient spatial calculations.
    """
    
    # Standard response time targets in minutes
    RESPONSE_TARGETS = {
        'critical': 5,   # 5 minutes for critical emergencies
        'urgent': 10,    # 10 minutes for urgent calls  
        'standard': 15,  # 15 minutes for standard calls
    }
    
    # Approximate speed for emergency vehicles (m/min)
    EMERGENCY_SPEED_M_MIN = 800  # ~48 km/h average with traffic
    
    def analyze_coverage(
        self,
        county_id: Optional[int] = None,
        facility_types: Optional[List[str]] = None,
        response_times: Optional[List[int]] = None
    ) -> Dict:
        """
        Analyze emergency service coverage.
        
        Args:
            county_id: Optional county to limit analysis
            facility_types: List of facility types to include
            response_times: Response time thresholds in minutes
            
        Returns:
            Coverage analysis results with statistics
        """
        from facilities.models import County, EmergencyFacility
        
        if response_times is None:
            response_times = [5, 10, 15]
        
        # Get facilities
        facilities = EmergencyFacility.objects.all()
        if facility_types:
            facilities = facilities.filter(type__in=facility_types)
        
        # Get county or all counties
        if county_id:
            counties = County.objects.filter(id=county_id)
        else:
            counties = County.objects.all()
        
        results = {
            'summary': {
                'total_facilities': facilities.count(),
                'total_counties': counties.count(),
                'response_times_analyzed': response_times,
            },
            'coverage_zones': [],
            'county_coverage': [],
            'gaps': [],
        }
        
        # Generate coverage zones for each response time
        for minutes in response_times:
            radius_m = minutes * self.EMERGENCY_SPEED_M_MIN
            zone_data = self._calculate_coverage_zone(
                facilities, 
                radius_m, 
                minutes,
                counties
            )
            results['coverage_zones'].append(zone_data)
        
        # Calculate per-county coverage
        for county in counties:
            county_data = self._calculate_county_coverage(
                county, 
                facilities,
                response_times
            )
            results['county_coverage'].append(county_data)
        
        # Identify coverage gaps
        results['gaps'] = self._identify_gaps(counties, facilities, response_times[0])
        
        return results
    
    def _calculate_coverage_zone(
        self,
        facilities,
        radius_m: float,
        minutes: int,
        counties
    ) -> Dict:
        """Calculate coverage zone for a given response time."""
        
        # Build union of all facility buffers using PostGIS
        with connection.cursor() as cursor:
            facility_ids = list(facilities.values_list('id', flat=True))
            
            if not facility_ids:
                return {
                    'response_time_minutes': minutes,
                    'radius_m': radius_m,
                    'covered_area_km2': 0,
                    'coverage_percentage': 0,
                    'geometry': None,
                }
            
            # Create union of buffers
            # Using ST_Transform to convert to meters for buffering, then back to WGS84
            cursor.execute("""
                WITH facility_buffers AS (
                    SELECT ST_Union(
                        ST_Transform(
                            ST_Buffer(
                                ST_Transform(geom, 32629),  -- Irish grid
                                %s
                            ),
                            4326
                        )
                    ) AS coverage_geom
                    FROM services_emergencyfacility
                    WHERE id = ANY(%s)
                )
                SELECT 
                    ST_Area(ST_Transform(coverage_geom, 32629)) / 1000000 as area_km2,
                    ST_AsGeoJSON(coverage_geom) as geojson
                FROM facility_buffers
            """, [radius_m, facility_ids])
            
            row = cursor.fetchone()
            
            if row and row[0]:
                covered_area_km2 = float(row[0])
                coverage_geojson = row[1]
            else:
                covered_area_km2 = 0
                coverage_geojson = None
            
            # Calculate total county area
            county_ids = list(counties.values_list('id', flat=True))
            cursor.execute("""
                SELECT SUM(ST_Area(ST_Transform(geom, 32629))) / 1000000
                FROM boundaries_county
                WHERE id = ANY(%s)
            """, [county_ids])
            
            total_area = cursor.fetchone()[0] or 0
            
            coverage_percentage = (covered_area_km2 / total_area * 100) if total_area > 0 else 0
        
        return {
            'response_time_minutes': minutes,
            'radius_m': radius_m,
            'covered_area_km2': round(covered_area_km2, 2),
            'total_area_km2': round(float(total_area), 2),
            'coverage_percentage': round(coverage_percentage, 1),
            'geometry': coverage_geojson,
        }
    
    def _calculate_county_coverage(
        self,
        county,
        facilities,
        response_times: List[int]
    ) -> Dict:
        """Calculate coverage statistics for a specific county."""
        
        # Count facilities in county using spatial query
        county_facilities = facilities.filter(geom__within=county.geom)
        
        result = {
            'county_id': county.id,
            'county_name': getattr(county, 'name_en', county.name) if hasattr(county, 'name') else str(county.id),
            'facility_count': county_facilities.count(),
            'facility_types': {},
            'coverage_by_response_time': {},
        }
        
        # Count by facility type
        for fac in county_facilities:
            ftype = fac.type
            result['facility_types'][ftype] = result['facility_types'].get(ftype, 0) + 1
        
        # Calculate coverage for each response time
        for minutes in response_times:
            radius_m = minutes * self.EMERGENCY_SPEED_M_MIN
            
            with connection.cursor() as cursor:
                facility_ids = list(county_facilities.values_list('id', flat=True))
                
                if not facility_ids:
                    result['coverage_by_response_time'][f'{minutes}min'] = 0
                    continue
                
                # Calculate intersection of buffers with county boundary
                cursor.execute("""
                    WITH facility_buffers AS (
                        SELECT ST_Union(
                            ST_Transform(
                                ST_Buffer(
                                    ST_Transform(geom, 32629),
                                    %s
                                ),
                                4326
                            )
                        ) AS coverage_geom
                        FROM services_emergencyfacility
                        WHERE id = ANY(%s)
                    ),
                    county_geom AS (
                        SELECT geom FROM boundaries_county WHERE id = %s
                    )
                    SELECT 
                        ST_Area(ST_Transform(ST_Intersection(f.coverage_geom, c.geom), 32629)) /
                        ST_Area(ST_Transform(c.geom, 32629)) * 100
                    FROM facility_buffers f, county_geom c
                """, [radius_m, facility_ids, county.id])
                
                row = cursor.fetchone()
                coverage = float(row[0]) if row and row[0] else 0
                result['coverage_by_response_time'][f'{minutes}min'] = round(min(coverage, 100), 1)
        
        return result
    
    def _identify_gaps(
        self,
        counties,
        facilities,
        max_response_time: int
    ) -> List[Dict]:
        """Identify areas with poor coverage (gaps)."""
        
        gaps = []
        radius_m = max_response_time * self.EMERGENCY_SPEED_M_MIN
        
        for county in counties:
            county_name = getattr(county, 'name_en', None) or getattr(county, 'name', str(county.id))
            county_facilities = facilities.filter(geom__within=county.geom)
            
            if county_facilities.count() == 0:
                # Entire county is a gap
                gaps.append({
                    'county_id': county.id,
                    'county_name': county_name,
                    'gap_type': 'no_facilities',
                    'description': f'No emergency facilities in {county_name}',
                    'severity': 'critical',
                })
                continue
            
            # Check coverage percentage
            with connection.cursor() as cursor:
                facility_ids = list(county_facilities.values_list('id', flat=True))
                
                cursor.execute("""
                    WITH facility_buffers AS (
                        SELECT ST_Union(
                            ST_Transform(
                                ST_Buffer(
                                    ST_Transform(geom, 32629),
                                    %s
                                ),
                                4326
                            )
                        ) AS coverage_geom
                        FROM services_emergencyfacility
                        WHERE id = ANY(%s)
                    ),
                    county_geom AS (
                        SELECT geom FROM boundaries_county WHERE id = %s
                    )
                    SELECT 
                        ST_Area(ST_Transform(ST_Intersection(f.coverage_geom, c.geom), 32629)) /
                        ST_Area(ST_Transform(c.geom, 32629)) * 100 as coverage_pct,
                        ST_AsGeoJSON(ST_Difference(c.geom, f.coverage_geom)) as gap_geom
                    FROM facility_buffers f, county_geom c
                """, [radius_m, facility_ids, county.id])
                
                row = cursor.fetchone()
                
                if row:
                    coverage = float(row[0]) if row[0] else 0
                    gap_geom = row[1]
                    
                    if coverage < 100:
                        severity = 'critical' if coverage < 50 else 'moderate' if coverage < 75 else 'minor'
                        gaps.append({
                            'county_id': county.id,
                            'county_name': county_name,
                            'gap_type': 'partial_coverage',
                            'description': f'{county_name} has {round(100-coverage, 1)}% uncovered area',
                            'coverage_percentage': round(coverage, 1),
                            'severity': severity,
                            'gap_geometry': gap_geom,
                        })
        
        # Sort by severity
        severity_order = {'critical': 0, 'moderate': 1, 'minor': 2}
        gaps.sort(key=lambda x: severity_order.get(x['severity'], 3))
        
        return gaps
    
    def get_vehicle_coverage(
        self,
        vehicle_type: Optional[str] = None,
        response_time: int = 10
    ) -> Dict:
        """
        Analyze current vehicle coverage based on vehicle positions.
        
        Args:
            vehicle_type: Optional vehicle type filter
            response_time: Response time threshold in minutes
            
        Returns:
            Real-time vehicle coverage analysis
        """
        from .models import Vehicle
        
        vehicles = Vehicle.objects.filter(
            status='available',
            current_location__isnull=False
        )
        
        if vehicle_type:
            vehicles = vehicles.filter(vehicle_type=vehicle_type)
        
        radius_m = response_time * self.EMERGENCY_SPEED_M_MIN
        
        vehicle_data = []
        for vehicle in vehicles:
            vehicle_data.append({
                'id': vehicle.id,
                'call_sign': vehicle.call_sign,
                'vehicle_type': vehicle.vehicle_type,
                'location': {
                    'type': 'Point',
                    'coordinates': [vehicle.current_location.x, vehicle.current_location.y]
                },
                'coverage_radius_m': radius_m,
            })
        
        return {
            'response_time_minutes': response_time,
            'vehicle_count': len(vehicle_data),
            'vehicles': vehicle_data,
        }


# Singleton instance
coverage_analyzer = CoverageAnalyzer()
