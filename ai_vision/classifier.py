# plantnet_classifier_fixed.py
import requests
import json
import os
import logging
from PIL import Image
from typing import Dict, List, Optional
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PlantNetClassifier:
    """
    Fixed PlantNet API classifier for Himalayan flora
    """
    
    # Correct PlantNet API endpoints
    API_URL = "https://my-api.plantnet.org/v2/identify/all"
    
    # Himalayan species of interest
    HIMALAYAN_SPECIES = {
        "Rhododendron arboreum": {
            "common_names": ["Buransh", "Tree Rhododendron", "Laligurans"],
            "category": "flora",
            "description": "National flower of Nepal, bright red flowers"
        },
        "Rhododendron campanulatum": {
            "common_names": ["Bell Rhododendron", "Simmali"],
            "category": "flora",
            "description": "Bell-shaped white to pink flowers"
        },
        "Cedrus deodara": {
            "common_names": ["Deodar", "Devdar", "Himalayan Cedar"],
            "category": "flora",
            "description": "Sacred tree, tall evergreen conifer"
        },
        "Quercus leucotrichophora": {
            "common_names": ["Banj Oak", "Himalayan Oak"],
            "category": "flora",
            "description": "Evergreen oak, important for wildlife"
        },
        "Pinus roxburghii": {
            "common_names": ["Chir Pine", "Himalayan Pine"],
            "category": "flora",
            "description": "Long-needled pine, resinous wood"
        },
        "Betula utilis": {
            "common_names": ["Bhojpatra", "Himalayan Birch"],
            "category": "flora",
            "description": "White bark used for ancient manuscripts"
        },
        "Saussurea obvallata": {
            "common_names": ["Brahma Kamal", "Sacred Lotus"],
            "category": "flora",
            "description": "Sacred flower of Lord Brahma"
        },
        "Meconopsis aculeata": {
            "common_names": ["Himalayan Blue Poppy"],
            "category": "flora",
            "description": "Rare blue flower, endangered"
        },
        "Primula denticulata": {
            "common_names": ["Drumstick Primula"],
            "category": "flora",
            "description": "Round clusters of purple flowers"
        },
        "Rheum australe": {
            "common_names": ["Himalayan Rhubarb", "Dolu"],
            "category": "flora",
            "description": "Medicinal plant, large leaves"
        },
        "Aconitum heterophyllum": {
            "common_names": ["Atis", "Himalayan Aconite"],
            "category": "flora",
            "description": "Medicinal plant, blue flowers"
        }
    }
    
    # Non-plant objects to reject
    NON_ECO_OBJECTS = {
        "trash": [
            "plastic", "bottle", "wrapper", "packet", "bag", 
            "can", "glass", "paper", "cup", "waste", "litter",
            "garbage", "rubbish", "trash", "dump"
        ],
        "manmade": [
            "building", "house", "road", "car", "vehicle", "phone",
            "camera", "shoe", "clothing", "bag", "backpack", "tent",
            "bench", "chair", "table", "fence", "sign", "pole", "wire"
        ],
        "animals": [
            "dog", "cat", "cow", "buffalo", "goat", "sheep", "bird",
            "person", "human", "man", "woman", "child"
        ],
        "river_elements": [
            "water", "river", "stream", "lake", "pond", "snow", "ice",
            "rock", "stone", "sand", "soil", "mud"
        ]
    }
    
    def __init__(self, api_key: str = None, confidence_threshold: float = 0.5):
        """
        Initialize PlantNet classifier
        
        Args:
            api_key: Your PlantNet API key
            confidence_threshold: Minimum confidence for valid identification
        """
        self.api_key = api_key or os.getenv('PLANTNET_API_KEY')
        if not self.api_key:
            logger.warning("No API key provided. Using mock mode.")
            self.mock_mode = True
        else:
            self.mock_mode = False
            
        self.confidence_threshold = confidence_threshold
        self.project = "all"  # all plants
        
        logger.info(f"✅ PlantNet Classifier initialized")
        logger.info(f"📚 Tracking {len(self.HIMALAYAN_SPECIES)} Himalayan species")
        logger.info(f"🎯 Confidence threshold: {confidence_threshold}")
        logger.info(f"🔧 Mode: {'MOCK' if self.mock_mode else 'LIVE'}")
    
    def identify_plant(self, image_path: str) -> Dict:
        """
        Identify plant from image
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dict with identification results
        """
        # Check if file exists
        if not os.path.exists(image_path):
            return {
                'success': False,
                'error': f"Image not found: {image_path}",
                'phase': 'file_check'
            }
        
        # Check image validity
        image_check = self._check_image_valid(image_path)
        if not image_check['valid']:
            return {
                'success': False,
                'error': image_check['message'],
                'phase': 'image_check'
            }
        
        # Use mock mode if no API key
        if self.mock_mode:
            logger.info("🔧 Using mock mode for testing")
            return self._get_mock_response(image_path)
        
        # Try live API
        return self._call_plantnet_api(image_path)
    
    def _call_plantnet_api(self, image_path: str) -> Dict:
        """Make actual API call to PlantNet"""
        
        # Try different endpoint variations
        endpoints = [
            "https://my-api.plantnet.org/v2/identify/all",
            "https://api.plantnet.org/v2/identify/all",
            "https://my-api.plantnet.org/v1/identify/all",
            "https://api.plantnet.org/v1/identify/all"
            ]
        
        for endpoint in endpoints:
            try:
                logger.info(f"📤 Trying endpoint: {endpoint}")
                
                # Prepare the image
                with open(image_path, 'rb') as f:
                    image_data = f.read()
                
                # Prepare multipart form data
                files = {
                    'images': (os.path.basename(image_path), image_data, 'image/jpeg')
                }
                
                data = {
                    'organs': 'auto'
                }
                
                params = {
                    'api-key': self.api_key
                }
                
                # Make request
                response = requests.post(
                    endpoint,
                    params=params,
                    files=files,
                    data=data,
                    timeout=30
                )
                
                logger.info(f"Response status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"✅ Success with endpoint: {endpoint}")
                    return self._parse_response(result, image_path)
                elif response.status_code == 404:
                    continue  # Try next endpoint
                else:
                    # Other error, return appropriate message
                    return self._handle_api_error(response.status_code)
                    
            except Exception as e:
                logger.error(f"Error with endpoint {endpoint}: {e}")
                continue
        
        # If all endpoints fail, fall back to mock
        logger.warning("All API endpoints failed, falling back to mock mode")
        return self._get_mock_response(image_path)
    
    def _handle_api_error(self, status_code: int) -> Dict:
        """Handle API error codes"""
        if status_code == 401:
            return {
                'success': False,
                'error': "Invalid API key. Please check your PlantNet API key.",
                'phase': 'api_auth'
            }
        elif status_code == 403:
            return {
                'success': False,
                'error': "Access forbidden. Your API key may not have permission.",
                'phase': 'api_auth'
            }
        elif status_code == 429:
            return {
                'success': False,
                'error': "Rate limit exceeded. Please wait before trying again.",
                'phase': 'rate_limit'
            }
        elif status_code == 500:
            return {
                'success': False,
                'error': "PlantNet server error. Please try again later.",
                'phase': 'server_error'
            }
        else:
            return {
                'success': False,
                'error': f"API error: {status_code}",
                'phase': 'api_error'
            }
    
    def _check_image_valid(self, image_path: str) -> Dict:
        """Check if image is valid for processing"""
        try:
            with Image.open(image_path) as img:
                # Check format
                if img.format not in ['JPEG', 'PNG', 'JPG']:
                    return {
                        'valid': False,
                        'message': "Only JPEG/PNG images are supported"
                    }
                
                # Check dimensions
                width, height = img.size
                if width < 100 or height < 100:
                    return {
                        'valid': False,
                        'message': "Image too small. Minimum 100x100 pixels"
                    }
                
                # Check file size (max 10MB)
                file_size = os.path.getsize(image_path) / (1024 * 1024)
                if file_size > 10:
                    return {
                        'valid': False,
                        'message': "Image too large. Maximum 10MB"
                    }
                
                return {'valid': True, 'message': "Image valid"}
                
        except Exception as e:
            return {
                'valid': False,
                'message': f"Invalid image: {str(e)}"
            }
    
    def _parse_response(self, api_response: Dict, image_path: str) -> Dict:
        """Parse PlantNet API response"""
        
        if not api_response or 'results' not in api_response:
            return {
                'success': False,
                'error': "No plants identified in the image",
                'phase': 'no_identification'
            }
        
        results = api_response['results']
        matches = []
        
        for idx, result in enumerate(results[:5]):
            try:
                species = result.get('species', {})
                scientific_name = species.get('scientificNameWithoutAuthor', 'Unknown')
                
                common_names = species.get('commonNames', [])
                if not common_names:
                    common_names = ['Unknown']
                
                score = result.get('score', 0)
                
                # Check if Himalayan species
                himalayan_info = self.HIMALAYAN_SPECIES.get(scientific_name, {})
                is_himalayan = bool(himalayan_info)
                
                match = {
                    'scientific_name': scientific_name,
                    'common_name': common_names[0],
                    'all_common_names': common_names,
                    'confidence': round(score, 3),
                    'is_himalayan': is_himalayan,
                    'category': himalayan_info.get('category', 'flora') if is_himalayan else 'unknown',
                    'himalayan_names': himalayan_info.get('common_names', []) if is_himalayan else [],
                    'description': himalayan_info.get('description', '') if is_himalayan else '',
                    'gbif_id': species.get('gbifId'),
                    'rank': idx + 1
                }
                
                matches.append(match)
                
            except Exception as e:
                logger.error(f"Error parsing result: {e}")
                continue
        
        if not matches:
            return {
                'success': False,
                'error': "Could not parse plant identification results",
                'phase': 'parsing_error'
            }
        
        # Get best match
        best_match = matches[0]
        
        # Validate
        validation = self._validate_eco_object(best_match)
        
        return {
            'success': True,
            'image_processed': os.path.basename(image_path),
            'best_match': best_match,
            'all_matches': matches,
            'validation': validation,
            'suggestions': self._get_suggestions(validation)
        }
    
    def _validate_eco_object(self, best_match: Dict) -> Dict:
        """Validate if the detected object is a valid eco-object"""
        
        # Check confidence
        if best_match['confidence'] < self.confidence_threshold:
            return {
                'valid': False,
                'reason': f"Low confidence ({best_match['confidence']:.2f})",
                'action': 'retake',
                'message': f"Please take a clearer photo (confidence too low: {best_match['confidence']:.2f})"
            }
        
        # Check if Himalayan species
        if best_match['is_himalayan']:
            return {
                'valid': True,
                'reason': f"Valid Himalayan species",
                'action': 'accept',
                'message': f"✓ Great! You found {best_match['common_name']} ({best_match['scientific_name']})"
            }
        
        # Check for non-plant objects
        text_to_check = f"{best_match['scientific_name'].lower()} {best_match['common_name'].lower()}"
        
        for object_type, keywords in self.NON_ECO_OBJECTS.items():
            for keyword in keywords:
                if keyword in text_to_check:
                    return {
                        'valid': False,
                        'reason': f"{object_type} detected",
                        'action': f'reject_{object_type}',
                        'message': f"This appears to be {object_type}. Please take a photo of a plant.",
                        'object_type': object_type
                    }
        
        # Check if general plant
        plant_keywords = ['plant', 'flower', 'tree', 'leaf', 'shrub', 'herb']
        if any(keyword in text_to_check for keyword in plant_keywords):
            return {
                'valid': False,
                'reason': "General plant (not Himalayan species)",
                'action': 'general_plant',
                'message': "This is a plant, but not a tracked Himalayan species. Try another!",
                'object_type': 'general_plant'
            }
        
        # Unknown
        return {
            'valid': False,
            'reason': "Unknown object",
            'action': 'reject_unknown',
            'message': "This doesn't appear to be a plant. Please take a photo of a Himalayan plant.",
            'object_type': 'unknown'
        }
    
    def _get_suggestions(self, validation: Dict) -> List[str]:
        """Get suggestions based on validation"""
        
        if validation['valid']:
            return [
                "✅ Great shot! Keep exploring!",
                "📸 Try photographing different Himalayan plants",
                "🏔️ Look for rare species at higher altitudes"
            ]
        
        object_type = validation.get('object_type', 'unknown')
        
        suggestions_map = {
            'trash': [
                "📸 Take a photo of a plant instead",
                "🌿 Look for flowers, leaves, or trees",
                "🌸 Try photographing Rhododendron (Buransh)"
            ],
            'animal': [
                "🐕 We need plants, not animals",
                "🌺 Focus on flowers or trees",
                "📷 Try a close-up of leaves or petals"
            ],
            'manmade': [
                "🏠 Please avoid buildings and objects",
                "🌳 Find a tree or plant to photograph",
                "📸 Look for natural elements only"
            ],
            'general_plant': [
                "🌱 Good plant! Try to find these Himalayan species:",
                "🌸 Rhododendron (Buransh)",
                "🌲 Deodar Cedar",
                "💮 Brahma Kamal"
            ],
            'unknown': [
                "📸 Make sure the plant is clearly visible",
                "🌿 Get closer to the flower or leaf",
                "☀️ Ensure good lighting on the plant",
                "🎯 Center the plant in the frame"
            ]
        }
        
        return suggestions_map.get(object_type, suggestions_map['unknown'])
    
    def _get_mock_response(self, image_path: str) -> Dict:
        """Return mock response for testing"""
        
        # Simulate different responses based on filename
        filename = os.path.basename(image_path).lower()
        
        # Default mock response
        if 'rhododendron' in filename or 'flower' in filename:
            mock = {
                'scientific_name': 'Rhododendron arboreum',
                'common_name': 'Tree Rhododendron',
                'confidence': 0.89,
                'is_himalayan': True,
                'category': 'flora',
                'himalayan_names': ['Buransh', 'Laligurans'],
                'description': 'National flower of Nepal'
            }
        elif 'pine' in filename or 'deodar' in filename:
            mock = {
                'scientific_name': 'Cedrus deodara',
                'common_name': 'Deodar Cedar',
                'confidence': 0.85,
                'is_himalayan': True,
                'category': 'flora',
                'himalayan_names': ['Devdar'],
                'description': 'Sacred Himalayan cedar'
            }
        elif 'plastic' in filename or 'bottle' in filename:
            mock = {
                'scientific_name': 'Plastic bottle',
                'common_name': 'Plastic waste',
                'confidence': 0.92,
                'is_himalayan': False,
                'category': 'trash'
            }
        else:
            mock = {
                'scientific_name': 'Generic Plant',
                'common_name': 'Unknown Plant',
                'confidence': 0.65,
                'is_himalayan': False,
                'category': 'unknown'
            }
        
        best_match = mock
        validation = self._validate_eco_object(best_match)
        
        return {
            'success': True,
            'image_processed': os.path.basename(image_path),
            'best_match': best_match,
            'all_matches': [best_match],
            'validation': validation,
            'suggestions': self._get_suggestions(validation),
            'mock_mode': True
        }

# For testing
if __name__ == "__main__":
    import sys
    
    # Get image path from command line or use default
    if len(sys.argv) > 1:
        test_image = sys.argv[1]
    else:
        test_image = "test_photo3.jpg"
    
    # Get API key from environment or prompt
    # api_key = os.getenv('PLANTNET_API_KEY')
    # if not api_key:
    #     print("\n🔑 No API key found in environment.")
    #     api_key = input("Enter your PlantNet API key (or press Enter for mock mode): ").strip()
    
    # Initialize classifier
    classifier = PlantNetClassifier(api_key="2b10KNHbotywEhTjPUjpqjgSe")
    
    print(f"\n🔍 Analyzing: {test_image}")
    print("="*50)
    
    # Identify plant
    result = classifier.identify_plant(test_image)
    
    # Print result
    print(json.dumps(result, indent=2))
    
    # Print validation message
    if result['success']:
        if result['validation']['valid']:
            print(f"\n✅ {result['validation']['message']}")
        else:
            print(f"\n❌ {result['validation']['message']}")
            print("\n💡 Suggestions:")
            for s in result['suggestions']:
                print(f"   • {s}")
    else:
        print(f"\n❌ Error: {result['error']}")