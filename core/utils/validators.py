"""
Shared validation utilities for spatial API endpoints.

Provides common validation functions for coordinates, distances, and other
geospatial parameters used across multiple apps.
"""
from rest_framework.exceptions import ValidationError


def parse_float(name, value, minv=None, maxv=None):
    """
    Parse and validate a float value with optional min/max constraints.
    
    Args:
        name: Field name for error messages
        value: Value to parse
        minv: Minimum allowed value (optional)
        maxv: Maximum allowed value (optional)
        
    Returns:
        Parsed float value
        
    Raises:
        ValidationError: If value cannot be parsed or is out of range
    """
    try:
        x = float(value)
    except (TypeError, ValueError):
        raise ValidationError({name: "Must be a number."})
    if minv is not None and x < minv:
        raise ValidationError({name: f"Must be ≥ {minv}."})
    if maxv is not None and x > maxv:
        raise ValidationError({name: f"Must be ≤ {maxv}."})
    return x


def validate_lat_lon(lat, lon):
    """
    Validate latitude and longitude coordinates.
    
    Args:
        lat: Latitude value (must be between -90 and 90)
        lon: Longitude value (must be between -180 and 180)
        
    Returns:
        Tuple of (lat, lon) as floats
        
    Raises:
        ValidationError: If coordinates are invalid
    """
    return (
        parse_float('lat', lat, -90, 90),
        parse_float('lon', lon, -180, 180),
    )


def parse_positive_meters(value, default=10000, maxv=200000):
    """
    Parse a distance value in meters with default and maximum constraints.
    
    Args:
        value: Distance value to parse (can be None)
        default: Default value if None (default: 10000)
        maxv: Maximum allowed value (default: 200000)
        
    Returns:
        Parsed distance in meters
        
    Raises:
        ValidationError: If value is invalid or out of range
    """
    if value is None:
        return default
    return parse_float('radius_m', value, 1, maxv)
