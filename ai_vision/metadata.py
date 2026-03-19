"""
EXIF Metadata Extraction Module
Extracts GPS coordinates and timestamp from image metadata
"""
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from datetime import datetime
from typing import Dict, Optional, Tuple
import logging

from utils.gps_utils import convert_to_degrees, validate_coordinates

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetadataExtractor:
    """
    Extracts and validates EXIF metadata from images
    """
    
    def __init__(self, max_distance_meters: int = 100):
        """
        Initialize the metadata extractor
        
        Args:
            max_distance_meters: Maximum allowed distance between image and user GPS
        """
        self.max_distance = max_distance_meters
        
    def extract_exif(self, image_path: str) -> Dict[str, any]:
        """
        Extract all EXIF data from an image
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing extracted EXIF data
        """
        try:
            image = Image.open(image_path)
            exif_data = {}
            
            if hasattr(image, '_getexif') and image._getexif() is not None:
                exif = image._getexif()
                
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    exif_data[tag] = value
                    
                logger.info(f"Successfully extracted EXIF data from {image_path}")
                return exif_data
            else:
                logger.warning(f"No EXIF data found in {image_path}")
                return {}
                
        except Exception as e:
            logger.error(f"Error extracting EXIF data: {str(e)}")
            return {}
    
    def get_gps_coordinates(self, image_path: str) -> Optional[Tuple[float, float]]:
        """
        Extract GPS coordinates from image EXIF data
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Tuple of (latitude, longitude) or None if not found
        """
        try:
            exif_data = self.extract_exif(image_path)
            
            if not exif_data or 'GPSInfo' not in exif_data:
                logger.info("No GPS info found in image")
                return None
            
            gps_info = {}
            for key in exif_data['GPSInfo'].keys():
                decode = GPSTAGS.get(key, key)
                gps_info[decode] = exif_data['GPSInfo'][key]
            
            # Extract latitude
            if 'GPSLatitude' in gps_info and 'GPSLatitudeRef' in gps_info:
                lat = convert_to_degrees(gps_info['GPSLatitude'])
                if gps_info['GPSLatitudeRef'] == 'S':
                    lat = -lat
            else:
                return None
            
            # Extract longitude
            if 'GPSLongitude' in gps_info and 'GPSLongitudeRef' in gps_info:
                lon = convert_to_degrees(gps_info['GPSLongitude'])
                if gps_info['GPSLongitudeRef'] == 'W':
                    lon = -lon
            else:
                return None
            
            # Validate coordinates
            if validate_coordinates(lat, lon):
                logger.info(f"Extracted GPS coordinates: ({lat:.4f}, {lon:.4f})")
                return (lat, lon)
            else:
                logger.warning(f"Invalid GPS coordinates extracted: ({lat}, {lon})")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting GPS coordinates: {str(e)}")
            return None
    
    def get_timestamp(self, image_path: str) -> Optional[datetime]:
        """
        Extract original timestamp from image EXIF data
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Datetime object or None if not found
        """
        try:
            exif_data = self.extract_exif(image_path)
            
            # Try multiple timestamp fields
            timestamp_fields = ['DateTimeOriginal', 'DateTimeDigitized', 'DateTime']
            
            for field in timestamp_fields:
                if field in exif_data:
                    timestamp_str = exif_data[field]
                    try:
                        # Parse EXIF timestamp format: "YYYY:MM:DD HH:MM:SS"
                        timestamp = datetime.strptime(timestamp_str, '%Y:%m:%d %H:%M:%S')
                        logger.info(f"Extracted timestamp: {timestamp}")
                        return timestamp
                    except ValueError:
                        continue
            
            logger.info("No timestamp found in image")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting timestamp: {str(e)}")
            return None
    
    def verify_image_authenticity(self, image_path: str, user_lat: float, 
                                  user_lon: float) -> Dict[str, any]:
        """
        Verify image authenticity by checking GPS and metadata
        
        Args:
            image_path: Path to the image file
            user_lat: User's reported latitude
            user_lon: User's reported longitude
            
        Returns:
            Dictionary with verification results
        """
        from utils.gps_utils import calculate_distance, format_coordinates
        
        result = {
            'authentic': False,
            'has_exif': False,
            'has_gps': False,
            'gps_match': False,
            'distance_meters': None,
            'image_location': None,
            'timestamp': None,
            'message': ''
        }
        
        # Check if image has EXIF data
        exif_data = self.extract_exif(image_path)
        if not exif_data:
            result['message'] = 'No EXIF data found. Image may be downloaded or edited.'
            return result
        
        result['has_exif'] = True
        
        # Get GPS coordinates
        image_gps = self.get_gps_coordinates(image_path)
        if not image_gps:
            result['message'] = 'No GPS data in image. Please enable GPS when taking photos.'
            return result
        
        result['has_gps'] = True
        result['image_location'] = format_coordinates(image_gps[0], image_gps[1])
        
        # Get timestamp
        timestamp = self.get_timestamp(image_path)
        if timestamp:
            result['timestamp'] = timestamp.isoformat()
        
        # Calculate distance between image and user GPS
        distance = calculate_distance(user_lat, user_lon, image_gps[0], image_gps[1])
        result['distance_meters'] = round(distance, 2)
        
        # Check if within acceptable range
        if distance <= self.max_distance:
            result['gps_match'] = True
            result['authentic'] = True
            result['message'] = f'Image verified. Location within {self.max_distance}m of reported position.'
        else:
            result['message'] = f'GPS mismatch: Image taken {distance:.0f}m from reported location.'
        
        return result


# Standalone function for quick verification
def verify_image_metadata(image_path: str, user_lat: float, user_lon: float) -> Dict[str, any]:
    """
    Quick verification function for image metadata
    
    Args:
        image_path: Path to the image file
        user_lat: User's reported latitude
        user_lon: User's reported longitude
        
    Returns:
        Dictionary with verification results
    """
    extractor = MetadataExtractor()
    return extractor.verify_image_authenticity(image_path, user_lat, user_lon)