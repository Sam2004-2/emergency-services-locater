from rest_framework.exceptions import ValidationError


def parse_float(name, value, minv=None, maxv=None):
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
    return (
        parse_float('lat', lat, -90, 90),
        parse_float('lon', lon, -180, 180),
    )


def parse_positive_meters(value, default=10000, maxv=200000):
    if value is None:
        return default
    return parse_float('radius_m', value, 1, maxv)
