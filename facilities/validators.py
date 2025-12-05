"""
Input validation utilities for API endpoints.

Provides consistent validation and error handling for geographic coordinates
and other numeric parameters.
"""
from rest_framework.exceptions import ValidationError


def parse_float(name: str, value, minv: float = None, maxv: float = None) -> float:
    """
    Parse a value to float with optional range validation.
    
    Args:
        name: Parameter name for error messages
        value: Value to parse
        minv: Minimum allowed value (optional)
        maxv: Maximum allowed value (optional)
        
    Returns:
        Parsed float value
        
    Raises:
        ValidationError: If value is not a valid number or out of range
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


def validate_lat_lon(lat, lon) -> tuple:
    """
    Validate latitude and longitude values.
    
    Args:
        lat: Latitude value (-90 to 90)
        lon: Longitude value (-180 to 180)
        
    Returns:
        Tuple of (latitude, longitude) as floats
        
    Raises:
        ValidationError: If coordinates are invalid
    """
    return (
        parse_float('lat', lat, -90, 90),
        parse_float('lon', lon, -180, 180),
    )


def parse_positive_meters(value, default: float = 10000, maxv: float = 200000) -> float:
    """
    Parse a positive distance value in meters.
    
    Args:
        value: Distance value to parse (None uses default)
        default: Default value if None provided
        maxv: Maximum allowed value
        
    Returns:
        Distance in meters as float
        
    Raises:
        ValidationError: If value is not a valid positive number
    """
    if value is None:
        return default
    return parse_float('radius_m', value, 1, maxv)
