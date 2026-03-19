"""
GPS Utilities for distance calculation and coordinate conversion
"""
from math import radians, sin, cos, sqrt, atan2
from typing import Tuple, Optional

def convert_to_degrees(value) -> float:
    """
    Convert GPS coordinates from EXIF format (degrees, minutes, seconds) to decimal degrees
        
    Returns:
        Decimal degrees as float
    """
    try:
        def rational_to_float(r):
            try:
                return float(r[0])/float(r[1]) if r[1]!=0 else 0
            except TypeError:
                return float(r)
        d = rational_to_float(value[0])
        m = rational_to_float(value[1])
        s = rational_to_float(value[2])

        return d + (m / 60.0) + (s / 3600.0)

    except Exception:
        return 0.0

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two GPS coordinates using Haversine formula
    
    Args:
        lat1, lon1: First coordinate in decimal degrees
        lat2, lon2: Second coordinate in decimal degrees
        
    Returns:
        Distance in meters
    """
    # Radius of the Earth in meters
    R = 6371000
    
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    distance = R * c
    return distance

def validate_coordinates(lat: float, lon: float) -> bool:
    """
    Validate if coordinates are within reasonable ranges
    
    Args:
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees
        
    Returns:
        True if coordinates are valid
    """
    return -90 <= lat <= 90 and -180 <= lon <= 180

def format_coordinates(lat: float, lon: float) -> str:
    """
    Format coordinates in a human-readable format
    
    Args:
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees
        
    Returns:
        Formatted string (e.g., "27.1234°N, 85.5678°E")
    """
    lat_dir = 'N' if lat >= 0 else 'S'
    lon_dir = 'E' if lon >= 0 else 'W'
    
    return f"{abs(lat):.4f}°{lat_dir}, {abs(lon):.4f}°{lon_dir}"