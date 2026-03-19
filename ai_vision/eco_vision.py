"""
eco_vision.py - Unified image analysis for Eco Action App
Combines metadata, quality, classification, and adds image hash.
"""
import hashlib
import logging
from typing import Optional, Dict, Any

# Import your existing modules (adjust paths if needed)
from metadata import MetadataExtractor
from utils.image_quality import ImageQualityChecker
from classifier import PlantNetClassifier
from utils.gps_utils import format_coordinates

logger = logging.getLogger(__name__)

def compute_image_hash(image_path: str, algorithm: str = 'md5') -> str:
    """
    Compute hash of image file contents (useful for duplicate detection).
    Args:
        image_path: Path to image file.
        algorithm: Hash algorithm ('md5', 'sha256', etc.)
    Returns:
        Hexadecimal hash string.
    """
    hash_func = hashlib.new(algorithm)
    with open(image_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)
    return hash_func.hexdigest()


class EcoVision:
    """
    Orchestrates all image checks:
    - Metadata (EXIF, GPS, authenticity)
    - Image quality (blur, brightness, contrast)
    - Object classification (plant / waste / etc.)
    - Image hash (for duplicate detection)
    """

    def __init__(self,
                 plantnet_api_key: Optional[str] = None,
                 confidence_threshold: float = 0.5,
                 max_distance_meters: int = 100):
        """
        Args:
            plantnet_api_key: PlantNet API key (optional, falls back to mock)
            confidence_threshold: Minimum confidence for valid identification
            max_distance_meters: Max allowed distance between image GPS and user GPS
        """
        self.metadata = MetadataExtractor(max_distance_meters=max_distance_meters)
        self.quality = ImageQualityChecker()
        self.classifier = PlantNetClassifier(
            api_key=plantnet_api_key,
            confidence_threshold=confidence_threshold
        )

    def analyze(self,
                image_path: str,
                user_lat: Optional[float] = None,
                user_lon: Optional[float] = None) -> Dict[str, Any]:
        """
        Perform all checks on an image.

        Args:
            image_path: Path to the image file.
            user_lat, user_lon: Optional user's reported GPS (for authenticity check).

        Returns:
            Dictionary with keys:
                - image_hash: MD5 hash of image file (for duplicate detection)
                - metadata: result from MetadataExtractor
                - quality: result from ImageQualityChecker.comprehensive_check
                - classification: result from PlantNetClassifier.identify_plant
                - overall: summary with 'is_acceptable' and 'issues'
        """
        result = {
            'image_path': image_path,
            'image_hash': compute_image_hash(image_path),
            'metadata': None,
            'quality': None,
            'classification': None,
            'overall': {}
        }

        # 1. Metadata extraction & verification
        if user_lat is not None and user_lon is not None:
            metadata_result = self.metadata.verify_image_authenticity(
                image_path, user_lat, user_lon
            )
        else:
            # Just extract GPS and timestamp (no verification)
            gps = self.metadata.get_gps_coordinates(image_path)
            timestamp = self.metadata.get_timestamp(image_path)
            metadata_result = {
                'authentic': None,
                'has_exif': gps is not None or timestamp is not None,
                'has_gps': gps is not None,
                'gps_match': None,
                'distance_meters': None,
                'image_location': format_coordinates(gps[0], gps[1]) if gps else None,
                'timestamp': timestamp.isoformat() if timestamp else None,
                'message': 'GPS verification skipped (user location not provided)'
            }
        result['metadata'] = metadata_result

        # 2. Image quality check
        quality_result = self.quality.comprehensive_check(image_path)
        result['quality'] = quality_result

        # 3. Classification
        classification_result = self.classifier.identify_plant(image_path)
        result['classification'] = classification_result

        # 4. Overall assessment (adjust logic to your reward rules)
        overall = {
            'is_acceptable': False,
            'issues': []
        }

        # Metadata issues (only if user GPS was provided)
        if user_lat is not None and user_lon is not None:
            if not metadata_result.get('authentic', False):
                overall['issues'].append('metadata_verification_failed')

        # Quality issues
        if not quality_result.get('is_acceptable', False):
            overall['issues'].append('quality_issues')

        # Classification issues
        if classification_result.get('success'):
            if not classification_result.get('validation', {}).get('valid', False):
                overall['issues'].append('invalid_object')
        else:
            overall['issues'].append('classification_failed')

        if len(overall['issues']) == 0:
            overall['is_acceptable'] = True

        result['overall'] = overall
        return result


# Example usage (for testing)
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 2:
        print("Usage: python eco_vision.py <image_path> [user_lat user_lon]")
        sys.exit(1)

    image = sys.argv[1]
    lat = float(sys.argv[2]) if len(sys.argv) > 2 else None
    lon = float(sys.argv[3]) if len(sys.argv) > 3 else None

    # Use your PlantNet API key from environment or hardcode for testing
    api_key = "2b10KNHbotywEhTjPUjpqjgSe"  # from your classifier test
    analyzer = EcoVision(plantnet_api_key=api_key)
    res = analyzer.analyze(image, user_lat=lat, user_lon=lon)

    import json
    print(json.dumps(res, indent=2, default=str))