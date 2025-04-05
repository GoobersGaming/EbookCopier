import cv2
import numpy as np
from PIL import Image
from utils import logs
from skimage.metrics import structural_similarity as ssim

"""Functions For Comparing And Manipulating Images"""
"""TODO:Compare Images, Should Be Is It An Exact Copy And Not A %ALIKE.
convert_to_pil needed?"""

def pil_to_cv2(image):
    if isinstance(image, Image.Image):
        img_np = np.array(image)
        img_cv2 = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        logs.LOGGER.debug("pil_to_cv2, Image converted from PIL to CV2")
        return img_cv2
    elif isinstance(image, np.ndarray):
        logs.LOGGER.debug("pil_to_cv2, Image Already CV2")
        return image
    else:
        logs.LOGGER.error("pil_to_cv2, Expected CV2 or PIL format.")
        raise TypeError("Only CV2 or PIL image formats accepted")

def is_blank(image, edge_threshold=0.01):
    # Edge Density (More Robust)
    #edge_threshold: Ratio of edge pixels (e.g., 0.01 = 1% edges).
    if image is None:
        logs.LOGGER.error("is_blank, Image is None")
        return True
    image_cv2 = pil_to_cv2(image)
    gray = cv2.cvtColor(image_cv2, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    edge_pixels = np.sum(edges > 0)
    total_pixels = edges.shape[0] * edges.shape[1]
    
    edge_ratio = edge_pixels / total_pixels
    logs.LOGGER.debug(f"is_blank, edge_ratio: {edge_ratio}, edge_threshold: {edge_threshold}, result: {edge_ratio < edge_threshold}")
    return edge_ratio < edge_threshold  # True if Too few edges = empty

def convert_to_pil(image):
    """Ensure the image is in a format suitable fr saving to a PDF"""
    if isinstance(image, Image.Image):  #Already PIL Image
        logs.LOGGER.debug(f"convert_to_pil, Image already in PIL format.")
        return image
    elif isinstance(image, np.ndarray): #OpenCV Image
        logs.LOGGER.debug(f"convert_to_pil, Image converted to PIL from CV2.")
        return Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    else:
        logs.LOGGER.error(f"convert_to_pill, Unsupported image format")
        raise ValueError("Unsupported image format")

# def compare_images(current_image, previous_image, threshold=0.95):
#     logs.LOGGER.info("Comparing images")
#     #convert imaeg to numpy arrays
#     current_image_np = np.array(current_image)
#     previous_image_np = np.array(previous_image)

#     #convert to grayscale
#     current_image_gray = cv2.cvtColor(current_image_np, cv2.COLOR_RGB2GRAY)
#     previous_image_gray = cv2.cvtColor(previous_image_np, cv2.COLOR_RGB2GRAY)

#     #compute ssim
#     score, _ = ssim(current_image_gray, previous_image_gray, full=True)
#     logs.LOGGER.info(f"Image Duplicate: {score >=threshold}")
#     logs.LOGGER.debug(f"compare_images score: {score}, threshold: {threshold}, result {score >= threshold}")
#     return score >= threshold #Returns True if similarity is above threshold

def compare_images(current_image, previous_image):
    logs.LOGGER.info("Comparing images")
    current_np = np.array(current_image)
    previous_np = np.array(previous_image)
    result = np.array_equal(current_np, previous_np)
    logs.LOGGER.info(f"Compared images result: {result}")
    return result