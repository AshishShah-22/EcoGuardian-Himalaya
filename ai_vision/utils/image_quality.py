"""
Image Quality Check Module
Detects blurry, dark, or low-quality images
"""
import cv2
import numpy as np
from typing import Dict, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageQualityChecker:
    """
    Checks image quality before sending to AI
    """
    
    @staticmethod
    def check_blur(image_path: str, threshold: float = 100.0) -> Dict:
        """
        Check if image is blurry using Laplacian variance
        
        Args:
            image_path: Path to image file
            threshold: Blur threshold (lower = more blurry)
            
        Returns:
            Dictionary with blur check results
        """
        try:
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                return {'is_blurry': True, 'message': 'Could not read image', 'score': 0}
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Calculate Laplacian variance
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            is_blurry = laplacian_var < threshold
            
            return {
                'is_blurry': is_blurry,
                'score': round(laplacian_var, 2),
                'threshold': threshold,
                'message': f'Image is {"blurry" if is_blurry else "sharp"} (score: {laplacian_var:.2f})'
            }
            
        except Exception as e:
            logger.error(f"Error checking blur: {str(e)}")
            return {'is_blurry': True, 'message': f'Error: {str(e)}', 'score': 0}
    
    @staticmethod
    def check_brightness(image_path: str, min_brightness: float = 50.0) -> Dict:
        """
        Check if image is too dark
        
        Args:
            image_path: Path to image file
            min_brightness: Minimum acceptable brightness (0-255)
            
        Returns:
            Dictionary with brightness check results
        """
        try:
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                return {'is_too_dark': True, 'message': 'Could not read image', 'brightness': 0}
            
            # Convert to HSV and get Value channel
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            brightness = np.mean(hsv[:, :, 2])
            
            is_too_dark = brightness < min_brightness
            
            # Determine lighting condition
            if brightness < 30:
                condition = "Very Dark"
            elif brightness < 60:
                condition = "Dark"
            elif brightness < 120:
                condition = "Normal"
            elif brightness < 200:
                condition = "Bright"
            else:
                condition = "Very Bright"
            
            return {
                'is_too_dark': is_too_dark,
                'brightness': round(brightness, 2),
                'condition': condition,
                'threshold': min_brightness,
                'message': f'Image is {condition.lower()} (brightness: {brightness:.2f})'
            }
            
        except Exception as e:
            logger.error(f"Error checking brightness: {str(e)}")
            return {'is_too_dark': True, 'message': f'Error: {str(e)}', 'brightness': 0}
    
    @staticmethod
    def check_contrast(image_path: str, min_contrast: float = 30.0) -> Dict:
        """
        Check image contrast
        
        Args:
            image_path: Path to image file
            min_contrast: Minimum acceptable contrast
            
        Returns:
            Dictionary with contrast check results
        """
        try:
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                return {'low_contrast': True, 'message': 'Could not read image', 'contrast': 0}
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Calculate contrast (standard deviation)
            contrast = np.std(gray)
            
            low_contrast = contrast < min_contrast
            
            return {
                'low_contrast': low_contrast,
                'contrast': round(contrast, 2),
                'threshold': min_contrast,
                'message': f'Image has {"low" if low_contrast else "good"} contrast (score: {contrast:.2f})'
            }
            
        except Exception as e:
            logger.error(f"Error checking contrast: {str(e)}")
            return {'low_contrast': True, 'message': f'Error: {str(e)}', 'contrast': 0}
    
    @staticmethod
    def comprehensive_check(image_path: str) -> Dict:
        """
        Run all quality checks
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary with all quality metrics
        """
        blur_result = ImageQualityChecker.check_blur(image_path)
        brightness_result = ImageQualityChecker.check_brightness(image_path)
        contrast_result = ImageQualityChecker.check_contrast(image_path)
        
        # Determine if image is acceptable
        is_acceptable = not (blur_result['is_blurry'] or 
                            brightness_result['is_too_dark'] or 
                            contrast_result['low_contrast'])
        
        issues = []
        if blur_result['is_blurry']:
            issues.append("blurry")
        if brightness_result['is_too_dark']:
            issues.append("too dark")
        if contrast_result['low_contrast']:
            issues.append("low contrast")
        
        return {
            'is_acceptable': is_acceptable,
            'issues': issues,
            'message': 'Image quality is acceptable' if is_acceptable else f'Image issues: {", ".join(issues)}',
            'blur': blur_result,
            'brightness': brightness_result,
            'contrast': contrast_result
        }
    
    @staticmethod
    def suggest_improvements(image_path: str) -> str:
        """
        Suggest improvements based on quality checks
        
        Args:
            image_path: Path to image file
            
        Returns:
            Improvement suggestions
        """
        quality = ImageQualityChecker.comprehensive_check(image_path)
        
        if quality['is_acceptable']:
            return "Image quality is good!"
        
        suggestions = []
        if quality['blur']['is_blurry']:
            suggestions.append("• Hold the camera steady or use a tripod")
            suggestions.append("• Ensure good lighting to allow faster shutter speed")
        
        if quality['brightness']['is_too_dark']:
            suggestions.append("• Take photo in better lighting conditions")
            suggestions.append("• Use flash or move to a brighter area")
        
        if quality['contrast']['low_contrast']:
            suggestions.append("• Ensure subject stands out from background")
            suggestions.append("• Avoid taking photos in fog or mist")
        
        return "Suggestions for better photo:\n" + "\n".join(suggestions)


# Quick test function
def test_quality_checker():
    """Test the image quality checker"""
    print("Testing Image Quality Checker")
    print("=" * 40)
    
    # Create a test image
    import numpy as np
    import cv2
    
    # Create a normal image
    normal_img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    cv2.imwrite("test_normal.jpg", normal_img)
    
    # Create a dark image
    dark_img = np.random.randint(0, 50, (480, 640, 3), dtype=np.uint8)
    cv2.imwrite("test_dark.jpg", dark_img)
    
    # Create a blurry image (by applying Gaussian blur)
    blurry_img = cv2.GaussianBlur(normal_img, (15, 15), 0)
    cv2.imwrite("test_blurry.jpg", blurry_img)
    
    print("\nNormal Image:")
    print(ImageQualityChecker.comprehensive_check("test_normal.jpg"))
    
    print("\nDark Image:")
    print(ImageQualityChecker.comprehensive_check("test_dark.jpg"))
    
    print("\nBlurry Image:")
    print(ImageQualityChecker.comprehensive_check("test_blurry.jpg"))
    
    print("\nSuggestions for blurry image:")
    print(ImageQualityChecker.suggest_improvements("test_blurry.jpg"))
    
    # Clean up
    import os
    os.remove("test_normal.jpg")
    os.remove("test_dark.jpg")
    os.remove("test_blurry.jpg")


if __name__ == "__main__":
    test_quality_checker()